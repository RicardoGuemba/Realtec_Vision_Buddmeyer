# Guia de Manutenção e Integração — Realtec Vision Buddmeyer v2.0

Orientação para **adicionar TAGs**, **manutenção por falha**, **sincronização robô–supervisório** e **recomendações de arquitetura**. Mantém a estrutura da documentação existente.

> **Relacionados:** [TAG_CONTRACT.md](TAG_CONTRACT.md) | [DOCUMENTACAO_SISTEMA_COMPLETA.md](DOCUMENTACAO_SISTEMA_COMPLETA.md) | [ESTABILIDADE_E_RESILIENCIA.md](ESTABILIDADE_E_RESILIENCIA.md)

---

## Índice

1. [Como adicionar TAGs](#1-como-adicionar-tags)
2. [Manutenção por falha — mapa tipo de falha por arquivo](#2-manutenção-por-falha--mapa-tipo-de-falha-por-arquivo)
3. [Tutorial: sincronizar robô e supervisório (mm/px e handshake)](#3-tutorial-sincronizar-robô-e-supervisório-mmpx-e-handshake)
4. [Recomendações de arquitetura e pontos falhos](#4-recomendações-de-arquitetura-e-pontos-falhos)

---

# 1. Como adicionar TAGs

Para incluir uma nova TAG na comunicação PC ↔ CLP, altere **três pontos** e documente o contrato.

## 1.1 Passo 1 — Config (nome físico no CLP)

**Arquivo:** `config/settings.py`

- Na classe **`TagSettings`**, adicione um campo com **nome lógico** (ex.: `MinhaNovaTag`) e valor padrão = **nome do TAG no CLP** (ex.: `"MinhaTag_NoCLP"`).
- Use o mesmo nome lógico em todo o código; o nome físico pode ser alterado via `config/config.yaml` (seção `tags`).

**Exemplo:**

```python
# TAGs de escrita (Visão → CLP)
MinhaNovaTag: str = Field(default="MinhaTag_NoCLP")   # novo

# TAGs de leitura (CLP → Visão)
OutraTagLeitura: str = Field(default="OutraTag_NoCLP")  # novo
```

Se o CLP usar outro nome, configure em `config/config.yaml`:

```yaml
tags:
  MinhaNovaTag: "NomeRealNoCLP"
  OutraTagLeitura: "NomeRealLeitura"
```

## 1.2 Passo 2 — TagMap (whitelist e tipo)

**Arquivo:** `communication/tag_map.py`

- No dicionário **`TagMap.DEFINITIONS`**, adicione uma entrada com **`TagDefinition`**:
  - `logical_name`: mesmo nome usado em `TagSettings`.
  - `plc_name`: nome padrão no CLP (será sobrescrito pelo config se existir).
  - `tag_type`: `TagType.BOOL`, `TagType.INT`, `TagType.REAL` ou `TagType.STRING`.
  - `direction`: `TagDirection.WRITE` (Visão→CLP), `TagDirection.READ` (CLP→Visão) ou `TagDirection.BOTH`.
  - `description`: texto curto para documentação.

**Exemplo:**

```python
"MinhaNovaTag": TagDefinition(
    logical_name="MinhaNovaTag",
    plc_name="MinhaTag_NoCLP",
    tag_type=TagType.BOOL,
    direction=TagDirection.WRITE,
    description="Minha nova TAG de escrita",
    default_value=False,
),
"OutraTagLeitura": TagDefinition(
    logical_name="OutraTagLeitura",
    plc_name="OutraTag_NoCLP",
    tag_type=TagType.INT,
    direction=TagDirection.READ,
    description="TAG de leitura do CLP",
),
```

O `TagMap` usa `get_settings().tags` para mapeamentos customizados; o nome físico vem do config, a whitelist e o tipo vêm de `DEFINITIONS`.

## 1.3 Passo 3 — Uso no código

- **Escrever (Visão → CLP):** `await cip_client.write_tag("MinhaNovaTag", valor)`.
- **Ler (CLP → Visão):** `valor = await cip_client.read_tag("OutraTagLeitura")`.

Se a TAG fizer parte do handshake ou do ciclo robô, altere também:

- **Escrita em lote:** `communication/cip_client.py` (ex.: `write_detection_result` para TAGs de detecção).
- **Leitura no ciclo:** `control/robot_controller.py` (ex.: `read_tag("RobotAck")`, `read_tag("PlcCycleStart")`).

Use sempre o **nome lógico** (ex.: `"MinhaNovaTag"`), nunca o nome físico do CLP no código.

## 1.4 Passo 4 — Documentar o contrato

**Arquivo:** `docs/TAG_CONTRACT.md`

- Inclua a nova TAG na tabela **Tags de escrita (PC → CLP)** ou **Tags de leitura (CLP → PC)**.
- Informe: nome lógico, nome no CLP (padrão), tipo, direção e semântica.

Isso mantém o contrato alinhado ao código e ao CLP.

---

# 2. Manutenção por falha — mapa tipo de falha por arquivo

Use este mapa para direcionar a investigação conforme o **tipo de falha** observado.

| Tipo de falha | Sintoma / onde aparece | Arquivo(s) prioritários | O que verificar |
|---------------|------------------------|--------------------------|------------------|
| **Conexão CLP** | Não conecta, “CLP em modo simulado”, timeout | `communication/cip_client.py`, `config/config.yaml` | IP, porta, timeout; `connect()`, `_connect_sync`; firewall/rede |
| **Leitura/escrita de TAG** | Erro ao ler ou escrever TAG, TAG inválido | `communication/tag_map.py`, `communication/cip_client.py`, `config/settings.py` (TagSettings) | Nome lógico em `DEFINITIONS` e em `TagSettings`; whitelist; nome no CLP em config |
| **Coordenadas erradas / mm/px** | Valores em mm incorretos ou instáveis | `preprocessing/transforms.py` (`pixel_to_mm`), `config/config.yaml` (preprocess.mm_per_pixel), `ui/pages/operation_page.py` (spinbox mm/px) | Valor de mm_per_pixel; uso de `get_settings().preprocess.mm_per_pixel`; ver [AVALIACAO_INSTABILIDADE_MM_PX.md](AVALIACAO_INSTABILIDADE_MM_PX.md) |
| **Ciclo robô trava / estado incoerente** | Não avança de estado, timeout ACK/pick/place | `control/robot_controller.py` | `VALID_TRANSITIONS`, `_transition_to`, `_handle_*`; timeouts em config (`robot_control`); logs de estado |
| **Detecção não envia ao CLP** | Objeto detectado mas CLP não recebe | `ui/pages/operation_page.py` (`_communicate_centroid_to_plc`, `_send_detection_to_plc`), `control/robot_controller.py`, `communication/cip_client.py` | Estado do CIP (conectado/degraded); RobotReady; intervalo de comunicação (frames); `write_detection_result` |
| **Stream de vídeo** | Câmera não abre, frame preto, stream para | `streaming/source_adapters.py`, `streaming/stream_manager.py`, `streaming/stream_health.py` | Adapter USB/GigE; IP/porta GigE; `open()`, `read()`; health e reconexão |
| **Inferência / modelo** | Erro ao carregar modelo, detecção não sai | `detection/model_loader.py`, `detection/inference_engine.py`, `detection/postprocess.py` | Caminho do modelo; device (CPU/GPU); threshold e NMS em config e postprocess |
| **Interface trava ou não reflete estado** | UI desatualizada, botões incorretos | `ui/pages/operation_page.py`, `ui/main_window.py`, `ui/widgets/status_panel.py` | Sinais `state_changed`, `stream_stopped`; `_update_ui_state`; thread/async (uso de `safe_create_task`) |
| **Encerramento da aplicação** | Crash ao fechar, “Event loop is closed” | `core/async_utils.py`, chamadas a `asyncio.create_task` em `ui`, `control`, `communication` | Uso de `safe_create_task` em vez de `create_task`; ver [ESTABILIDADE_E_RESILIENCIA.md](ESTABILIDADE_E_RESILIENCIA.md) |
| **Configuração não persiste** | Alterações não salvam ou não carregam | `config/settings.py`, `ui/pages/configuration_page.py` (`_save_settings`, `_load_settings`), `config/config.yaml` | `to_yaml`/`from_yaml`; caminho do arquivo; permissões de escrita |
| **Auto-início Windows** | Não inicia com o Windows | `core/windows_startup.py`, `ui/pages/configuration_page.py` (aba Sistema) | `set_auto_start`; pasta Inicialização; caminho do `.bat` e do `main.py` |

**Fluxo sugerido:** identificar o sintoma → localizar a linha na tabela → abrir o(s) arquivo(s) indicados e checar logs (structlog) e mensagens da UI/console.

---

# 3. Tutorial: sincronizar robô e supervisório (mm/px e handshake)

Objetivo: deixar **coordenadas**, **unidades** e **handshake** alinhados entre supervisório e CLP/robô, usando os recursos disponíveis (mm/px, TAGs, modo manual/contínuo).

## 3.1 Calibração mm/px (coordenadas em mm)

1. **Definir a relação mm/pixel**  
   - Medir no cenário real: quantos mm correspondem a 1 pixel (ex.: 0,25 mm/px).  
   - No supervisório: **Configuração → Pré-processamento → Calibração mm/px** e/ou **Operação → mm/px** (efeito imediato).  
   - Valor **1** = coordenadas em **pixels**; qualquer outro valor = coordenadas em **mm** enviadas ao CLP e exibidas na UI.

2. **Onde é usado**  
   - `preprocessing/transforms.py`: `pixel_to_mm()`.  
   - `config/config.yaml`: `preprocess.mm_per_pixel`.  
   - Envio ao CLP: `CENTROID_X`, `CENTROID_Y` em **mm** (quando mm/px ≠ 1).  
   - Garantir que o **CLP/robô** espere as mesmas unidades (mm) e origem (canto da imagem ou referência da célula).

3. **Verificação rápida**  
   - Colocar objeto em posição conhecida; conferir na UI (centroide em mm) e no CLP (TAGs CENTROID_X/Y); comparar com medição física.

## 3.2 Origem e eixo no CLP

- Definir no **CLP/robô** a **origem** (0,0) e a **orientação dos eixos** (X, Y) de forma consistente com a câmera (ex.: canto inferior esquerdo da imagem = origem).  
- Se a câmera tiver espelhamento ou rotação, tratar no CLP ou (se necessário) no código (ex.: inverter eixo em `pixel_to_mm` ou na escrita das TAGs).

## 3.3 Handshake e ciclo (checklist)

| Etapa | Supervisório | CLP / Robô |
|-------|--------------|-------------|
| 1. Prontidão | VisionReady = True ao iniciar; False ao parar | Aguardar VisionReady antes de habilitar ciclo |
| 2. Autorização | Lê `PlcAuthorizeDetection` (RobotCtrl_AuthorizeDetection) | Colocar True quando permitir detecção |
| 3. Detecção | Envia PRODUCT_DETECTED, CENTROID_X, CENTROID_Y, CONFIDENCE, etc. | Receber e armazenar; setar ROBOT_ACK quando aceitar |
| 4. Echo ACK | Envia VisionEchoAck = True após ler ROBOT_ACK | Iniciar movimento (pick) ao ver EchoAck |
| 5. Pick/Place | Lê RobotPickComplete, RobotPlaceComplete | Setar True ao concluir cada etapa |
| 6. Fim de ciclo | Lê PlcCycleStart (ou equivalente); envia VisionReadyForNext = True | Setar sinal de ciclo completo; resetar flags para próximo ciclo |

Recursos no código:  
- **Escrita em lote:** `communication/cip_client.py` → `write_detection_result`, `set_vision_ready`, `set_vision_echo_ack`, `set_ready_for_next`.  
- **Leitura e transições:** `control/robot_controller.py` → `_handle_waiting_ack`, `_handle_ack_confirmed`, `_handle_waiting_pick`, `_handle_waiting_place`, `_handle_waiting_cycle_start`, `_handle_ready_for_next`.

## 3.4 Modo manual vs contínuo

- **Modo manual:** supervisório espera “Autorizar envio ao CLP” e “Novo Ciclo” na UI; use para comissionamento e testes.  
- **Modo contínuo:** após cada ciclo o supervisório volta a autorizar detecção automaticamente; use em produção quando o CLP/robô estiver estável.  
- Garantir que o **CLP** respeite a mesma sequência (autorização → dados → ACK → pick → place → ciclo completo) para evitar corrida de estados.

## 3.5 Checklist de sincronização

- [ ] mm/px calibrado e mesmo valor em Config e Operação; CLP/robô configurados para receber em mm.  
- [ ] Origem e eixos (X, Y) alinhados entre câmera e robô.  
- [ ] TAGs do handshake criadas no CLP com os mesmos nomes (ou mapeados em `config/config.yaml`).  
- [ ] VisionReady True ao iniciar e False ao parar; CLP não inicia ciclo sem VisionReady.  
- [ ] Sequência ACK → EchoAck → Pick → Place → Cycle complete testada em modo manual.  
- [ ] Timeouts (ACK, pick, place) em `config/config.yaml` → `robot_control` compatíveis com os tempos reais do robô.

---

# 4. Recomendações de arquitetura e pontos falhos

## 4.1 Pontos fortes atuais

- **Separação de camadas:** streaming → detecção → controle → comunicação; UI apenas orquestra e exibe.  
- **Uma fonte de verdade para mm/px:** settings em memória + spinbox na Operação; efeito imediato.  
- **Validação de transições:** `RobotController` com `VALID_TRANSITIONS` e `_transition_to`.  
- **Recuperação limitada:** número máximo de tentativas a partir de ERROR; evita loop infinito.  
- **Safe async:** `safe_create_task` para não agendar tarefas com loop fechado no encerramento.

## 4.2 Pontos falhos e melhorias recomendadas

| Ponto falho | Risco | Recomendação |
|-------------|--------|--------------|
| **PreprocessPipeline não integrado** | ROI, brilho e contraste da config não são aplicados antes da inferência | Integrar `PreprocessPipeline` no fluxo StreamManager → (pré-processo) → InferenceEngine ou documentar que ROI/brilho/contraste são “futuro”. |
| **Validação de coordenadas antes do CLP** | mm/px mal configurado pode enviar valores fora do range ou negativos | Validar min/max de CENTROID_X/Y (e opcionalmente confiança) antes de `write_detection_result`; log e/ou descartar se fora do range. |
| **Sem versionamento de config** | Alteração de schema pode quebrar instalações antigas | Introduzir `config_version` no YAML e migrações opcionais ao carregar. |
| **Backup de config** | Sobrescrita acidental do config sem cópia | Fazer backup com timestamp antes de `to_yaml` (ex.: `config.yaml.bak.<timestamp>`). |
| **Parada de emergência na UI** | Operador pode não ter fluxo claro para recuperar após emergência | Ter tela ou botão “Emergência liberada” e fluxo explícito (ex.: voltar a WAITING_AUTHORIZATION após confirmação). |
| **Log de auditoria** | Rastreabilidade de decisões críticas limitada | Registrar em log estruturado: envio de coordenadas ao CLP, autorização de envio (modo manual), transições de estado do robô. |
| **Testes do RobotController** | Mudanças na máquina de estados podem regredir comportamento | Testes automatizados que simulam leituras do CLP e verificam transições esperadas. |
| **Health check agregado** | Monitoramento externo limitado | Endpoint (ex.: no MJPEG ou dedicado) que agrega: stream ativo, inferência ativa, CLP conectado. |

## 4.3 Melhorias de arquitetura (médio/longo prazo)

- **Configuração:** manter `get_settings()` como singleton; não usar `reload=True` no fluxo de salvar da UI para evitar referências “stale” (já evitado hoje).  
- **Comunicação:** manter CIP em camada dedicada; novas TAGs apenas via TagSettings + TagMap + TAG_CONTRACT.  
- **Controle:** manter máquina de estados no `RobotController`; qualquer novo estado ou transição atualizar `VALID_TRANSITIONS` e documentação.  
- **Observabilidade:** considerar export de métricas (ex.: Prometheus) e logs estruturados para análise pós-incidente.

---

## Referências rápidas

| Tópico | Documento |
|--------|-----------|
| Contrato de TAGs | [TAG_CONTRACT.md](TAG_CONTRACT.md) |
| Onde alterar X (manutenção geral) | [DOCUMENTACAO_SISTEMA_COMPLETA.md](DOCUMENTACAO_SISTEMA_COMPLETA.md) § 2.4 |
| Estabilidade e resiliência | [ESTABILIDADE_E_RESILIENCIA.md](ESTABILIDADE_E_RESILIENCIA.md) |
| Causa raiz mm/px | [AVALIACAO_INSTABILIDADE_MM_PX.md](AVALIACAO_INSTABILIDADE_MM_PX.md) |
| Backlog de melhorias | [OPORTUNIDADES_DE_MELHORIA.md](OPORTUNIDADES_DE_MELHORIA.md) |

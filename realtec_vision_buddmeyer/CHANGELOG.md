# Changelog

## [Unreleased]

_(Alterações em desenvolvimento.)_

---

## [2.1.0] – 2025-02-20

### Adicionado

- **Menu Sair (Arquivo → Sair / Ctrl+Q):** Encerra todos os processos (stream, inferência, CLP, robô, MJPEG) e fecha a aplicação. `MainWindow._request_exit()` e `_force_shutdown()` garantem parada ordenada.
- **Confinamento de centroide (ROI em mm):** Configuração → Pré-processamento: área retangular definida a partir do centro da imagem com X+, X-, Y+, Y- em mm (plano cartesiano). Centroides fora da área são projetados para o ponto mais próximo dentro da ROI (`clamp_centroid_to_confinement()`). Evita colisão da placa de ventosas com as paredes do contêiner. Config em `ConfinementROISettings`; aplicado em `OperationPage` e `RobotController`.
- **Overlay da ROI na imagem:** Checkbox **ROI** na aba Operação liga/desliga o desenho do retângulo da área de confinamento sobre o vídeo (traço amarelo fino). `VideoWidget._draw_confinement_roi()`.
- **Referência das variáveis da UI:** Nova seção em **docs/USO_E_ABAS.md** listando todas as variáveis/controles (tipo, localização, significado) das abas Operação, Configuração e Diagnósticos e da barra de status.
- **Pré-carregamento do modelo:** `OperationPage.start_model_preload()` e sinal `model_preload_finished` para carregar o modelo em background após abrir a janela (evita travamento ao clicar Iniciar).

### Removido

- **preprocessing/preprocess_pipeline.py** e **preprocessing/roi_manager.py:** Não utilizados pelo fluxo principal (apenas `transforms`: pixel_to_mm, clamp_centroid_to_confinement, ImageTransforms).
- **tests/unit/test_preprocessing_roi.py:** Testes do ROI antigo removidos com o módulo.

### Alterado

- **Branding:** Nome do produto e instaladores atualizados para **Realtec Vision Buddmeyer** (título da janela, menu Sobre, log `realtec_vision_buddmeyer.log`, instalador/diretório `RealtecVisionBuddmeyer`, scripts `Iniciar_Realtec_Vision_Buddmeyer.bat/.ps1`, etc.). Classe de exceção `BuddmeyerVisionError` mantida por compatibilidade.
- **Botão "Novo Ciclo" → "Stop":** Na aba Operação, o botão interrompe imediatamente o ciclo e comandos ao robô; detecções continuam; apenas envio ao CLP e comandos ao robô são parados. Modo manual passa a avançar automaticamente para o próximo ciclo após PLACE (autorização manual apenas para envio ao CLP).
- **preprocessing/__init__.py:** Exporta apenas `ImageTransforms`, `pixel_to_mm`, `clamp_centroid_to_confinement`.
- **Documentação:** USO_E_ABAS, DOCUMENTACAO_SISTEMA_COMPLETA, DOCUMENTACAO_PARA_CLIENTE, DOCUMENTACAO_AVALIACAO_CLIENTE_TI, instalador e PRD atualizados (ROI overlay, referência UI, Stop, Realtec Vision Buddmeyer). Link em DOCUMENTACAO_SISTEMA_COMPLETA para a referência de variáveis da UI em USO_E_ABAS.
- **Versão da aplicação:** `main.py` e CHANGELOG em 2.1.0.

---

## Histórico anterior (até 2.0)

### Adicionado

- **Estabilidade e resiliência (supervisório pick-and-place):**
  - **RobotController:** Limpeza de estado em `stop()` (detecção, etapas, flags, recovery); limite de tentativas de recuperação a partir de ERROR (3 tentativas, depois aguarda intervenção); `get_status()` com serialização segura da detecção atual.
  - **CIPClient:** Reset de `error_count`, `last_error` e `reconnect_attempts` em conexão e reconexão bem-sucedidas.
  - **core/async_utils.py:** `safe_create_task()` — agenda coroutine apenas se o event loop estiver ativo, evitando crash ao encerrar a aplicação.
  - Uso de `safe_create_task` em OperationPage, RobotController e CIPClient (conexão PLC, envio ao CLP, shutdown, polling do robô, reconnect, heartbeat).
- **docs/ESTABILIDADE_E_RESILIENCIA.md:** Documento com causas de instabilidade e práticas aplicadas para supervisório.
- **Auto-início com o Windows:** Nova aba Configuração → Sistema com opção "Iniciar automaticamente com o Windows". Quando habilitada, o sistema é adicionado à pasta Inicialização do Windows e restabelece automaticamente após reinício do PC (ex.: falta de energia). Implementação em `core/windows_startup.py` usando pasta Inicialização do usuário (sem privilégios de admin).

### Removido

- **core/application.py:** Orquestrador não utilizado; main.py usa MainWindow diretamente.
- **control/cycle_processor.py:** Lógica consolidada em RobotController; nunca importado.
- **docs/DOCUMENTACAO_COMPLETA.md:** Redundante com DOCUMENTACAO_SISTEMA_COMPLETA.md (mais completo).

### Alterado

- **docs/USO_E_ABAS.md:** Removidas referências a Arquivo de Vídeo e Stream RTSP (sistema usa apenas USB e GigE).
- **README.md:** Atualizado para fontes USB/GigE; links de documentação; estrutura do projeto.
- **docs/DOCUMENTACAO_SISTEMA_COMPLETA.md:** Referências atualizadas.

### Adicionado

- **docs/README.md:** Índice de documentos com descrição e público-alvo.
- **docs/GUIA_MANUTENCAO_E_INTEGRACAO.md:** Guia com: (1) como adicionar TAGs (config, tag_map, uso, TAG_CONTRACT); (2) mapa de manutenção por falha (tipo de falha → arquivo); (3) tutorial para sincronizar robô e supervisório (mm/px, handshake, checklist); (4) recomendações de arquitetura e pontos falhos. Índice e DOCUMENTACAO_SISTEMA_COMPLETA atualizados com links.

### Corrigido

- **Instabilidade com objeto muito perto da câmera:**
  - **Post-process (NMS):** Proteção contra divisão por zero e bboxes degeneradas; clip de boxes aos limites da imagem (objeto muito perto pode gerar boxes fora do frame).
  - **Comunicação periódica ao CLP:** Não envia coordenadas durante ciclo do robô (SENDING_DATA, WAITING_ACK, ACK_CONFIRMED, WAITING_PICK, WAITING_PLACE, WAITING_CYCLE_START) para evitar sobrescrever coordenadas em uso.
  - **Throttle:** Intervalo mínimo de 500 ms entre envios ao CLP (evita flood quando objeto está muito perto e há detecção contínua).
- **tag_map.py:** Uso de `model_dump()` em vez de `dir()` para carregar mapeamentos customizados (evita depreciação Pydantic v2.11).
- **cip_client.write_detection_result:** Validação de coordenadas (range ±10000 mm, NaN/Inf) antes de enviar ao CLP.

---

## Testes unitários e oportunidades de melhoria (anterior)

### Adicionado

- **Testes unitários (pytest):** testes em `tests/unit/` para config, core.exceptions, detection.events, detection.postprocess, preprocessing.transforms, streaming.frame_buffer, communication.connection_state, output.mjpeg_stream.
- **docs/OPORTUNIDADES_DE_MELHORIA.md:** Documento com 19 oportunidades de melhoria priorizadas (robustez, segurança industrial, observabilidade, testes, config, performance).
- **pytest** em requirements.txt para execução de testes.

---

## Calibração mm/px, higienização e refatoração (anterior)

### Adicionado

- **Calibração espacial (mm/pixel):** Campo na aba Pré-processamento para informar a relação mm/px. Quando configurado, as coordenadas (u, v) do centroide são exibidas e enviadas ao CLP em milímetros. Valor padrão 1 mantém compatibilidade.
- **Função `pixel_to_mm`** em `preprocessing/transforms.py` para conversão de coordenadas.

### Removido

- **detection_overlay.py:** Widget não utilizado (VideoWidget desenha overlay internamente).
- **preprocess_config.py:** Configurações duplicadas; uso consolidado em PreprocessSettings.
- **README_INSTALLER.md, RESUMO_INSTALADOR_COMPLETO.md:** Documentação de instalador consolidada.
- **models/README_MODELO.md:** Conteúdo mergeado em models/README.md.

### Alterado

- Documentação atualizada (DOCUMENTACAO_SISTEMA_COMPLETA, USO_E_ABAS) para refletir calibração e estrutura atual.

---

## Correções de comunicação e fluxo básico PC ↔ CLP (anterior)

### Corrigido

- **Erro `NSeries has no attribute close`:** `disconnect()` agora verifica se o método existe (`close_explicit` ou `close`) antes de chamar; se não existir, apenas descarta a referência.
- **Recursão no processamento de estado:** Adicionado flag `_processing` no `RobotController` para serializar chamadas a `_process_current_state()`, evitando concorrência e estouro de pilha.
- **VisionReady duplicado:** Removida chamada a `set_vision_ready(True)` no `_handle_initializing()` do RobotController; agora é feito apenas uma vez na `OperationPage._connect_plc_and_start_robot()`.

### Adicionado

- **Handshake básico:** Antes de enviar X/Y, verifica se CLP está conectado, não está degradado, e opcionalmente lê `RobotReady`.
- **VisionReady no ciclo completo:** Seta `VisionReady=True` ao iniciar e `VisionReady=False` ao parar (novo método `_shutdown_plc_connection()`).
- **Log aprimorado:** Log de status do CLP ao enviar centroide; log de transição inclui `duration_s`.

---

## Alinhamento ao PRD PC ↔ CLP e melhorias (anterior)

### Adicionado (PRD)

- **docs/TAG_CONTRACT.md:** Contrato de tags documentado e versionado (RF/RNF), com mapeamento PRD ↔ implementação atual.
- **robot_control no config:** Seção `robot_control` com `ack_timeout`, `pick_timeout`, `place_timeout` configuráveis (RNF-02).
- **CIP:** `io_retries` (tentativas de leitura/escrita por operação) e `auto_reconnect` (reconexão automática quando degradado).
- **Reconexão automática:** Ao ficar DEGRADED (muitos erros), agenda tentativa de reconexão após `retry_interval` (RNF-02).
- **Retry em read/write:** Leitura e escrita de tags com até `io_retries` tentativas e log `cip_read_retry`/`cip_write_retry`.
- **UI (RF-06):** Painel de status exibe "Último erro" e "Latência CIP (ms)" (latência a partir de `cip_response_time`).
- **Log de transição:** `state_transition` passa a incluir `duration_s` no estado anterior (observabilidade).

### Alterado

- **RobotController:** Timeouts (ack, pick, place) lidos do config; ao iniciar recarrega `robot_control`.
- **StatusPanel:** Novos campos último erro e latência CIP; setters `set_last_error`, `set_latency_ms`.
- **OperationPage:** Erros CIP e robô atualizam último erro no painel; timer de FPS também atualiza latência CIP.
- **config.yaml:** Incluídas seções `robot_control` e parâmetros CIP `io_retries`, `auto_reconnect`.

---

## Correção IP/CLP e roteiro cliente (anterior)

### Corrigido

- **IP do CLP não atualizava após alterar na tela:** o backend usava o IP carregado apenas na inicialização. Agora, a cada tentativa de **conexão**, a aplicação recarrega IP, porta e timeout do arquivo de configuração (e da UI após salvar). Assim, alterar o IP na Configuração, salvar e conectar passa a usar o IP novo.
- **Rastreio por log:**
  - Ao **salvar** configurações: log `config_saved` com `cip_ip`, `cip_port` e caminho do arquivo.
  - Ao **conectar** ao CLP: log `cip_connecting` com IP, porta, timeout e modo simulado usados.
  - Em **erros CIP** (conexão ou tag): log `cip_error` com IP, porta, tag (quando aplicável) e mensagem de erro.

### Adicionado

- **ROTEIRO_CLIENTE.md:** guia para o cliente com:
  - Como iniciar a aplicação.
  - Como configurar o IP do CLP (salvar e depois conectar).
  - Onde ficam os logs e o que procurar (`config_saved`, `cip_connecting`, `cip_error`).
  - O que fazer quando “diz conectado mas dá erro ao enviar tag”.
  - Como executar o teste de recarregamento de config (`test_cip_config_reload.py`).
- **Script de teste** `scripts/test_cip_config_reload.py`: verifica se, ao conectar, o sistema usa o IP atual do config (pode ser executado a partir da pasta do projeto ou de `realtec_vision_buddmeyer`).
- Referência ao **ROTEIRO_CLIENTE.md** no README principal.

### Alterações técnicas

- `communication/cip_client.py`:
  - Novo método `_reload_connection_config()` para recarregar IP/porta/timeout do config.
  - `connect()` chama `_reload_connection_config()` antes de conectar e registra `cip_connecting`.
  - `_handle_error()` passa a receber `tag_name` opcional e registra `cip_error` com IP, porta e tag.
- `ui/pages/configuration_page.py`: ao salvar configurações, registra `config_saved` com `cip_ip` e `cip_port`.

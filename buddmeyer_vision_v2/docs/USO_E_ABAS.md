# Uso do sistema e ajustes por aba

Buddmeyer Vision System v2.0 — Guia das abas Operação, Configuração e Diagnósticos.

---

## Indicador de CLP (barra de status)

Na **barra inferior** da janela principal:

- **CLP: Conectado** (verde) — Conexão CIP com o CLP real (IP configurado) estabelecida.
- **CLP: Simulado** (azul) — Modo simulado ativo (configuração `simulated: true` ou falha de conexão com o CLP real).
- **CLP: Desconectado** / **Connecting** / **Degraded** (vermelho) — Sem conexão ou em tentativa/reconexão.

O modo (real vs simulado) é definido em **Configuração → Controle (CLP)** (checkbox "Modo simulado") e pelo sucesso ou falha da conexão ao iniciar.

---

## Aba Operação

**Uso:** Operação diária: escolher fonte de vídeo, iniciar/parar, acompanhar detecções e status do CLP/robô.

### Elementos

- **Vídeo (central):** exibe o stream ao vivo e as caixas de detecção (bounding boxes e centroide). Duplo clique ou F11 para tela cheia.
- **Console de eventos (abaixo do vídeo):** mensagens em tempo real (início/parada, detecções, erros, CLP).
- **Painel lateral (direita):** status do sistema, do CLP, última detecção (classe, confiança, centroide), contadores de detecções/ciclos/erros atualizados em tempo real, latência CIP e último erro.

### Ajustes possíveis (na própria aba)

- **Fonte:** Combo com:
  - **Arquivo de Vídeo** — usa o arquivo configurado em Configuração ou o selecionado em "Selecionar...".
  - **Câmera USB** — câmera USB (índice definido em Configuração).
  - **Stream RTSP** — URL RTSP (Configuração).
  - **Câmera GigE** — IP e porta GigE (Configuração).
- **Selecionar...:** abre diálogo para escolher arquivo de vídeo (visível só quando "Arquivo de Vídeo" está selecionado). Pode trocar o vídeo mesmo com o sistema rodando (o stream será reiniciado com o novo arquivo; em caso de falha, o sistema para para manter estado consistente).
- **Iniciar (F5):** inicia stream + inferência + conexão CLP + controlador de robô. A fonte usada é a **selecionada no combo** (não apenas a do config.yaml).
- **Pausar / Retomar:** Pausa o stream e a inferência sem encerrar a sessão. Ao pausar, o botão muda para "Retomar". Útil para inspecionar o estado atual sem processar novos frames.
- **Parar (F6):** para stream, inferência, controlador e encerra conexão CLP (VisionReady = False).
- **Modo Contínuo (checkbox):** quando marcado, ciclos de pick-and-place executam automaticamente sem intervenção. Quando desmarcado (**padrão**), ao final de cada ciclo o sistema aguarda "Novo Ciclo" e, **após uma detecção**, aguarda "Autorizar envio ao CLP" antes de enviar coordenadas.
- **Autorizar envio ao CLP (botão):** em modo manual, quando um objeto é detectado (acima do threshold), este botão é exibido. Ao clicar, as coordenadas são enviadas ao CLP e o ciclo (ACK → Pick → Place) segue. Sem isso, o processo não é deflagado.
- **Novo Ciclo (botão):** autoriza manualmente o próximo ciclo de pick-and-place. Habilitado apenas em modo manual e quando o ciclo anterior foi concluído.
- **Status atual (barra):** exibe em tempo real a etapa em execução (ex.: "Aguardando PICK…", "PLACE concluído").

### Ciclo de Pick-and-Place (handshake Visão/CLP/Robô)

O sistema executa o seguinte fluxo a cada detecção:

1. **Detecção** — a câmera detecta uma embalagem via RT-DETR.
2. **Envio de coordenadas** — centroide (X, Y), confiança e contagem são escritos nas TAGs do CLP.
3. **ACK do robô** — o CLP/robô confirma recebimento (ROBOT_ACK).
4. **PICK** — o robô coleta a embalagem (RobotPickComplete).
5. **PLACE** — o robô posiciona a embalagem (RobotPlaceComplete).
6. **Ciclo completo** — o CLP sinaliza fim de ciclo (PlcCycleStart).
7. **Resumo** — o console de eventos exibe todas as etapas com timestamps.
8. **Próximo ciclo** — em modo manual, aguarda "Novo Ciclo"; em contínuo, reinicia automaticamente.

> Quando não há CLP/robô real, o sistema opera em modo simulado com delays que representam tempos de movimentação do robô virtual (ACK ~1s, Pick ~2s, Place ~2s).

### Atalhos

- **F5** — Iniciar
- **F6** — Parar
- **F11** — Tela cheia (toggle)
- **Ctrl+Q** — Sair (menu)

---

## Aba Configuração

**Uso:** Definir todos os parâmetros do sistema; as alterações só passam a valer após **Salvar Configurações** (e, para stream, ao próximo **Iniciar** na aba Operação, que usa a fonte escolhida no combo).

### Subaba: Fonte de Vídeo

- **Tipo:** Arquivo de Vídeo | Câmera USB | Stream RTSP | Câmera GigE (define o tipo padrão salvo no config).
- **Arquivo de Vídeo:** Caminho do arquivo (Procurar...) e **Loop do vídeo** (reproduz em ciclo).
- **Câmera USB:** Índice da câmera (0, 1, …). Útil quando há mais de uma câmera.
- **Stream RTSP:** URL (ex.: `rtsp://...`).
- **Câmera GigE:** IP e Porta (padrão 3956).
- **Buffer:** Tamanho máximo do buffer de frames (1–100).

### Subaba: Modelo RT-DETR

- **Modelo:** Nome do modelo (Hugging Face ou local), editável (ex.: PekingU/rtdetr_r50vd).
- **Caminho local:** Pasta onde estão os arquivos do modelo (config.json, pesos, etc.) se usar modelo local.
- **Device:** auto | cuda | cpu (dispositivo de inferência).
- **Confiança mínima:** Slider 0–100% (threshold de detecção).
- **Máx. detecções:** Número máximo de detecções por frame.
- **FPS de inferência:** Limite de FPS do processamento (ex.: 15).

### Subaba: Pré-processamento

- **Calibração mm/px:** Valor (mm/pixel) para coordenadas do centroide. 1 = pixels. Outro valor = (u,v) exibidos e enviados ao CLP em mm.
- **Brilho / Contraste:** Sliders (-100 a 100) para ajuste fino.
- **ROI:** Ativar ROI e coordenadas X, Y, Largura (W), Altura (H) da região de interesse.

### Subaba: Controle (CLP)

- **IP do CLP:** Endereço do CLP Omron (ex.: 187.99.124.229).
- **Porta CIP:** 44818 (padrão EtherNet-IP).
- **Timeout:** Timeout de conexão em segundos.
- **Modo simulado:** Se marcado, **não** tenta o CLP real; usa apenas o simulador interno. Use para testes sem CLP.
- **Testar Conexão:** Botão que executa um teste TCP contra o IP/porta configurados. Informa se o CLP está acessível na rede. Não funciona em modo simulado.
- **Reconexão automática:** Intervalo (s) e número máximo de tentativas de reconexão.
- **Heartbeat:** Intervalo (s) do sinal de heartbeat para o CLP.

### Subaba: Output

- **Stream MJPEG (Supervisório Web):** Habilita stream em tempo real para visualização em navegador. O cliente abre `http://<IP>:porta/` ou `http://<IP>:porta/viewer`, informa a URL do stream (ex.: `http://192.168.1.10:8765/stream`) e clica em Conectar. Porta padrão: 8765. FPS configura o ritmo do stream (ex.: 10).
- **Servidor RTSP:** (opcional) Habilitar servidor RTSP, porta 8554, path /stream.

### Ações na parte inferior

- **Restaurar Padrões:** Restaura todos os campos para os valores padrão do sistema (definidos no Pydantic). As alterações ficam somente em memória até que o botão "Salvar Configurações" seja pressionado.
- **Salvar Configurações:** Grava tudo no `config/config.yaml` e aplica em memória. Para stream/fonte, o efeito completo é na próxima vez que você escolher a fonte na aba Operação e clicar em Iniciar.

---

## Aba Diagnósticos

**Uso:** Monitorar saúde do sistema, métricas, logs e informações de ambiente (SO, PyTorch, CUDA, modelo).

### Subaba: Visão Geral

- **Cards:** Stream FPS, Inferência FPS, Detecções (contador), Status CLP (Conectado/Simulado/Desconectado etc.), Ciclos (robô), Erros (contador).
- **Banner de saúde:**
  - Verde — "Sistema funcionando normalmente"
  - Amarelo — "Sistema com alertas"
  - Cinza — "Sistema parado"

### Subaba: Métricas

- Gráficos em tempo (quase) real:
  - **FPS do Stream**
  - **Tempo de Inferência (ms)**
  - **Confiança de Detecção (%)**
  - **Tempo de Resposta CLP (ms)**

### Subaba: Logs

- Visualizador de logs do sistema (arquivo definido em `log_file` no config).
- Filtros por nível (INFO, WARNING, ERROR) e por componente.
- Ações típicas: **Exportar** (salvar trecho em arquivo de texto), **Limpar** (limpar visualização).

### Subaba: Sistema

- **Sistema operacional:** OS, versão do Python, arquitetura.
- **PyTorch / CUDA:** Versão do PyTorch, se CUDA está disponível, nome da GPU, versão do CUDA.
- **Modelo de detecção:** Se está carregado, nome, device (cpu/cuda).
- **Uso de recursos:** CPU (% do processo), memória RAM (MB do processo) e, se houver GPU, memória alocada/reservada via PyTorch CUDA. Atualizado a cada segundo. Requer `psutil` para CPU/memória (incluído em requirements.txt).

---

## Comportamento padrão do CLP ao iniciar

O sistema **sempre tenta conectar ao CLP real** por padrão (`simulated: false` no config). Se a conexão falhar:

1. O console exibe: _"CLP real não alcançável — operando em modo SIMULADO"_.
2. O sistema cai automaticamente para **modo simulado** com robô virtual.
3. Todas as funcionalidades continuam operando normalmente com delays simulados.

Para forçar modo simulado sem tentar o CLP real, marque **"Modo simulado"** em Configuração → Controle (CLP).

## Resumo: onde ver se está CLP real ou simulado

- **Configuração:** Aba **Configuração → Controle (CLP)**.
  - **Modo simulado desmarcado** — sistema tenta CLP real (IP/porta da mesma aba).
  - **Modo simulado marcado** — sempre simulado.
- **Em execução:** Barra de status da janela principal: **"CLP: Conectado"** = CLP real; **"CLP: Simulado"** = modo simulado (por opção ou por falha de conexão).
- **Console de eventos:** ao iniciar, exibe mensagem explícita indicando se conectou ao CLP real ou operando em modo simulado.

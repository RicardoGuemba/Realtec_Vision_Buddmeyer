# Uso do sistema e ajustes por aba

Realtec Vision Buddmeyer v2.0 — Guia das abas Operação, Configuração e Diagnósticos.

Neste documento: descrição dos elementos de cada aba e, na seção **Referência das variáveis da UI**, a lista de todas as variáveis/controles com tipo, localização e significado.

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
  - **Câmera USB** — câmera USB (índice definido em Configuração).
  - **Câmera GigE** — IP e porta GigE (Configuração).
- **Iniciar (F5):** inicia stream + inferência + conexão CLP + controlador de robô. A fonte usada é a **selecionada no combo** (não apenas a do config.yaml).
- **Parar (F6):** para stream, inferência, controlador e encerra conexão CLP (VisionReady = False). A parada é executada em segundo plano para não bloquear a interface.
- **mm/px:** calibração em tempo real (mesmo valor da Configuração; efeito imediato nas coordenadas exibidas e enviadas ao CLP).
- **ROI (checkbox):** exibe ou oculta o retângulo da área de confinamento sobre a imagem (traço fino amarelo). Útil para visualizar a região válida para centroides quando o confinamento está habilitado em Configuração → Pré-processamento.
- **Modo Contínuo (checkbox):** quando marcado, ciclos de pick-and-place executam automaticamente sem intervenção. Quando desmarcado (**padrão**), **após uma detecção** aguarda "Autorizar envio ao CLP" antes de enviar coordenadas.
- **Autorizar envio ao CLP (botão):** em modo manual, quando um objeto é detectado (acima do threshold), este botão é exibido. Ao clicar, as coordenadas são enviadas ao CLP e o ciclo (ACK → Pick → Place) segue. Sem isso, o processo não é deflagado.
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
8. **Próximo ciclo** — em modo contínuo, reinicia automaticamente; em manual, aguarda próxima detecção e autorização para envio.

> Quando não há CLP/robô real, o sistema opera em modo simulado com delays que representam tempos de movimentação do robô virtual (ACK ~1s, Pick ~2s, Place ~2s).

### Atalhos

- **F5** — Iniciar
- **F6** — Parar
- **F11** — Tela cheia (toggle)
- **Ctrl+Q** — Sair (menu)

---

## Referência das variáveis da UI

Abaixo, cada variável ou controle da interface é listado com tipo, localização e significado.

### Barra de status (janela principal)

| Variável | Tipo | Descrição |
|----------|------|-----------|
| **Sistema** | Label | Estado do sistema: "Rodando" (verde) ou "Parado" (cinza). |
| **FPS** | Label | Frames por segundo do stream de vídeo (ex.: "FPS: 15.2") ou "--" quando parado. |
| **CLP** | Label | Estado da conexão CIP: "Conectado" (verde), "Simulado" (azul), "Desconectado"/"Connecting"/"Degraded" (vermelho). |
| **Timestamp** | Label | Hora atual (HH:MM:SS), atualizada a cada 0,5 s. |

### Aba Operação — Controles e exibição

| Variável | Tipo | Descrição |
|----------|------|-----------|
| **Fonte** | QComboBox | Seleção da fonte de vídeo: "Câmera USB" ou "Câmera GigE". O índice USB e IP/porta GigE vêm da Configuração; a fonte efetiva ao clicar Iniciar é a selecionada aqui. |
| **Iniciar** | QPushButton | Inicia stream, inferência, conexão CIP e controlador de robô. Atalho: F5. Desabilitado enquanto o sistema está rodando. |
| **Parar** | QPushButton | Para stream, inferência, controlador e encerra conexão CLP (VisionReady = False). Atalho: F6. Parada em segundo plano (não bloqueia a UI). |
| **mm/px** | QDoubleSpinBox | Calibração mm por pixel (ex.: 0,25). Valor em tempo real; coordenadas exibidas e enviadas ao CLP usam este valor. Sincronizado com Configuração → Pré-processamento. |
| **ROI** | QCheckBox | Liga/desliga a exibição do retângulo da área de confinamento sobre o vídeo (traço amarelo fino). Só desenha se o confinamento estiver habilitado em Configuração. |
| **Modo Contínuo** | QCheckBox | Marcado: ciclos seguem automaticamente após cada detecção. Desmarcado (padrão): após detecção, aguarda "Autorizar envio ao CLP". |
| **Autorizar envio ao CLP** | QPushButton | Visível em modo manual quando há detecção. Ao clicar, envia coordenadas ao CLP e inicia o ciclo (ACK → Pick → Place). |
| **Status atual** | QLabel | Texto da etapa atual do controlador (ex.: "Aguardando detecção", "Aguardando PICK…", "PLACE concluído"). |
| **Vídeo (central)** | VideoWidget | Exibe stream ao vivo, overlay de detecções (caixa e centroide da melhor detecção) e, se ativo, o retângulo da ROI. Duplo clique ou F11: tela cheia. |
| **Legenda da fonte** | QLabel | Texto abaixo do vídeo indicando a fonte (ex.: "Fonte: Câmera USB (índice 0)"). |
| **Console de eventos** | Widget | Lista rolável de mensagens em tempo real (início/parada, detecções, erros, CLP). |
| **Status Sistema / Stream / Inferência / CLP / Robô** | Labels (painel) | Estado de cada componente (ex.: RUNNING, STOPPED, Conectado). |
| **Última detecção** | Texto (painel) | Classe, confiança e centroide (em mm se mm/px ≠ 1) da última detecção considerada. |
| **Contadores** | Labels (painel) | Número de detecções, ciclos concluídos e erros. |
| **Latência CIP** | Label (painel) | Tempo de resposta do CLP em ms (quando disponível). |
| **Último erro** | Label (painel) | Última mensagem de erro exibida ao usuário. |

### Aba Configuração — Variáveis por sub-aba

#### Fonte de Vídeo

| Variável | Tipo | Descrição |
|----------|------|-----------|
| **Tipo** | QComboBox | "Câmera USB" ou "Câmera GigE". Define o tipo salvo em `streaming.source_type`. |
| **Índice (USB)** | QSpinBox | Índice da câmera USB (0, 1, …). Corresponde a `streaming.usb_camera_index`. |
| **IP (GigE)** | QLineEdit | Endereço IP da câmera GigE. `streaming.gige_ip`. |
| **Porta (GigE)** | QSpinBox | Porta do stream GigE (padrão 3956). `streaming.gige_port`. |
| **Tamanho máximo (Buffer)** | QSpinBox | Tamanho máximo do buffer de frames (1–100). `streaming.max_frame_buffer_size`. |

#### Modelo RT-DETR

| Variável | Tipo | Descrição |
|----------|------|-----------|
| **Modelo** | QComboBox (editável) | Nome do modelo (Hugging Face ou local). `detection.default_model`. |
| **Caminho local** | QLineEdit | Pasta dos arquivos do modelo (config, pesos). `detection.model_path`. |
| **Device** | QComboBox | "auto", "cuda" ou "cpu". `detection.device`. |
| **Confiança mínima** | QSlider + Label | Threshold de detecção (0–100%). `detection.confidence_threshold`. |
| **Máx. detecções** | QSpinBox | Número máximo de detecções por frame. `detection.max_detections`. |
| **FPS de inferência** | QSpinBox | Limite de FPS do processamento (ex.: 10). Frames excedentes são descartados. `detection.inference_fps`. |

#### Pré-processamento

| Variável | Tipo | Descrição |
|----------|------|-----------|
| **Valor (mm/pixel)** | QDoubleSpinBox | Calibração mm por pixel. 1 = coordenadas em pixels; outro valor = coordenadas em mm. `preprocess.mm_per_pixel`. |
| **Brilho** | QSlider + Label | Ajuste de brilho (-100 a 100). `preprocess.brightness`. |
| **Contraste** | QSlider + Label | Ajuste de contraste (-100 a 100). `preprocess.contrast`. |
| **Habilitar confinamento** | QCheckBox | Ativa a ROI de confinamento de centroides. `preprocess.confinement.enabled`. |
| **X- (esquerda)** | QDoubleSpinBox | Limite em mm à esquerda do centro da imagem. `preprocess.confinement.x_negative_mm`. |
| **X+ (direita)** | QDoubleSpinBox | Limite em mm à direita do centro. `preprocess.confinement.x_positive_mm`. |
| **Y+ (acima)** | QDoubleSpinBox | Limite em mm acima do centro. `preprocess.confinement.y_positive_mm`. |
| **Y- (abaixo)** | QDoubleSpinBox | Limite em mm abaixo do centro. `preprocess.confinement.y_negative_mm`. |

#### Controle (CLP)

| Variável | Tipo | Descrição |
|----------|------|-----------|
| **IP do CLP** | QLineEdit | Endereço do CLP Omron. `cip.ip`. |
| **Porta CIP** | QSpinBox | Porta CIP (padrão 44818). `cip.port`. |
| **Timeout** | QDoubleSpinBox | Timeout de conexão em segundos. `cip.connection_timeout`. |
| **Modo simulado** | QCheckBox | Se marcado, não tenta CLP real; usa simulador. `cip.simulated`. |
| **Testar Conexão** | QPushButton | Teste TCP ao IP/porta configurados. |
| **Intervalo (Reconexão)** | QDoubleSpinBox | Intervalo entre tentativas de reconexão (s). `cip.retry_interval`. |
| **Máx. tentativas (Reconexão)** | QSpinBox | Número máximo de tentativas. `cip.max_retries`. |
| **Intervalo (Heartbeat)** | QDoubleSpinBox | Intervalo do heartbeat para o CLP (s). `cip.heartbeat_interval`. |

#### Sistema

| Variável | Tipo | Descrição |
|----------|------|-----------|
| **Iniciar automaticamente com o Windows** | QCheckBox | Adiciona atalho na pasta Inicialização do Windows. `system.auto_start`. |

#### Output

| Variável | Tipo | Descrição |
|----------|------|-----------|
| **Habilitar stream MJPEG para web** | QCheckBox | Ativa o servidor HTTP de stream. `output.stream_http_enabled`. |
| **Porta** | QSpinBox | Porta do stream MJPEG (ex.: 8765). `output.stream_http_port`. |
| **FPS** | QSpinBox | FPS do stream MJPEG. `output.stream_http_fps`. |
| **URL (acesso web)** | QLineEdit (somente leitura) | URL para abrir no navegador (ex.: http://&lt;IP&gt;:8765/stream). Botão "Copiar" ao lado. |

#### Ações (rodapé da aba Configuração)

| Variável | Tipo | Descrição |
|----------|------|-----------|
| **Restaurar Padrões** | QPushButton | Restaura todos os campos para os valores padrão (em memória); é necessário salvar para persistir. |
| **Salvar Configurações** | QPushButton | Grava o estado atual em `config/config.yaml` e aplica em memória. |

### Aba Diagnósticos — Variáveis por sub-aba

#### Visão Geral

| Variável | Tipo | Descrição |
|----------|------|-----------|
| **Stream FPS** | Card | FPS atual do stream de vídeo. |
| **Inferência FPS** | Card | FPS do processamento de inferência. |
| **Detecções** | Card | Contador de detecções. |
| **CLP** | Card | Status da conexão (Conectado, Simulado, Desconectado, etc.). |
| **Ciclos** | Card | Número de ciclos pick-and-place concluídos. |
| **Erros** | Card | Contador de erros. |
| **Banner de saúde** | Label | "Sistema funcionando normalmente" (verde), "Sistema com alertas" (amarelo) ou "Sistema parado" (cinza). |

#### Métricas

| Variável | Tipo | Descrição |
|----------|------|-----------|
| **FPS do Stream** | Gráfico | Série temporal do FPS do stream. |
| **Tempo de Inferência (ms)** | Gráfico | Série do tempo de inferência por frame. |
| **Confiança de Detecção (%)** | Gráfico | Confiança da última detecção. |
| **Tempo de Resposta CLP (ms)** | Gráfico | Latência da comunicação CIP. |

#### Logs

| Variável | Tipo | Descrição |
|----------|------|-----------|
| **Visualizador** | LogViewer | Conteúdo do arquivo de log (`log_file` no config). |
| **Filtros** | Combos/controles | Filtro por nível (INFO, WARNING, ERROR) e por componente. |
| **Exportar / Limpar** | Botões | Exportar trecho para arquivo; limpar a visualização. |

#### Sistema

| Variável | Tipo | Descrição |
|----------|------|-----------|
| **Sistema operacional** | Texto | OS e versão. |
| **Python** | Texto | Versão do interpretador. |
| **PyTorch / CUDA** | Texto | Versão PyTorch, disponibilidade CUDA, GPU, versão CUDA. |
| **Modelo de detecção** | Texto | Se está carregado, nome, device. |
| **CPU / RAM / GPU** | Textos | Uso de recursos do processo (atualizado periodicamente). |

---

## Aba Configuração

**Uso:** Definir todos os parâmetros do sistema; as alterações só passam a valer após **Salvar Configurações** (e, para stream, ao próximo **Iniciar** na aba Operação, que usa a fonte escolhida no combo).

### Subaba: Fonte de Vídeo

- **Tipo:** Câmera USB | Câmera GigE (define o tipo padrão salvo no config).
- **Câmera USB:** Índice da câmera (0, 1, …). Útil quando há mais de uma câmera.
- **Câmera GigE:** IP e Porta (padrão 3956).
- **Buffer:** Tamanho máximo do buffer de frames (1–100).

### Subaba: Modelo RT-DETR

- **Modelo:** Nome do modelo (Hugging Face ou local), editável (ex.: PekingU/rtdetr_r50vd).
- **Caminho local:** Pasta onde estão os arquivos do modelo (config.json, pesos, etc.) se usar modelo local.
- **Device:** auto | cuda | cpu (dispositivo de inferência).
- **Confiança mínima:** Slider 0–100% (threshold de detecção).
- **Máx. detecções:** Número máximo de detecções por frame.
- **FPS de inferência:** Limite de FPS do processamento (padrão: 10). Controla quantos frames por segundo são enviados à inferência; frames excedentes são descartados (sempre usa o mais recente).

### Subaba: Pré-processamento

- **Calibração mm/px:** Valor (mm/pixel) para coordenadas do centroide. 1 = pixels. Outro valor = (u,v) exibidos e enviados ao CLP em mm.
- **Brilho / Contraste:** Sliders (-100 a 100) para ajuste fino.
- **Confinamento de Centroide (ROI):** Quando habilitado, define uma área retangular centrada na imagem da câmera usando limites em mm (plano cartesiano): X- (esquerda), X+ (direita), Y+ (acima), Y- (abaixo). Centroides detectados fora desta área são projetados para o ponto mais próximo dentro da ROI. Isto evita que a placa de ventosas colida com as paredes do contêiner quando o centroide está próximo à borda. Na aba **Operação**, o checkbox **ROI** permite exibir ou ocultar o retângulo dessa área sobre o vídeo (traço amarelo fino).

### Subaba: Sistema

- **Iniciar automaticamente com o Windows:** Quando marcado, o sistema é adicionado à pasta Inicialização do Windows. Após reinício do PC (ex.: falta de energia), o aplicativo inicia automaticamente quando o usuário fizer login. Útil para restabelecer operação sem intervenção manual.

### Subaba: Controle (CLP)

- **IP do CLP:** Endereço do CLP Omron (ex.: 187.99.124.229).
- **Porta CIP:** 44818 (padrão EtherNet-IP).
- **Timeout:** Timeout de conexão em segundos.
- **Modo simulado:** Se marcado, **não** tenta o CLP real; usa apenas o simulador interno. Use para testes sem CLP.
- **Testar Conexão:** Botão que executa um teste TCP contra o IP/porta configurados. Informa se o CLP está acessível na rede. Não funciona em modo simulado.
- **Reconexão automática:** Intervalo (s) e número máximo de tentativas de reconexão.
- **Heartbeat:** Intervalo (s) do sinal de heartbeat para o CLP.

### Subaba: Output

- **Stream MJPEG (Supervisório Web):** Protocolo principal para visualização remota. **Não requer instalação extra** — apenas Python e OpenCV. Habilite a opção e use a **URL exibida** na interface (campo "URL (acesso web)") para copiar e abrir no navegador. O cliente abre a URL no navegador, ou acessa `http://<IP>:8765/` para a página viewer. Porta padrão: 8765. FPS configura o ritmo do stream (ex.: 10).

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

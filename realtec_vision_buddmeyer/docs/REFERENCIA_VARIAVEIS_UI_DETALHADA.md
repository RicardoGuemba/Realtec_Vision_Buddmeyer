# Referência Detalhada das Variáveis da UI

Realtec Vision Buddmeyer v2.1.0 — Explicação completa de cada variável, parâmetro de visão computacional e mapeamento para `config.yaml`.

---

## 1. Variáveis da Barra de Status (janela principal)

| Variável | Tipo | Chave config | Descrição detalhada |
|----------|------|--------------|---------------------|
| **Sistema** | QLabel | — | Estado do sistema: "Rodando" (verde) quando stream + inferência estão ativos; "Parado" (cinza) quando não. Atualizado via sinal `stream_started` / `stream_stopped`. |
| **FPS** | QLabel | — | **FPS do stream de vídeo** (captura da câmera). Valor calculado em tempo real pelo `StreamHealth` a partir dos frames recebidos. Ex.: "FPS: 29.8" ou "--" quando parado. Atualizado a cada 500 ms. |
| **CLP** | QLabel | `cip.simulated` | Estado da conexão CIP: "Conectado" (verde) = CLP real; "Simulado" (azul) = modo simulado; "Desconectado"/"Connecting"/"Degraded" (vermelho) = sem conexão ou em tentativa. |
| **Timestamp** | QLabel | — | Hora atual (HH:MM:SS), atualizada a cada 0,5 s. |

---

## 2. Aba Operação — Controles e exibição

| Variável | Tipo | Chave config | Descrição detalhada |
|----------|------|--------------|---------------------|
| **Fonte** | QComboBox | `streaming.source_type` | Seleção: "Câmera USB" ou "Câmera GigE". O índice USB (`usb_camera_index`) e IP/porta GigE (`gige_ip`, `gige_port`) vêm da Configuração. A fonte efetiva ao clicar Iniciar é a selecionada aqui. |
| **Iniciar** | QPushButton | — | Inicia stream, inferência, conexão CIP e controlador de robô. Atalho F5. Desabilitado enquanto o sistema está rodando. |
| **Parar** | QPushButton | — | Para stream, inferência, controlador e encerra conexão CLP. Atalho F6. Parada em segundo plano (não bloqueia a UI). |
| **mm/px** | QDoubleSpinBox | `preprocess.mm_per_pixel` | Calibração mm por pixel. 1 = coordenadas em pixels; outro valor = coordenadas em mm. **Efeito imediato** — não requer reinício. Sincronizado com Configuração → Pré-processamento. |
| **ROI** | QComboBox | `preprocess.confinement.show_roi` | Liga/Desliga a exibição do retângulo da ROI de confinamento sobre o vídeo (linhas verdes). Dimensionamento em Configuração → Pré-processamento (X±, Y± em mm). |
| **Modo Contínuo** | QCheckBox | — | Marcado (padrão): ciclos pick-and-place seguem automaticamente. Desmarcado: após detecção, aguarda "Autorizar envio ao CLP". |
| **Autorizar envio ao CLP** | QPushButton | — | Visível em modo manual quando há detecção. Ao clicar, envia coordenadas ao CLP e inicia o ciclo. |
| **Status atual** | QLabel | — | Etapa atual do controlador (ex.: "Aguardando detecção", "Enviando coordenadas ao CLP...", "Aguardando PICK…"). |
| **Vídeo (central)** | VideoWidget | — | Stream ao vivo, overlay de detecções (bbox + centroide da melhor), ROI de confinamento (se ligada), FPS no canto. Duplo clique ou F11: tela cheia. |
| **Legenda da fonte** | QLabel | — | Ex.: "Fonte: Câmera USB (índice 0)" ou "Fonte: Câmera GigE — 192.168.1.100". |
| **Console de eventos** | Widget | — | Mensagens em tempo real (início/parada, detecções, erros, CLP). |
| **Status Sistema / Stream / Inferência / CLP / Robô** | Labels | — | Estado de cada componente (RUNNING, STOPPED, Conectado, etc.). |
| **Última detecção** | Texto | — | Classe, confiança e centroide (em mm se mm/px ≠ 1) da última detecção. |
| **Contadores** | Labels | — | Detecções, ciclos concluídos, erros. |
| **Latência CIP** | Label | — | Tempo de resposta do CLP em ms (quando disponível). |
| **Último erro** | Label | — | Última mensagem de erro exibida. |

---

## 3. Aba Configuração — Variáveis por sub-aba

### 3.1 Fonte de Vídeo

| Variável | Tipo | Chave config | Descrição detalhada |
|----------|------|--------------|---------------------|
| **Tipo** | QComboBox | `streaming.source_type` | "usb" ou "gige". Define o tipo padrão. |
| **Índice (USB)** | QSpinBox | `streaming.usb_camera_index` | Índice da câmera USB (0 = primeira, 1 = segunda, …). |
| **IP (GigE)** | QLineEdit | `streaming.gige_ip` | Endereço IP da câmera GigE. |
| **Porta (GigE)** | QSpinBox | `streaming.gige_port` | Porta do stream GigE (padrão 3956). |
| **Tamanho máximo (Buffer)** | QSpinBox | `streaming.max_frame_buffer_size` | Tamanho do buffer de frames (1–100). Padrão: 30. Frames excedentes são descartados (sempre o mais recente é mantido). |

### 3.2 Modelo RT-DETR

| Variável | Tipo | Chave config | Descrição detalhada |
|----------|------|--------------|---------------------|
| **Modelo** | QComboBox | `detection.default_model` | Nome do modelo (Hugging Face, ex.: PekingU/rtdetr_r50vd, ou local). |
| **Caminho local** | QLineEdit | `detection.model_path` | Pasta dos arquivos do modelo. |
| **Device** | QComboBox | `detection.device` | "auto" (detecta CUDA), "cuda" ou "cpu". |
| **Confiança mínima** | QSlider | `detection.confidence_threshold` | Threshold 0–100%. Detecções abaixo são descartadas. |
| **Máx. detecções** | QSpinBox | `detection.max_detections` | Número máximo de detecções por frame (NMS). |
| **FPS de inferência** | QSpinBox | `detection.inference_fps` | **Limite de FPS do processamento** (1–60). Padrão: 10. Controla quantos frames/segundo são enviados ao modelo; excedentes são descartados. **Requer reinício** (próximo Iniciar) para aplicar. |

### 3.3 Pré-processamento

| Variável | Tipo | Chave config | Descrição detalhada |
|----------|------|--------------|---------------------|
| **Valor (mm/pixel)** | QDoubleSpinBox | `preprocess.mm_per_pixel` | Calibração espacial. 1 = pixels; outro valor = coordenadas em mm. |
| **Brilho** | QSlider | `preprocess.brightness` | Ajuste de brilho (-100 a 100). |
| **Contraste** | QSlider | `preprocess.contrast` | Ajuste de contraste (-100 a 100). |
| **ROI de confinamento** | QComboBox | `preprocess.confinement.show_roi` | Liga/Desliga exibição do retângulo na aba Operação. |
| **Habilitar confinamento** | QCheckBox | `preprocess.confinement.enabled` | Ativa a projeção de centroides para dentro da ROI. |
| **X- (esquerda)** | QDoubleSpinBox | `preprocess.confinement.x_negative_mm` | Limite em mm à esquerda do centro. |
| **X+ (direita)** | QDoubleSpinBox | `preprocess.confinement.x_positive_mm` | Limite em mm à direita do centro. |
| **Y+ (acima)** | QDoubleSpinBox | `preprocess.confinement.y_positive_mm` | Limite em mm acima do centro. |
| **Y- (abaixo)** | QDoubleSpinBox | `preprocess.confinement.y_negative_mm` | Limite em mm abaixo do centro. |

### 3.4 Controle (CLP)

| Variável | Tipo | Chave config | Descrição detalhada |
|----------|------|--------------|---------------------|
| **IP do CLP** | QLineEdit | `cip.ip` | Endereço do CLP Omron. |
| **Porta CIP** | QSpinBox | `cip.port` | Porta CIP (padrão 44818). |
| **Timeout** | QDoubleSpinBox | `cip.connection_timeout` | Timeout de conexão em segundos. |
| **Modo simulado** | QCheckBox | `cip.simulated` | Se marcado, não tenta CLP real. |
| **Intervalo (Reconexão)** | QDoubleSpinBox | `cip.retry_interval` | Intervalo entre tentativas (s). |
| **Máx. tentativas** | QSpinBox | `cip.max_retries` | Número máximo de tentativas. |
| **Intervalo (Heartbeat)** | QDoubleSpinBox | `cip.heartbeat_interval` | Intervalo do heartbeat (s). |

### 3.5 Output (Stream MJPEG)

| Variável | Tipo | Chave config | Descrição detalhada |
|----------|------|--------------|---------------------|
| **Habilitar stream MJPEG** | QCheckBox | `output.stream_http_enabled` | Ativa servidor HTTP de stream para supervisório web. |
| **Porta** | QSpinBox | `output.stream_http_port` | Porta do stream (padrão 8765). |
| **FPS** | QSpinBox | `output.stream_http_fps` | **FPS do stream MJPEG** (1–30). Padrão: 10. Controla o ritmo de envio de frames para clientes web. **Requer reinício** para aplicar. |

---

## 4. Dados de Visão Computacional — FPS e Streaming

### 4.1 Quantos FPS tem o streaming?

O **streaming** (captura da câmera) usa o FPS **nativo da câmera**. O sistema obtém esse valor via `cv2.CAP_PROP_FPS` (USB) ou propriedades da GigE. Se a câmera reportar 0, o padrão é **30 FPS**. O StreamWorker limita a captura a esse `target_fps` via `sleep` entre frames.

**Onde ver:** Barra de status ("FPS: X.X") e aba Diagnósticos → Visão Geral → Stream FPS.

### 4.2 Posso alterar o FPS em tempo real?

| Parâmetro | Alteração em tempo real? | Como alterar |
|-----------|--------------------------|--------------|
| **FPS do stream (câmera)** | Não | O FPS vem da câmera. Câmeras USB/GigE têm taxa fixa. Para mudar, use outra câmera ou ajuste na câmera (se suportado). |
| **FPS de inferência** | Não | Configurável em Configuração → Modelo RT-DETR → FPS de inferência. **Requer Salvar + reinício** (Parar → Iniciar). |
| **FPS do stream MJPEG (web)** | Não | Configurável em Configuração → Output → FPS. **Requer Salvar + reinício**. |
| **mm/px** | Sim | Alterável na aba Operação; efeito imediato. |
| **ROI (exibição)** | Sim | Combo ROI na Operação; efeito imediato. |
| **Confiança mínima** | Não | Configuração → Modelo; requer Salvar. O modelo já carregado usa o valor em memória até reinício. |

### 4.3 Fluxo de FPS no sistema

```
Câmera (ex.: 30 FPS nativo)
    → StreamWorker (captura até target_fps da câmera)
    → FrameBuffer (até max_frame_buffer_size frames)
    → InferenceWorker (processa até inference_fps, ex.: 10 FPS)
    → PostProcessor → Detecções
```

Se a câmera produz 30 FPS e a inferência está em 10 FPS, **2 de cada 3 frames são descartados** (sempre processa o mais recente).

### 4.4 Onde cada FPS é exibido

| Local | O que mostra |
|-------|--------------|
| Barra de status | FPS do **stream** (captura) |
| Aba Diagnósticos → Visão Geral | Stream FPS e Inferência FPS |
| Aba Diagnósticos → Métricas | Gráfico de FPS do stream ao longo do tempo |
| Widget de vídeo (canto) | FPS do stream (mesmo valor da barra) |

---

## 5. Resumo de parâmetros que exigem reinício

Para aplicar alterações, é necessário **Salvar Configurações** e **Parar → Iniciar**:

- Tipo de fonte (USB/GigE), índice, IP, porta
- FPS de inferência
- Modelo, device, confiança mínima, máx. detecções
- Habilitar/desabilitar confinamento, limites X/Y da ROI
- Stream MJPEG (habilitar, porta, FPS)
- IP/porta do CLP, modo simulado

**Não exigem reinício** (efeito imediato):

- mm/px (Operação)
- ROI: Ligado/Desligado (exibição do retângulo)
- Modo Contínuo / Manual

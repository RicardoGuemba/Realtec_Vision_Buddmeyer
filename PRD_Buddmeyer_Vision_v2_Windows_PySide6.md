# PRD – Realtec Vision Buddmeyer v2.0 (Windows + PySide6)

**Versão:** 2.0.0  
**Data:** Janeiro 2025  
**Plataforma:** Windows 10/11  
**Framework UI:** PySide6 (Qt for Python)  
**Pipeline:** Streaming → Pré-processamento → DETR/RT-DETR → Comunicação CIP → CLP Omron NX102  
**Uso:** Contexto para desenvolvimento com Cursor Code Assistant em ambiente Windows

---

## 📋 ÍNDICE

1. [Resumo Executivo](#0-resumo-executivo)
2. [Objetivos](#1-objetivos)
3. [Premissas e Dados Fixos](#2-premissas-e-dados-fixos)
4. [Usuários e Personas](#3-usuários-e-personas)
5. [Arquitetura do Sistema](#4-arquitetura-do-sistema)
6. [Requisitos Funcionais](#5-requisitos-funcionais-detalhados)
7. [Comunicação CIP/CLP](#6-comunicação-cip---especificação-técnica)
8. [Requisitos Não Funcionais](#7-requisitos-não-funcionais)
9. [Dependências](#8-dependências-e-versões)
10. [Plano de Implementação](#9-plano-de-implementação)
11. [Critérios de Aceitação](#10-critérios-de-aceitação)

---

## 0. RESUMO EXECUTIVO

Sistema desktop Windows para automação de expedição (pick-and-place) de embalagens, com:

- ✅ **Detecção em tempo real** usando modelos DETR/RT-DETR (Hugging Face)
- ✅ **Comunicação industrial** com CLP Omron NX102 via CIP/EtherNet-IP
- ✅ **Interface desktop PySide6** com 3 abas: Operação, Configuração, Diagnósticos
- ✅ **Múltiplas fontes de vídeo**: arquivos MP4, USB, RTSP, GigE
- ✅ **Sistema de logs** estruturado para rastreamento de detecções e erros
- ✅ **Modo simulado** para desenvolvimento sem CLP real

### Mudanças em Relação ao Sistema Atual

| Aspecto | Sistema Atual | Sistema v2.0 |
|---------|--------------|--------------|
| Arquitetura | Frontend (React) + Backend (FastAPI) | Aplicação Desktop Monolítica |
| UI Framework | React + TypeScript + Tailwind | PySide6 (Qt for Python) |
| Servidor Web | Uvicorn + Vite | Não necessário |
| Dependência Node.js | Sim | Não |
| Deploy | Múltiplos processos | Executável único |
| Plataforma | Mac/Windows/Linux | Windows-only |

### Tecnologias Obrigatórias

**Core:**
- Python 3.10+ (Windows)
- PySide6 6.6+ (interface desktop)
- PyTorch 2.0+ (inferência DETR/RT-DETR)
- OpenCV 4.9+ (processamento de imagem)
- aphyt 2.1.9+ (comunicação CIP com CLP Omron)
- structlog (logging estruturado)

---

## 1. OBJETIVOS

### 1.1 Objetivos de Negócio

- ✅ **Simplicidade de Deploy**: Instalação única no Windows
- ✅ **Estabilidade**: Aplicação desktop nativa, sem servidor web
- ✅ **Manutenibilidade**: Código organizado por funções
- ✅ **Performance**: Otimização para Windows, suporte a GPU NVIDIA (CUDA)

### 1.2 Objetivos Técnicos

- ✅ **Arquitetura Limpa**: Separação clara de responsabilidades (UI, lógica, comunicação)
- ✅ **Observabilidade**: Logs estruturados, métricas, health checks
- ✅ **Resiliência**: Reconexão automática, tratamento de erros robusto
- ✅ **Testabilidade**: Componentes isolados, fácil de testar

### 1.3 Não Objetivos (Fora do Escopo)

- ❌ Suporte a macOS/Linux (Windows-only)
- ❌ Interface web (apenas desktop PySide)
- ❌ Múltiplos workers/processos (single-process)
- ❌ MLOps avançado (apenas inferência local)

---

## 2. PREMISSAS E DADOS FIXOS

### 2.1 Ambiente de Execução

| Requisito | Valor |
|-----------|-------|
| Sistema Operacional | Windows 10 (build 1903+) ou Windows 11 |
| Python | 3.10 ou superior |
| GPU | NVIDIA RTX (opcional, recomendado) |
| RAM | Mínimo 8 GB (recomendado 16 GB) |
| Disco | 10 GB livres |

### 2.2 CLP e Rede

| Parâmetro | Valor |
|-----------|-------|
| CLP | Omron NX102 |
| Protocolo | CIP / EtherNet/IP |
| Porta | 44818 (padrão CIP) |
| IP | Configurável (padrão: 187.99.125.5) |

### 2.3 Visão Computacional

| Parâmetro | Valor |
|-----------|-------|
| Modelo | DETR/RT-DETR (PekingU/rtdetr_r50vd) |
| Framework | Hugging Face Transformers + PyTorch |
| Device | CPU, CUDA (NVIDIA), ou Auto |
| Classes | Embalagens (single ou multi-class) |

### 2.4 Interface Gráfica

| Parâmetro | Valor |
|-----------|-------|
| Framework | PySide6 (Qt 6.6+) |
| Estilo | Qt Style Sheets (QSS) - tema industrial |
| Layout | QMainWindow com QTabWidget |
| Threading | QThread para operações pesadas |

---

## 3. USUÁRIOS E PERSONAS

### 3.1 Operador de Produção

**Necessidades:**
- Visualizar stream de vídeo com detecções em tempo real
- Ver status de conexão com CLP
- Iniciar/parar sistema com um clique
- Alertas visuais claros para falhas

**Interface:** Aba "Operação" (principal)

### 3.2 Engenheiro de Automação

**Necessidades:**
- Configurar IP do CLP, portas, timeouts
- Ajustar ROI, thresholds de confiança
- Selecionar modelo de detecção
- Visualizar logs e métricas detalhadas

**Interface:** Abas "Configuração" e "Diagnósticos"

### 3.3 Supervisor de Produção

**Necessidades:**
- Dashboard com métricas agregadas
- Histórico de eventos e alarmes
- Export de relatórios

**Interface:** Aba "Diagnósticos"

---

## 4. ARQUITETURA DO SISTEMA

### 4.1 ESTRUTURA DE DIRETÓRIOS

```
realtec_vision_buddmeyer/
├── main.py                           # Ponto de entrada
├── config/
│   ├── __init__.py
│   ├── settings.py                   # Pydantic Settings
│   └── config.yaml                   # Configuração YAML
├── ui/                               # Interface PySide6
│   ├── __init__.py
│   ├── main_window.py                # QMainWindow principal
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── video_widget.py           # Widget de vídeo com overlay
│   │   ├── detection_overlay.py      # Overlay de detecções (bboxes)
│   │   ├── status_panel.py           # Painel de status lateral
│   │   ├── metrics_chart.py          # Gráficos de métricas
│   │   ├── event_console.py          # Console de eventos
│   │   └── log_viewer.py             # Visualizador de logs
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── operation_page.py         # Aba Operação
│   │   ├── configuration_page.py     # Aba Configuração
│   │   └── diagnostics_page.py       # Aba Diagnósticos
│   └── styles/
│       └── industrial.qss            # Tema industrial escuro
├── core/
│   ├── __init__.py
│   ├── application.py                # Classe principal singleton
│   ├── logger.py                     # Sistema de logging estruturado
│   ├── metrics.py                    # Coleta de métricas
│   └── exceptions.py                 # Exceções customizadas
├── streaming/
│   ├── __init__.py
│   ├── stream_manager.py             # Gerenciador de stream (singleton)
│   ├── source_adapters.py            # Adaptadores: vídeo, USB, RTSP, GigE
│   ├── frame_buffer.py               # Buffer de frames thread-safe
│   └── stream_health.py              # Health check do stream
├── preprocessing/
│   ├── __init__.py
│   └── transforms.py                 # Transformações (pixel_to_mm, confinamento ROI)
├── detection/
│   ├── __init__.py
│   ├── inference_engine.py           # Engine de inferência DETR/RT-DETR
│   ├── model_loader.py               # Carregador de modelos HuggingFace
│   ├── postprocess.py                # NMS, filtros, centroides
│   └── events.py                     # Eventos de detecção (dataclasses)
├── communication/
│   ├── __init__.py
│   ├── cip_client.py                 # Cliente CIP/EtherNet-IP (aphyt)
│   ├── tag_map.py                    # Mapeamento de TAGs
│   ├── connection_state.py           # Estado da conexão
│   ├── cip_logger.py                 # Logger específico CIP
│   └── exceptions.py                 # Exceções CIP
├── control/
│   ├── __init__.py
│   ├── robot_controller.py           # Máquina de estados do robô
│   └── cycle_processor.py            # Processador de ciclos
├── models/                           # Modelos de ML
│   ├── README.md
│   ├── config.json
│   └── model.safetensors
├── logs/                             # Logs do sistema
│   └── .gitkeep
├── videos/                           # Vídeos de teste
│   └── .gitkeep
├── requirements.txt
└── README.md
```

### 4.2 ARQUITETURA DE COMPONENTES

```
┌─────────────────────────────────────────────────────────┐
│              UI Layer (PySide6)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Operation    │  │ Configuration │  │ Diagnostics  │  │
│  │ Page         │  │ Page          │  │ Page         │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         └─────────────────┴─────────────────┘           │
│                    │                                    │
│         ┌──────────▼──────────┐                         │
│         │   Main Window       │                         │
│         │   (QMainWindow)     │                         │
│         └──────────┬──────────┘                         │
└────────────────────┼────────────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │   Application Core    │
         │   (Singleton)         │
         │                       │
         │  ┌─────────────────┐  │
         │  │ Stream Manager  │  │
         │  └────────┬────────┘  │
         │           │           │
         │  ┌────────▼────────┐  │
         │  │ Inference Engine│  │
         │  └────────┬────────┘  │
         │           │           │
         │  ┌────────▼────────┐  │
         │  │ CIP Client      │  │
         │  └────────┬────────┘  │
         │           │           │
         │  ┌────────▼────────┐  │
         │  │ Robot Controller│  │
         │  └─────────────────┘  │
         └───────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼────┐    ┌──────▼──────┐   ┌─────▼─────┐
│Stream  │    │  Detection  │   │   CIP    │
│Source  │    │   (RT-DETR) │   │  (aphyt) │
└────────┘    └─────────────┘   └──────────┘
```

### 4.3 FLUXO DE DADOS PRINCIPAL

```
1. Stream Source (Vídeo/USB/RTSP/GigE)
   ↓
2. Stream Manager (QThread) → Frame Buffer
   ↓
3. Preprocessing Pipeline (ROI, transforms)
   ↓
4. Inference Engine (QThread) → RT-DETR Model
   ↓
5. Post-processing (NMS, confidence filter)
   ↓
6. Detection Event → UI Update (Signal/Slot)
   ↓
7. Robot Controller → CIP Client → CLP Tags
   ↓
8. CLP Response → UI Update (Signal/Slot)
```

### 4.4 PADRÕES DE DESIGN

- **Singleton**: StreamManager, InferenceEngine, CIPClient, RobotController
- **Observer**: Eventos via Qt Signals/Slots
- **Factory**: Source adapters (vídeo, USB, RTSP, GigE)
- **State Machine**: RobotController
- **Strategy**: Preprocessing transforms

---

## 5. REQUISITOS FUNCIONAIS DETALHADOS

### 5.1 INTERFACE GRÁFICA (UI)

#### 5.1.1 Janela Principal (MainWindow)

```python
class MainWindow(QMainWindow):
    """
    Janela principal com:
    - QTabWidget com 3 abas: Operação, Configuração, Diagnósticos
    - StatusBar: Status do sistema, FPS, Conexão CLP, Timestamp
    - MenuBar: Arquivo, Configurações, Ajuda
    """
```

#### 5.1.2 Aba Operação (OperationPage)

**Componentes:**

1. **VideoWidget**: Exibe vídeo em tempo real com overlay de detecções
   - Bounding boxes com cor por confiança
   - Labels com classe e confiança
   - Centroide destacado
   - FPS no canto

2. **StatusPanel** (lateral direita):
   - Status do sistema (RUNNING/PAUSED/STOPPED)
   - Status do CLP (CONNECTED/DISCONNECTED/DEGRADED)
   - Última detecção: classe, confiança, centroide (X, Y)
   - Contador de detecções no ciclo

3. **EventConsole**: Log de eventos em tempo real

4. **Controles**: Play, Pause, Stop, Reset, Seletor de vídeo

**Funcionalidades:**
- ✅ Visualização de vídeo com detecções em tempo real
- ✅ Overlay de bounding boxes com centroides
- ✅ Painel de status lateral
- ✅ Console de eventos em tempo real
- ✅ Controles: Play/Pause, Stop, Reset
- ✅ Seletor de fonte de vídeo (dropdown)
- ✅ Fullscreen do vídeo

#### 5.1.3 Aba Configuração (ConfigurationPage)

**Sub-abas:**

1. **Fonte de Vídeo**:
   - Tipo: Arquivo de Vídeo, Câmera USB, Stream RTSP, Câmera GigE
   - Seletor de arquivo de vídeo
   - Índice da câmera USB
   - URL RTSP
   - IP e porta GigE (padrão: 3956)
   - Loop de vídeo (checkbox)

2. **Modelo RT-DETR**:
   - Caminho do modelo (local ou HuggingFace ID)
   - Device: CPU, CUDA, Auto
   - Threshold de confiança (slider 0.0-1.0)
   - Máximo de detecções (spinbox)

3. **Pré-processamento**:
   - ROI (seletor retangular na imagem)
   - Brightness/Contrast (sliders)
   - Perfil pré-configurado (dropdown)

4. **Controle (CLP)**:
   - IP do CLP (padrão: 187.99.125.5)
   - Porta CIP (padrão: 44818)
   - Timeout de conexão (segundos)
   - Modo simulado (checkbox)
   - Botão "Testar Conexão"

5. **Output**:
   - RTSP Server: habilitado/desabilitado
   - Porta RTSP (padrão: 8554)
   - Path RTSP (padrão: /stream)

#### 5.1.4 Aba Diagnósticos (DiagnosticsPage)

**Sub-abas:**

1. **Visão Geral**:
   - Cards de status: Stream, Detecção, CLP, Pré-processamento
   - Health banner (saudável/alerta)

2. **Métricas**:
   - Gráfico de FPS do stream
   - Gráfico de FPS de inferência
   - Latência de detecção (ms)
   - Taxa de detecção (%)
   - Erros de comunicação CIP
   - Tempo de resposta do CLP (ms)

3. **Logs**:
   - Visualizador de logs com filtros
   - Filtro por nível: INFO/WARNING/ERROR
   - Filtro por componente
   - Botão "Exportar Logs"
   - Botão "Limpar"

4. **Sistema**:
   - Informações: OS, Python, PyTorch, CUDA
   - Uso de CPU/RAM/GPU
   - Versão do modelo carregado

### 5.2 GERENCIAMENTO DE STREAM

#### 5.2.1 Tipos de Fonte Suportados

```python
class SourceType(str, Enum):
    VIDEO = "video"    # Arquivo MP4, AVI, MOV
    USB = "usb"        # Câmera USB/USB-C
    RTSP = "rtsp"      # Stream RTSP
    GIGE = "gige"      # Câmera GigE (Gigabit Ethernet)
```

#### 5.2.2 StreamManager (Singleton)

```python
class StreamManager(QObject):
    # Signals
    frame_available = Signal(np.ndarray)
    stream_started = Signal()
    stream_stopped = Signal()
    stream_error = Signal(str)
    
    # Métodos
    def start(self) -> bool
    def stop(self)
    def pause(self)
    def resume(self)
    def change_source(self, source_type: str, **params)
    def get_current_frame(self) -> Optional[np.ndarray]
    def get_fps(self) -> float
    def get_status(self) -> dict
```

#### 5.2.3 Source Adapters

```python
class BaseSourceAdapter(ABC):
    def open(self) -> bool
    def read(self) -> Optional[FrameInfo]
    def close(self)
    def get_properties(self) -> dict
    def get_fps(self) -> float

class VideoFileAdapter(BaseSourceAdapter):
    """Arquivo de vídeo (MP4, AVI, MOV). Suporta loop."""

class USBCameraAdapter(BaseSourceAdapter):
    """Câmera USB. Suporta USB-C."""

class RTSPAdapter(BaseSourceAdapter):
    """Stream RTSP."""

class GigECameraAdapter(BaseSourceAdapter):
    """Câmera GigE Vision. Porta padrão: 3956."""
```

### 5.3 DETECÇÃO E PREDIÇÃO

#### 5.3.1 Modelos Suportados

- **DETR** (facebook/detr-resnet-50)
- **RT-DETR** (PekingU/rtdetr_r50vd) - padrão
- Modelos customizados locais (`models/`)

#### 5.3.2 InferenceEngine (Singleton)

```python
class InferenceEngine(QObject):
    # Signals
    detection_event = Signal(object)  # DetectionEvent
    inference_started = Signal()
    inference_stopped = Signal()
    model_loaded = Signal(str)
    
    # Métodos
    def load_model(self, model_path: str, device: str) -> bool
    def start(self) -> bool
    def stop(self)
    def pause(self)
    def resume(self)
    def get_status(self) -> dict
```

#### 5.3.3 Eventos de Detecção

```python
@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float
    
    @property
    def center(self) -> Tuple[float, float]
    @property
    def width(self) -> float
    @property
    def height(self) -> float

@dataclass
class Detection:
    bbox: BoundingBox
    confidence: float
    class_id: int
    class_name: str
    
    @property
    def centroid(self) -> Tuple[float, float]

@dataclass
class DetectionResult:
    detections: List[Detection]
    inference_time_ms: float
    frame_id: int
    timestamp: datetime
    
    @property
    def best_detection(self) -> Optional[Detection]
    @property
    def count(self) -> int

@dataclass
class DetectionEvent:
    detected: bool
    class_name: str
    confidence: float
    bbox: List[float]
    centroid: Tuple[float, float]
    source_id: str
    frame_id: int
    timestamp: datetime
    
    def to_plc_data(self) -> dict:
        return {
            "product_detected": self.detected,
            "centroid_x": self.centroid[0],
            "centroid_y": self.centroid[1],
            "confidence": self.confidence,
        }
```

### 5.4 CONTROLE DE ROBÔ

#### 5.4.1 Estados da Máquina

```python
class RobotControlState(str, Enum):
    INITIALIZING = "INITIALIZING"
    WAITING_AUTHORIZATION = "WAITING_AUTHORIZATION"
    DETECTING = "DETECTING"
    SENDING_DATA = "SENDING_DATA"
    WAITING_ACK = "WAITING_ACK"
    ACK_CONFIRMED = "ACK_CONFIRMED"
    WAITING_PICK = "WAITING_PICK"
    WAITING_PLACE = "WAITING_PLACE"
    WAITING_CYCLE_START = "WAITING_CYCLE_START"
    READY_FOR_NEXT = "READY_FOR_NEXT"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    SAFETY_BLOCKED = "SAFETY_BLOCKED"
```

#### 5.4.2 Fluxo Sequencial

1. Sistema de visão indica pronto (`vision_ready = TRUE`)
2. Aguarda autorização do CLP (`plc_authorize_detection = TRUE`)
3. Detecta produto e encaminha coordenadas
4. Aguarda ACK do robô (`robot_ack = TRUE`)
5. Envia echo de confirmação (`vision_echo_ack = TRUE`)
6. Aguarda pick completo (`robot_pick_complete = TRUE`)
7. Aguarda place completo (`robot_place_complete = TRUE`)
8. Aguarda comando para novo ciclo (`plc_cycle_start = TRUE`)

### 5.5 PRÉ-PROCESSAMENTO

```python
class PreprocessPipeline:
    def process(self, frame: np.ndarray) -> np.ndarray
    def set_roi(self, roi: Optional[Tuple[int, int, int, int]])
    def set_brightness(self, value: float)
    def set_contrast(self, value: float)
```

### 5.6 SISTEMA DE LOGGING

#### 5.6.1 Logger Estruturado (structlog)

```python
def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """
    Configura logging estruturado com:
    - Formato JSON para arquivos
    - Formato colorido para console
    - ID de correlação para rastreamento
    - Timestamp ISO 8601
    """

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Retorna logger para componente."""
```

#### 5.6.2 Tipos de Logs

1. **Logs de Detecção**:
   - Detecção encontrada: classe, confiança, centroide
   - Tempo de inferência
   - Frame ID

2. **Logs de Comunicação CIP**:
   - Conexão estabelecida/perdida
   - Leitura/escrita de TAGs
   - Erros de comunicação
   - Tentativas de reconexão

3. **Logs de Processamento**:
   - Stream iniciado/parado
   - Modelo carregado
   - Erros de pré-processamento

4. **Logs de Controle**:
   - Mudanças de estado
   - Ciclos completados
   - Erros de timeout

#### 5.6.3 Formato de Log

```json
{
  "timestamp": "2025-01-24T12:00:00.000Z",
  "level": "INFO",
  "logger_name": "detection.engine",
  "correlation_id": "abc12345",
  "event": "detection_found",
  "class_name": "Embalagem",
  "confidence": 0.95,
  "centroid": {"x": 320.5, "y": 240.3},
  "inference_time_ms": 45.2
}
```

---

## 6. COMUNICAÇÃO CIP - ESPECIFICAÇÃO TÉCNICA

### 6.1 DEPENDÊNCIA OBRIGATÓRIA

```txt
# Biblioteca CIP para Omron NX102
aphyt>=2.1.9
```

### 6.2 PROTOCOLO DE TAGs

#### TAGs de ESCRITA (Visão → CLP)

| Nome Lógico | Nome CLP | Tipo | Descrição |
|-------------|----------|------|-----------|
| vision_ready | VisionCtrl.VisionReady | BOOL | Sistema de visão pronto |
| vision_busy | VisionCtrl.VisionBusy | BOOL | Sistema processando |
| vision_error | VisionCtrl.VisionError | BOOL | Erro no sistema |
| vision_heartbeat | VisionCtrl.Heartbeat | BOOL | Heartbeat (toggle) |
| product_detected | PRODUCT_DETECTED | BOOL | Produto detectado |
| centroid_x | CENTROID_X | REAL | Coordenada X do centroide |
| centroid_y | CENTROID_Y | REAL | Coordenada Y do centroide |
| confidence | CONFIDENCE | REAL | Confiança (0-1) |
| detection_count | DETECTION_COUNT | INT | Contador de detecções |
| processing_time | PROCESSING_TIME | REAL | Tempo de processamento (ms) |
| vision_echo_ack | VisionCtrl.EchoAck | BOOL | Echo de confirmação |
| vision_data_sent | VisionCtrl.DataSent | BOOL | Dados enviados |
| vision_ready_for_next | VisionCtrl.ReadyForNext | BOOL | Pronto para próximo ciclo |
| system_fault | SYSTEM_FAULT | BOOL | Falha do sistema |

#### TAGs de LEITURA (CLP → Visão)

| Nome Lógico | Nome CLP | Tipo | Descrição |
|-------------|----------|------|-----------|
| robot_ack | ROBOT_ACK | BOOL | ACK do robô |
| robot_ready | ROBOT_READY | BOOL | Robô pronto |
| robot_error | ROBOT_ERROR | BOOL | Erro no robô |
| robot_busy | RobotStatus.Busy | BOOL | Robô executando movimento |
| robot_pick_complete | RobotStatus.PickComplete | BOOL | Pick completado |
| robot_place_complete | RobotStatus.PlaceComplete | BOOL | Place completado |
| plc_authorize_detection | RobotCtrl.AuthorizeDetection | BOOL | CLP autoriza detecção |
| plc_cycle_start | RobotCtrl.CycleStart | BOOL | CLP solicita novo ciclo |
| plc_cycle_complete | RobotCtrl.CycleComplete | BOOL | Ciclo completo |
| plc_emergency_stop | RobotCtrl.EmergencyStop | BOOL | Parada de emergência |
| plc_system_mode | RobotCtrl.SystemMode | INT | Modo (0=Manual, 1=Auto, 2=Manutenção) |
| heartbeat | SystemStatus.Heartbeat | BOOL | Heartbeat do sistema |
| system_mode | SystemStatus.Mode | INT | Modo do sistema |

#### TAGs de Segurança (LEITURA)

| Nome Lógico | Nome CLP | Tipo | Descrição |
|-------------|----------|------|-----------|
| safety_gate_closed | Safety.GateClosed | BOOL | Portão fechado |
| safety_area_clear | Safety.AreaClear | BOOL | Área livre |
| safety_light_curtain_ok | Safety.LightCurtainOK | BOOL | Cortina de luz OK |
| safety_emergency_stop | Safety.EmergencyStop | BOOL | Emergência não ativa |

### 6.3 CLIENTE CIP PRINCIPAL

```python
class CIPClient:
    """
    Cliente CIP para comunicação com CLP Omron NX102.
    
    Características:
    - Conexão via EtherNet/IP (porta 44818)
    - Leitura e escrita de TAGs
    - Whitelist de TAGs permitidos
    - Reconexão automática com backoff
    - Fallback para modo simulado
    """
    
    def __init__(self, ip: str = "187.99.125.5", port: int = 44818, 
                 connection_timeout: float = 10.0, timeout_ms: int = 10000,
                 simulated: bool = False):
        ...
    
    async def connect(self) -> bool:
        """Conecta ao CLP. Tenta real, fallback para simulado."""
        ...
    
    async def disconnect(self) -> None:
        """Desconecta do CLP."""
        ...
    
    async def read_tag(self, logical_name: str) -> Any:
        """Lê valor de um TAG."""
        ...
    
    async def write_tag(self, logical_name: str, value: Any) -> bool:
        """Escreve valor em um TAG."""
        ...
    
    async def write_detection_result(
        self, detected: bool, centroid_x: float = 0,
        centroid_y: float = 0, confidence: float = 0
    ) -> bool:
        """Escreve resultado de detecção nos TAGs do CLP."""
        ...
    
    async def read_robot_ack(self) -> bool:
        """Lê o ACK do robô."""
        ...
    
    async def set_vision_ready(self, ready: bool) -> bool:
        """Define se o sistema de visão está pronto."""
        ...
    
    def get_status(self) -> dict:
        """Retorna status da conexão."""
        ...
```

### 6.4 CONEXÃO COM APHYT

```python
from aphyt import omron

def _connect_sync(self, ip: str, timeout: float) -> Any:
    """Conecta ao CLP de forma síncrona."""
    # IMPORTANTE: A classe correta é NSeries
    plc = omron.n_series.NSeries()
    
    if timeout and timeout > 0:
        plc.connect_explicit(ip, connection_timeout=timeout)
    else:
        plc.connect_explicit(ip)
    
    return plc
```

### 6.5 NOTAS IMPORTANTES

1. **Biblioteca aphyt**: Usar `omron.n_series.NSeries()` (não `NSeriesEIP`)
2. **Porta CIP**: 44818 (padrão EtherNet/IP)
3. **Timeout**: Mínimo 10s para handshake CIP completo
4. **Notação de ponto**: Evitar TAGs com `.` - causa `RecursionError` na biblioteca aphyt
5. **Fallback**: Sempre implementar fallback para modo simulado
6. **Thread separada**: Executar operações CIP em `ThreadPoolExecutor` para não bloquear UI
7. **Reconexão automática**: Implementar exponential backoff

### 6.6 SIMULADOR DE CLP

```python
class SimulatedPLC:
    """PLC simulado para desenvolvimento e testes."""
    
    def __init__(self):
        self._tags = {
            "VISION_READY": True,
            "PRODUCT_DETECTED": False,
            "CENTROID_X": 0.0,
            "CENTROID_Y": 0.0,
            "CONFIDENCE": 0.0,
            "ROBOT_ACK": False,
            "ROBOT_READY": True,
            "ROBOT_ERROR": False,
            "HEARTBEAT": False,
            "DETECTION_COUNT": 0,
        }
        self._ack_delay_seconds = 1.5
    
    def read_variable(self, name: str) -> Any:
        return self._tags.get(name, 0)
    
    def write_variable(self, name: str, value: Any) -> None:
        self._tags[name] = value
        # Auto ACK após detecção
        if name == "PRODUCT_DETECTED" and value:
            threading.Timer(1.5, self._auto_ack).start()
```

---

## 7. REQUISITOS NÃO FUNCIONAIS

### 7.1 Performance

| Requisito | Valor |
|-----------|-------|
| FPS de Inferência (CPU) | ≥ 15 FPS |
| FPS de Inferência (CUDA) | ≥ 30 FPS |
| Latência de Detecção (CPU) | < 500ms |
| Latência de Detecção (CUDA) | < 100ms |
| UI Responsiva | Sem travamentos |
| Uso de Memória | < 8 GB |

### 7.2 Confiabilidade

- ✅ **Reconexão Automática**: CLP desconectado → tentar reconectar a cada 5s
- ✅ **Tratamento de Erros**: Nenhum erro deve travar a aplicação
- ✅ **Validação de Entrada**: Todas as entradas do usuário validadas
- ✅ **Fallback**: Modo simulado se CLP não disponível

### 7.3 Usabilidade

- ✅ **Interface Intuitiva**: Operador consegue usar sem treinamento extenso
- ✅ **Feedback Visual**: Todas as ações têm feedback imediato
- ✅ **Alertas Claros**: Erros exibidos de forma clara e acionável
- ✅ **Atalhos de Teclado**: F5 (iniciar), F6 (parar), Ctrl+Q (sair)

### 7.4 Manutenibilidade

- ✅ **Código Limpo**: PEP 8, type hints, docstrings
- ✅ **Arquitetura Modular**: Componentes isolados
- ✅ **Documentação**: README, docstrings, comentários
- ✅ **Testes**: Testes unitários para componentes críticos

### 7.5 Segurança

- ✅ **Validação de Entrada**: Prevenir injection em comandos CIP
- ✅ **Whitelist de TAGs**: Apenas TAGs permitidos podem ser lidos/escritos
- ✅ **Logs de Auditoria**: Todas as operações críticas logadas

---

## 8. DEPENDÊNCIAS E VERSÕES

### 8.1 Dependências Python (requirements.txt)

```txt
# Interface
PySide6>=6.6.0

# Configuração
pydantic>=2.6.0
pydantic-settings>=2.2.0
pyyaml>=6.0.0

# ML/AI (DETR/RT-DETR)
torch>=2.0.0
torchvision>=0.15.0
transformers>=4.38.0
accelerate>=0.27.0
safetensors>=0.4.0

# Processamento de Imagem
opencv-python>=4.9.0
Pillow>=10.2.0
numpy>=1.24.0

# Comunicação CLP
aphyt>=2.1.9

# Logging
structlog>=24.1.0
colorama>=0.4.6

# Async
qasync>=0.27.0

# Gráficos (opcional)
matplotlib>=3.8.0
```

### 8.2 Instalação

**Ambiente Virtual:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

**GPU NVIDIA (CUDA):**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

---

## 9. PLANO DE IMPLEMENTAÇÃO

### Fase 1: Fundação (Semana 1-2)
- ✅ Estrutura de diretórios
- ✅ Configuração (Pydantic Settings + YAML)
- ✅ Sistema de logging estruturado
- ✅ MainWindow básico com abas
- ✅ Tema QSS industrial

### Fase 2: Streaming (Semana 2-3)
- ✅ StreamManager com adaptadores
- ✅ VideoWidget para exibir frames
- ✅ Threading para captura (QThread)
- ✅ Health check do stream

### Fase 3: Detecção (Semana 3-4)
- ✅ ModelLoader (Hugging Face + local)
- ✅ InferenceEngine com QThread
- ✅ Post-processing (NMS, filtros)
- ✅ Overlay de detecções no vídeo

### Fase 4: Comunicação CIP (Semana 4-5)
- ✅ CIPClient com aphyt
- ✅ TagMap e validação
- ✅ Reconexão automática
- ✅ Integração com UI (status)

### Fase 5: Controle de Robô (Semana 5-6)
- ✅ RobotController (máquina de estados)
- ✅ CycleProcessor
- ✅ Integração detecção → CLP

### Fase 6: UI Completa (Semana 6-7)
- ✅ Aba Operação (completa)
- ✅ Aba Configuração (completa)
- ✅ Aba Diagnósticos (métricas + logs)

### Fase 7: Polimento (Semana 7-8)
- ✅ Tratamento de erros robusto
- ✅ Testes unitários
- ✅ Documentação
- ✅ Otimizações de performance

---

## 10. CRITÉRIOS DE ACEITAÇÃO

### 10.1 Funcionalidade

- [ ] Todas as funcionalidades do sistema atual implementadas
- [ ] Interface com 3 abas funcionais (Operação, Configuração, Diagnósticos)
- [ ] Detecção em tempo real com overlay de bounding boxes
- [ ] Comunicação CIP com CLP Omron NX102 funcionando
- [ ] Controle de robô com máquina de estados
- [ ] Sistema de logs para detecções e erros
- [ ] Status de comunicação exibido na interface
- [ ] Suporte a múltiplas fontes de vídeo (arquivo, USB, RTSP, GigE)
- [ ] Suporte a modelos DETR e RT-DETR
- [ ] Modo simulado funcional

### 10.2 Performance

- [ ] FPS de inferência ≥ 15 (CPU) ou ≥ 30 (CUDA)
- [ ] UI responsiva (sem travamentos)
- [ ] Latência de detecção < 500ms (CPU) ou < 100ms (CUDA)

### 10.3 Estabilidade

- [ ] Aplicação não trava em erros
- [ ] Reconexão automática ao CLP
- [ ] Logs estruturados para debugging

### 10.4 Usabilidade

- [ ] Interface intuitiva para operador
- [ ] Configuração acessível para engenheiro
- [ ] Diagnósticos claros para supervisor

---

## ANEXOS

### Anexo A: Configuração Padrão (config.yaml)

```yaml
# Logging
log_level: INFO

# Streaming
streaming:
  source_type: video  # video, usb, rtsp, gige
  video_path: ../videos/test.mp4
  usb_camera_index: 0
  rtsp_url: ""
  gige_ip: ""
  gige_port: 3956
  max_frame_buffer_size: 30
  loop_video: true

# Detecção
detection:
  model_path: ../models
  default_model: PekingU/rtdetr_r50vd
  confidence_threshold: 0.5
  max_detections: 10
  target_classes: null  # null = todas
  inference_fps: 15
  device: cuda  # cpu, cuda, auto

# Pré-processamento
preprocess:
  profile: default
  brightness: 0
  contrast: 0
  roi: null  # null = frame completo

# Comunicação CIP
cip:
  ip: 187.99.125.5
  port: 44818
  connection_timeout: 10.0
  timeout_ms: 10000
  retry_interval: 2.0
  max_retries: 3
  simulated: false

# Mapeamento de TAGs
tags:
  VisionReady: VisionCtrl.VisionReady
  DetectionCount: VisionCtrl.DetectionCount
  BestCentroidX: VisionCtrl.BestCentroidX
  BestCentroidY: VisionCtrl.BestCentroidY
  BestConfidence: VisionCtrl.BestConfidence
  ProcessingTime: VisionCtrl.ProcessingTime
  RobotAck: RobotStatus.Ack
  RobotReady: RobotStatus.Ready
  RobotError: RobotStatus.Error
  Heartbeat: SystemStatus.Heartbeat
  SystemMode: SystemStatus.Mode
```

### Anexo B: Exemplo de MainWindow

```python
from PySide6.QtWidgets import QMainWindow, QTabWidget, QStatusBar
from PySide6.QtCore import Qt
from ui.pages.operation_page import OperationPage
from ui.pages.configuration_page import ConfigurationPage
from ui.pages.diagnostics_page import DiagnosticsPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Realtec Vision Buddmeyer v2.0")
        self.setMinimumSize(1280, 720)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(OperationPage(), "Operação")
        self.tabs.addTab(ConfigurationPage(), "Configuração")
        self.tabs.addTab(DiagnosticsPage(), "Diagnósticos")
        
        self.setCentralWidget(self.tabs)
        
        # Status bar
        self.statusBar().showMessage("Sistema inicializado")
```

### Anexo C: Referências

- **PySide6:** https://doc.qt.io/qtforpython/
- **PyTorch:** https://pytorch.org/docs/
- **Hugging Face Transformers:** https://huggingface.co/docs/transformers/
- **aphyt (CIP):** https://github.com/aphyt/aphyt
- **OpenCV:** https://docs.opencv.org/
- **RT-DETR:** https://huggingface.co/PekingU/rtdetr_r50vd

---

**Versão:** 2.0.0  
**Data:** Janeiro 2025  
**Autor:** Sistema de Automação Industrial  
**Plataforma:** Windows 10/11  
**Framework UI:** PySide6

# -*- coding: utf-8 -*-
"""
Página de Operação - Aba principal para operação do sistema.
"""

import asyncio
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QComboBox, QLabel, QFileDialog,
    QSplitter, QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QFont, QKeySequence, QShortcut

from config import get_settings
from core.logger import get_logger
from core.metrics import MetricsCollector
from streaming import StreamManager
from detection import InferenceEngine
from communication import CIPClient
from control import RobotController

from ui.widgets.video_widget import VideoWidget
from ui.widgets.status_panel import StatusPanel
from ui.widgets.event_console import EventConsole


class OperationPage(QWidget):
    """
    Página de Operação.
    
    Contém:
    - Widget de vídeo com detecções
    - Painel de status lateral
    - Console de eventos
    - Controles de operação
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._logger = get_logger("ui.operation")
        self._settings = get_settings()
        self._stream_manager = StreamManager()
        self._inference_engine = InferenceEngine()
        self._cip_client = CIPClient()
        self._robot_controller = RobotController()
        
        self._is_running = False
        
        # Contador de frames para comunicação periódica com CLP
        self._frame_count = 0
        self._communication_interval = 25  # Comunicar a cada 25 frames
        self._last_best_detection = None  # Armazena última melhor detecção
        self._detection_count = 0  # Contador total de detecções
        self._error_count = 0  # Contador total de erros
        
        self._setup_ui()
        self._sync_combo_to_settings()
        self._connect_signals()
        self._setup_shortcuts()
    
    def _setup_ui(self) -> None:
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Splitter principal (horizontal)
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Área central (vídeo + console)
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(8)
        
        # Widget de vídeo
        self._video_widget = VideoWidget()
        self._video_widget.double_clicked.connect(self._toggle_fullscreen)
        central_layout.addWidget(self._video_widget, stretch=3)
        
        # Legenda da fonte atual (abaixo do vídeo)
        self._source_caption = QLabel()
        self._source_caption.setStyleSheet("color: #8b9dc3; font-size: 11px; padding: 2px 0;")
        self._source_caption.setAlignment(Qt.AlignCenter)
        central_layout.addWidget(self._source_caption)
        
        # Console de eventos
        console_group = QGroupBox("Eventos")
        console_group.setStyleSheet("""
            QGroupBox {
                color: #e0e0e0;
                border: 1px solid #3d4852;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
            }
        """)
        console_layout = QVBoxLayout(console_group)
        self._event_console = EventConsole()
        self._event_console.setMinimumHeight(140)
        console_layout.addWidget(self._event_console)
        central_layout.addWidget(console_group, stretch=1)
        
        main_splitter.addWidget(central_widget)
        
        # Painel de status (direita)
        self._status_panel = StatusPanel()
        main_splitter.addWidget(self._status_panel)
        
        # Proporções do splitter
        main_splitter.setSizes([800, 280])
        
        layout.addWidget(main_splitter, stretch=1)
        
        # Barra de status da etapa atual (pick-and-place)
        status_bar = QFrame()
        status_bar.setStyleSheet("""
            QFrame {
                background-color: #252d3a;
                border: 1px solid #3d4852;
                border-radius: 4px;
            }
        """)
        status_bar.setMinimumHeight(44)
        status_bar_layout = QHBoxLayout(status_bar)
        status_bar_layout.setContentsMargins(12, 8, 12, 8)
        status_label = QLabel("Status atual:")
        status_label.setStyleSheet("color: #adb5bd; font-size: 11px; font-weight: bold;")
        status_bar_layout.addWidget(status_label)
        self._status_step_label = QLabel("—")
        self._status_step_label.setStyleSheet("color: #00d4ff; font-weight: bold; font-size: 11px;")
        self._status_step_label.setWordWrap(True)
        status_bar_layout.addWidget(self._status_step_label, stretch=1)
        layout.addWidget(status_bar)
        
        # Barra de controles (inferior)
        controls_frame = QFrame()
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #1e2836;
                border: 1px solid #2d3748;
                border-radius: 4px;
            }
        """)
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(12, 8, 12, 8)
        controls_layout.setSpacing(12)
        
        # Seletor de fonte
        controls_layout.addWidget(QLabel("Fonte:"))
        
        self._source_combo = QComboBox()
        self._source_combo.setMinimumWidth(150)
        self._source_combo.addItems([
            "Arquivo de Vídeo",
            "Câmera USB",
            "Stream RTSP",
            "Câmera GigE",
        ])
        self._source_combo.currentIndexChanged.connect(self._on_source_changed)
        controls_layout.addWidget(self._source_combo)
        
        self._source_path_btn = QPushButton("Selecionar...")
        self._source_path_btn.clicked.connect(self._select_video_file)
        controls_layout.addWidget(self._source_path_btn)
        
        controls_layout.addStretch()
        
        # Botões de controle
        self._play_btn = QPushButton("▶ Iniciar")
        self._play_btn.setMinimumWidth(100)
        self._play_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self._play_btn.clicked.connect(self._start_system)
        controls_layout.addWidget(self._play_btn)
        
        self._pause_btn = QPushButton("⏸ Pausar")
        self._pause_btn.setMinimumWidth(100)
        self._pause_btn.setEnabled(False)
        self._pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: black;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: white;
            }
        """)
        self._pause_btn.clicked.connect(self._toggle_pause)
        controls_layout.addWidget(self._pause_btn)
        
        self._stop_btn = QPushButton("⏹ Parar")
        self._stop_btn.setMinimumWidth(100)
        self._stop_btn.setEnabled(False)
        self._stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self._stop_btn.clicked.connect(self._stop_system)
        controls_layout.addWidget(self._stop_btn)
        
        # Separador visual
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("background-color: #3d4852;")
        controls_layout.addWidget(sep)
        
        # Autorizar envio ao CLP (modo manual, apos deteccao)
        self._authorize_send_btn = QPushButton("Autorizar envio ao CLP")
        self._authorize_send_btn.setMinimumWidth(140)
        self._authorize_send_btn.setEnabled(False)
        self._authorize_send_btn.setVisible(False)
        self._authorize_send_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self._authorize_send_btn.setToolTip("Objeto detectado. Clique para enviar coordenadas ao CLP e iniciar o ciclo.")
        self._authorize_send_btn.clicked.connect(self._authorize_send_to_plc)
        controls_layout.addWidget(self._authorize_send_btn)
        
        # Controles de ciclo pick-and-place
        self._continuous_cb = QCheckBox("Modo Continuo")
        self._continuous_cb.setChecked(False)
        self._continuous_cb.setToolTip(
            "Marcado: ciclos de pick-and-place executam automaticamente.\n"
            "Desmarcado: aguarda 'Novo Ciclo' ao final de cada ciclo."
        )
        self._continuous_cb.stateChanged.connect(self._on_cycle_mode_changed)
        controls_layout.addWidget(self._continuous_cb)
        
        self._new_cycle_btn = QPushButton("Novo Ciclo")
        self._new_cycle_btn.setMinimumWidth(100)
        self._new_cycle_btn.setEnabled(False)
        self._new_cycle_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self._new_cycle_btn.setToolTip("Autoriza o proximo ciclo de pick-and-place (modo manual)")
        self._new_cycle_btn.clicked.connect(self._authorize_new_cycle)
        controls_layout.addWidget(self._new_cycle_btn)
        
        layout.addWidget(controls_frame)
    
    def _sync_combo_to_settings(self) -> None:
        """Sincroniza o combo de fonte com o source_type do settings."""
        source_type_map = {"video": 0, "usb": 1, "rtsp": 2, "gige": 3}
        current_source = self._settings.streaming.source_type
        combo_index = source_type_map.get(current_source, 1)  # 1 = usb como padrão
        self._source_combo.setCurrentIndex(combo_index)
        # Atualiza visibilidade do botão de seleção de arquivo
        self._source_path_btn.setVisible(combo_index == 0)
        self._update_source_caption()
    
    def _update_source_caption(self) -> None:
        """Atualiza a legenda da fonte atual (abaixo do vídeo)."""
        idx = self._source_combo.currentIndex()
        if idx == 0:
            path = self._settings.streaming.video_path or "—"
            name = Path(path).name if path != "—" else path
            self._source_caption.setText(f"Fonte: Arquivo de vídeo — {name}")
        elif idx == 1:
            cam = self._settings.streaming.usb_camera_index
            self._source_caption.setText(f"Fonte: Câmera USB (índice {cam})")
        elif idx == 2:
            self._source_caption.setText("Fonte: Stream RTSP")
        else:
            self._source_caption.setText("Fonte: Câmera GigE")
    
    def _connect_signals(self) -> None:
        """Conecta os sinais."""
        # Stream
        self._stream_manager.frame_available.connect(self._video_widget.update_frame)
        self._stream_manager.frame_info_available.connect(self._on_frame_available)
        self._stream_manager.stream_started.connect(self._on_stream_started)
        self._stream_manager.stream_stopped.connect(self._on_stream_stopped)
        self._stream_manager.stream_error.connect(self._on_stream_error)
        
        # Inferência
        self._inference_engine.detection_result.connect(self._video_widget.update_detections)
        self._inference_engine.detection_event.connect(self._on_detection)
        
        # CIP
        self._cip_client.state_changed.connect(self._status_panel.set_connection_state)
        self._cip_client.connection_error.connect(self._on_cip_error)
        
        # Robô
        self._robot_controller.state_changed.connect(self._status_panel.set_robot_state)
        self._robot_controller.state_changed.connect(self._on_robot_state_changed)
        self._robot_controller.cycle_completed.connect(self._on_cycle_completed)
        self._robot_controller.error_occurred.connect(self._on_robot_error)
        self._robot_controller.cycle_step.connect(self._on_cycle_step)
        self._robot_controller.cycle_summary.connect(self._on_cycle_summary)
        
        # Timer para atualizar FPS
        self._fps_timer = QTimer(self)
        self._fps_timer.timeout.connect(self._update_fps)
        self._fps_timer.start(500)
    
    def _setup_shortcuts(self) -> None:
        """Configura atalhos de teclado."""
        # F5 - Iniciar
        start_shortcut = QShortcut(QKeySequence("F5"), self)
        start_shortcut.activated.connect(self._start_system)
        
        # F6 - Parar
        stop_shortcut = QShortcut(QKeySequence("F6"), self)
        stop_shortcut.activated.connect(self._stop_system)
        
        # F11 - Fullscreen
        fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        fullscreen_shortcut.activated.connect(self._toggle_fullscreen)
    
    @Slot()
    def _start_system(self) -> None:
        """Inicia o sistema."""
        if self._is_running:
            return
        
        # Determina fonte selecionada na UI
        source_types = ["video", "usb", "rtsp", "gige"]
        source_labels = ["Arquivo de Vídeo", "Câmera USB", "Stream RTSP", "Câmera GigE"]
        source_index = self._source_combo.currentIndex()
        source_type = source_types[source_index]
        
        self._event_console.add_info(
            f"Iniciando sistema com fonte: {source_labels[source_index]}..."
        )
        self._logger.info("start_system_requested", source_type=source_type)
        
        # Atualiza fonte em memória
        self._settings.streaming.source_type = source_type
        
        # Validação prévia específica para vídeo (arquivo)
        if source_type == "video":
            video_path_str = self._settings.streaming.video_path
            video_path = Path(video_path_str)
            
            # Normaliza caminho (resolve relativos e absolutos)
            if not video_path.is_absolute():
                base_path = Path(__file__).parent.parent.parent
                video_path = base_path / video_path_str
            
            try:
                video_path = video_path.resolve()
            except Exception as e:
                self._logger.warning("path_resolve_failed", path=str(video_path), error=str(e))
            
            # Verifica se arquivo existe
            if not video_path.exists():
                error_msg = (
                    f"Arquivo de vídeo não encontrado:\n"
                    f"{video_path}\n\n"
                    f"Por favor, selecione um arquivo válido usando o botão 'Selecionar...'"
                )
                self._event_console.add_error(error_msg)
                self._logger.error("video_not_found_on_start", path=str(video_path))
                return
            
            # Verifica se é um arquivo válido (não é diretório)
            if not video_path.is_file():
                error_msg = f"O caminho especificado não é um arquivo: {video_path}"
                self._event_console.add_error(error_msg)
                self._logger.error("video_path_is_not_file", path=str(video_path))
                return
            
            # Testa se OpenCV consegue abrir o arquivo
            import cv2
            test_cap = cv2.VideoCapture(str(video_path))
            if not test_cap.isOpened():
                test_cap.release()
                error_msg = (
                    f"Não foi possível abrir o arquivo de vídeo:\n"
                    f"{video_path}\n\n"
                    f"O arquivo pode estar corrompido ou em formato não suportado.\n"
                    f"Formatos suportados: MP4, AVI, MOV, MKV"
                )
                self._event_console.add_error(error_msg)
                self._logger.error("video_cannot_open", path=str(video_path))
                return
            test_cap.release()
            
            # Atualiza com caminho normalizado
            self._settings.streaming.video_path = str(video_path)
            self._logger.info("video_validated", path=str(video_path))
        
        # Atualiza configuração do StreamManager com os parâmetros da fonte
        # change_source() atualiza o singleton em memória; start() usará esses valores
        if source_type == "video":
            self._stream_manager.change_source(
                source_type=source_type,
                video_path=self._settings.streaming.video_path,
                loop_video=self._settings.streaming.loop_video,
            )
        elif source_type == "usb":
            self._stream_manager.change_source(
                source_type=source_type,
                camera_index=self._settings.streaming.usb_camera_index,
            )
        elif source_type == "rtsp":
            self._stream_manager.change_source(
                source_type=source_type,
                rtsp_url=self._settings.streaming.rtsp_url,
            )
        elif source_type == "gige":
            self._stream_manager.change_source(
                source_type=source_type,
                gige_ip=self._settings.streaming.gige_ip,
                gige_port=self._settings.streaming.gige_port,
            )
        
        # Inicia stream (usa configurações em memória, NÃO recarrega do YAML)
        if not self._stream_manager.start():
            self._event_console.add_error(
                f"Falha ao iniciar stream ({source_labels[source_index]})"
            )
            return
        
        self._event_console.add_info(
            f"Stream iniciado: {source_labels[source_index]}"
        )
        
        # Carrega modelo (se não carregado)
        if not self._inference_engine.is_model_loaded:
            self._event_console.add_info("Carregando modelo de detecção...")
            if not self._inference_engine.load_model():
                self._event_console.add_error("Falha ao carregar modelo")
                self._stream_manager.stop()
                return
        
        # Inicia inferência
        if not self._inference_engine.start():
            self._event_console.add_error("Falha ao iniciar inferência")
            self._stream_manager.stop()
            return
        
        self._event_console.add_info("Inferência iniciada - detecção ativa")
        
        # Aplica modo de ciclo antes de iniciar o controlador
        cycle_mode = "continuous" if self._continuous_cb.isChecked() else "manual"
        self._robot_controller.set_cycle_mode(cycle_mode)
        
        # Conecta ao CLP e inicia controlador de robô
        asyncio.create_task(self._connect_plc_and_start_robot())
        
        self._is_running = True
        self._update_ui_state()
        
        self._event_console.add_success(
            f"Sistema iniciado [{source_labels[source_index]}]"
        )
        self._status_panel.set_system_status("RUNNING")
    
    async def _connect_plc_and_start_robot(self) -> None:
        """
        Conecta ao CLP em modo real por default.
        Se falhar, avisa e inicia em modo simulado com robo virtual.
        """
        try:
            # Tenta conectar (real primeiro, fallback para simulado)
            await self._cip_client.connect()
            
            if self._cip_client.is_simulated:
                self._event_console.add_warning(
                    "CLP real nao alcancavel - operando em modo SIMULADO.\n"
                    "Robo virtual ativo: pick-and-place simulado com delays."
                )
                self._logger.warning("plc_fallback_to_simulated")
            else:
                self._event_console.add_success(
                    f"Conectado ao CLP real ({self._settings.cip.ip}:{self._settings.cip.port})"
                )
            
            # Seta VisionReady = True
            try:
                await self._cip_client.set_vision_ready(True)
                self._event_console.add_info("VisionReady = True enviado ao CLP")
            except Exception as e:
                self._logger.warning("failed_to_set_vision_ready", error=str(e))
            
            # Inicia controlador de robo (funciona em real e simulado)
            self._robot_controller.start()
            mode_label = "continuo" if self._continuous_cb.isChecked() else "manual"
            self._event_console.add_info(
                f"Controlador de robo iniciado (modo {mode_label})"
            )
                
        except Exception as e:
            self._event_console.add_warning(
                f"Erro ao conectar CLP: {e}\n"
                f"Sistema operando em modo simulado."
            )
            self._logger.error("plc_connect_exception", error=str(e))
            # Garante conexão simulada
            if not self._cip_client.is_connected:
                await self._cip_client._connect_simulated()
            self._robot_controller.start()
    
    async def _connect_plc(self) -> None:
        """Conecta ao CLP."""
        try:
            await self._cip_client.connect()
            self._event_console.add_success("Conectado ao CLP")
        except Exception as e:
            self._event_console.add_warning(f"CLP em modo simulado: {e}")
    
    def _communicate_centroid_to_plc(self) -> None:
        """
        Comunica as coordenadas do centroide ao CLP.
        
        Chamado a cada 25 frames.
        Usa as TAGs definidas: CENTROID_X, CENTROID_Y, CONFIDENCE, etc.
        Inclui handshake básico: só envia se CLP conectado e visão OK.
        """
        if self._last_best_detection is None:
            return
        
        # Handshake básico: verifica estado do CLP
        if not self._cip_client._state.is_connected:
            self._logger.debug("skipping_centroid_plc_not_connected")
            return
        
        # Verifica se está em modo saudável (não degradado)
        if self._cip_client._state.status.value == "degraded":
            self._logger.debug("skipping_centroid_plc_degraded")
            return
        
        detection = self._last_best_detection
        centroid_x = detection.centroid[0]
        centroid_y = detection.centroid[1]
        confidence = detection.confidence
        
        # Log da comunicação
        self._logger.info(
            "communicating_centroid_to_plc",
            frame=self._frame_count,
            centroid_x=centroid_x,
            centroid_y=centroid_y,
            confidence=confidence,
            plc_status=self._cip_client._state.status.value,
        )
        
        # Mensagem no console (a cada 25 frames para não poluir)
        self._event_console.add_info(
            f"[Frame {self._frame_count}] Enviando centroide: ({centroid_x:.1f}, {centroid_y:.1f}) - Conf: {confidence:.0%}",
            "CLP"
        )
        
        # Envia dados ao CLP usando as TAGs definidas
        asyncio.create_task(self._send_detection_to_plc(
            centroid_x=centroid_x,
            centroid_y=centroid_y,
            confidence=confidence,
            detection_count=detection.detection_count,
            processing_time=detection.inference_time_ms,
        ))
    
    async def _send_detection_to_plc(
        self,
        centroid_x: float,
        centroid_y: float,
        confidence: float,
        detection_count: int,
        processing_time: float,
    ) -> None:
        """
        Envia dados de detecção ao CLP via TAGs com handshake básico.
        
        Handshake:
        1. Verifica se CLP está conectado
        2. (Opcional) Lê RobotReady para confirmar que CLP aceita dados
        3. Escreve as TAGs de detecção
        
        TAGs utilizadas:
        - PRODUCT_DETECTED: bool
        - CENTROID_X: float
        - CENTROID_Y: float
        - CONFIDENCE: float
        - DETECTION_COUNT: int
        - PROCESSING_TIME: float
        """
        try:
            # Checagem de status antes de enviar
            if not self._cip_client._state.is_connected:
                self._logger.debug("send_detection_skipped_not_connected")
                return
            
            # Handshake: tenta ler RobotReady (se falhar, continua mesmo assim)
            robot_ready = True  # Default para modo simulado ou se leitura falhar
            try:
                robot_ready = await self._cip_client.read_tag("RobotReady")
            except Exception:
                pass  # Em modo simulado ou erro de leitura, assume ready
            
            if not robot_ready:
                self._logger.debug("send_detection_skipped_robot_not_ready")
                return
            
            # Usa o método write_detection_result do CIPClient
            await self._cip_client.write_detection_result(
                detected=True,
                centroid_x=centroid_x,
                centroid_y=centroid_y,
                confidence=confidence,
                detection_count=detection_count,
                processing_time=processing_time,
            )
            
            self._logger.debug(
                "detection_sent_to_plc",
                centroid_x=centroid_x,
                centroid_y=centroid_y,
                robot_ready=robot_ready,
            )
            
        except Exception as e:
            self._logger.warning("failed_to_send_detection", error=str(e))
            self._status_panel.set_last_error(str(e))
    
    async def _shutdown_plc_connection(self) -> None:
        """Seta VisionReady = False e desconecta do CLP."""
        try:
            if self._cip_client._state.is_connected:
                await self._cip_client.set_vision_ready(False)
                self._logger.info("vision_ready_false_sent")
        except Exception as e:
            self._logger.warning("failed_to_set_vision_ready_false", error=str(e))
        finally:
            await self._cip_client.disconnect()
    
    @Slot()
    def _stop_system(self) -> None:
        """Para o sistema."""
        if not self._is_running:
            return
        
        self._event_console.add_info("Parando sistema...")
        
        # Para componentes
        self._robot_controller.stop()
        self._inference_engine.stop()
        self._stream_manager.stop()
        
        # Seta VisionReady = False e desconecta CLP
        asyncio.create_task(self._shutdown_plc_connection())
        
        self._is_running = False
        self._frame_count = 0
        self._last_best_detection = None
        self._update_ui_state()
        
        # Reseta texto do botão pause caso estivesse pausado
        self._pause_btn.setText("⏸ Pausar")
        
        self._video_widget.clear()
        
        self._event_console.add_info("Sistema parado")
        self._status_panel.set_system_status("STOPPED")
    
    @Slot()
    def _toggle_pause(self) -> None:
        """Alterna pause/resume do stream e da inferência."""
        if not self._is_running:
            return
        
        if self._stream_manager._worker and self._stream_manager._worker._paused:
            # Resumir
            self._stream_manager.resume()
            self._inference_engine.start()
            self._pause_btn.setText("⏸ Pausar")
            self._event_console.add_info("Sistema retomado")
            self._status_panel.set_system_status("RUNNING")
            self._logger.info("system_resumed")
        else:
            # Pausar
            self._stream_manager.pause()
            self._inference_engine.stop()
            self._pause_btn.setText("▶ Retomar")
            self._event_console.add_info("Sistema pausado")
            self._status_panel.set_system_status("PAUSED")
            self._logger.info("system_paused")
    
    def _update_ui_state(self) -> None:
        """Atualiza estado da UI."""
        self._play_btn.setEnabled(not self._is_running)
        self._pause_btn.setEnabled(self._is_running)
        self._stop_btn.setEnabled(self._is_running)
        self._source_combo.setEnabled(not self._is_running)
        self._source_path_btn.setEnabled(True)  # Sempre habilitado
        
        # Controles de ciclo
        is_manual = not self._continuous_cb.isChecked()
        self._new_cycle_btn.setEnabled(
            self._is_running and is_manual
            and self._robot_controller.state.value == "READY_FOR_NEXT"
        )
        
        if not self._is_running:
            self._status_step_label.setText("—")
            self._authorize_send_btn.setVisible(False)
            self._authorize_send_btn.setEnabled(False)
        
        self._status_panel.set_stream_running(self._is_running)
        self._status_panel.set_inference_running(self._is_running)
    
    def _on_source_changed(self, index: int) -> None:
        """Handler para mudança de fonte."""
        # Mostra botão de seleção apenas para vídeo
        self._source_path_btn.setVisible(index == 0)
        self._update_source_caption()
    
    def _select_video_file(self) -> None:
        """Abre diálogo para selecionar vídeo."""
        # Obtém diretório inicial (tenta usar o último caminho ou diretório padrão)
        initial_dir = None
        current_path = self._settings.streaming.video_path
        if current_path:
            current_path_obj = Path(current_path)
            if current_path_obj.exists():
                initial_dir = str(current_path_obj.parent)
            elif current_path_obj.parent.exists():
                initial_dir = str(current_path_obj.parent)
        
        if not initial_dir:
            # Usa diretório padrão de vídeos
            base_path = Path(__file__).parent.parent.parent
            initial_dir = str(base_path / "videos")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Vídeo",
            initial_dir,
            "Vídeos (*.mp4 *.avi *.mov *.mkv);;Todos os Arquivos (*)",
        )
        
        if file_path:
            file_path_obj = Path(file_path)
            
            # Validações
            if not file_path_obj.exists():
                self._event_console.add_error(
                    f"Arquivo não encontrado: {file_path}\n"
                    f"Por favor, verifique se o arquivo existe."
                )
                return
            
            if not file_path_obj.is_file():
                self._event_console.add_error(
                    f"O caminho especificado não é um arquivo: {file_path}"
                )
                return
            
            # Testa se OpenCV consegue abrir
            import cv2
            test_cap = cv2.VideoCapture(str(file_path_obj))
            if not test_cap.isOpened():
                test_cap.release()
                self._event_console.add_error(
                    f"Não foi possível abrir o arquivo de vídeo:\n"
                    f"{file_path}\n\n"
                    f"O arquivo pode estar corrompido ou em formato não suportado.\n"
                    f"Formatos suportados: MP4, AVI, MOV, MKV"
                )
                return
            test_cap.release()
            
            # Converte para caminho absoluto normalizado
            abs_path = file_path_obj.resolve()
            abs_path_str = str(abs_path)
            
            # Atualiza configuração
            self._settings.streaming.video_path = abs_path_str
            
            # Log
            self._logger.info("video_selected", path=abs_path_str)
            self._event_console.add_info(f"Vídeo selecionado: {file_path_obj.name}")
            
            # Se o sistema está rodando, atualiza o stream sem parar a inferência
            if self._is_running and self._stream_manager.is_running:
                self._event_console.add_info("Atualizando stream para novo vídeo...")
                
                # Muda a fonte; change_source reinicia automaticamente se estava rodando
                success = self._stream_manager.change_source(
                    source_type="video",
                    video_path=abs_path_str,
                    loop_video=self._settings.streaming.loop_video,
                )
                
                if success:
                    # Atualiza o combo para refletir a nova fonte
                    self._source_combo.blockSignals(True)
                    self._source_combo.setCurrentIndex(0)  # "Arquivo de Vídeo"
                    self._source_combo.blockSignals(False)
                    self._source_path_btn.setVisible(True)
                    
                    self._event_console.add_success(f"Stream atualizado para: {file_path_obj.name}")
                    self._logger.info("video_changed_during_runtime", path=abs_path_str)
                else:
                    # O stream falhou ao trocar — para o sistema inteiro para estado consistente
                    self._event_console.add_error(
                        f"Falha ao abrir vídeo: {file_path_obj.name}\n"
                        f"O sistema será parado. Reinicie manualmente."
                    )
                    self._logger.error("video_change_failed_stopping_system", path=abs_path_str)
                    self._stop_system()
            else:
                # Sistema não está rodando, apenas atualiza configuração em memória
                self._stream_manager.change_source(
                    source_type="video",
                    video_path=abs_path_str,
                    loop_video=self._settings.streaming.loop_video,
                )
                # Atualiza o combo para refletir a nova fonte
                self._source_combo.blockSignals(True)
                self._source_combo.setCurrentIndex(0)  # "Arquivo de Vídeo"
                self._source_combo.blockSignals(False)
                self._source_path_btn.setVisible(True)
    
    def _toggle_fullscreen(self) -> None:
        """Alterna fullscreen do vídeo."""
        main_window = self.window()
        if main_window is None:
            return
        
        if main_window.isFullScreen():
            main_window.showNormal()
            self._event_console.add_info("Saiu do modo tela cheia")
        else:
            main_window.showFullScreen()
            self._event_console.add_info("Modo tela cheia (F11 para sair)")
    
    def _update_fps(self) -> None:
        """Atualiza FPS no widget de vídeo e latência CIP no painel (RF-06)."""
        if self._stream_manager.is_running:
            fps = self._stream_manager.get_fps()
            self._video_widget.set_fps(fps)
        latency_ms = MetricsCollector().get_last_value("cip_response_time")
        self._status_panel.set_latency_ms(latency_ms)
    
    @Slot()
    def _on_stream_started(self) -> None:
        """Handler para stream iniciado."""
        self._event_console.add_info("Stream iniciado", "Stream")
    
    @Slot()
    def _on_stream_stopped(self) -> None:
        """Handler para stream parado (inclusive por falha em change_source)."""
        self._event_console.add_info("Stream parado", "Stream")
        
        # Se a UI ainda pensa que está rodando mas o stream parou,
        # precisamos sincronizar o estado para evitar inconsistência.
        if self._is_running and not self._stream_manager.is_running:
            self._logger.warning("stream_stopped_unexpectedly_resetting_state")
            self._stop_system()
    
    @Slot(str)
    def _on_stream_error(self, error: str) -> None:
        """Handler para erro de stream."""
        self._event_console.add_error(f"Erro de stream: {error}", "Stream")
    
    @Slot(object)
    def _on_frame_available(self, frame_info) -> None:
        """Handler para frame disponível - envia para inferência."""
        if self._is_running and self._inference_engine.is_running:
            self._inference_engine.process_frame(frame_info.frame, frame_info.frame_id)
            
            # Incrementa contador de frames
            self._frame_count += 1
            
            # A cada 25 frames, comunica coordenadas ao CLP se houver detecção
            if self._frame_count % self._communication_interval == 0:
                self._communicate_centroid_to_plc()
    
    @Slot(object)
    def _on_detection(self, event) -> None:
        """Handler para detecção."""
        if event.detected:
            # Armazena a melhor detecção para comunicação periódica
            self._last_best_detection = event
            self._detection_count += 1
            
            self._event_console.add_success(
                f"Detectado: {event.class_name} ({event.confidence:.0%})",
                "Detecção"
            )
            self._status_panel.update_detection(event)
            self._status_panel.set_detection_count(self._detection_count)
            
            # Processa no controlador de robô
            self._robot_controller.process_detection(event)
    
    @Slot(int)
    def _on_cycle_completed(self, cycle_number: int) -> None:
        """Handler para ciclo completado."""
        self._event_console.add_success(f"Ciclo {cycle_number} completado", "Robô")
        self._status_panel.set_cycle_count(cycle_number)
    
    def _on_cycle_mode_changed(self, state: int) -> None:
        """Handler para mudança de modo de ciclo (manual/contínuo)."""
        mode = "continuous" if self._continuous_cb.isChecked() else "manual"
        self._robot_controller.set_cycle_mode(mode)
        self._new_cycle_btn.setEnabled(not self._continuous_cb.isChecked() and self._is_running)
        label = "Contínuo" if mode == "continuous" else "Manual"
        self._event_console.add_info(f"Modo de ciclo: {label}")
    
    def _authorize_new_cycle(self) -> None:
        """Autoriza o próximo ciclo de pick-and-place (modo manual)."""
        self._robot_controller.authorize_next_cycle()
        self._new_cycle_btn.setEnabled(False)
        self._event_console.add_info("Novo ciclo autorizado pelo operador")
    
    def _authorize_send_to_plc(self) -> None:
        """Autoriza envio das coordenadas ao CLP apos deteccao (modo manual)."""
        self._robot_controller.authorize_send_to_plc()
        self._authorize_send_btn.setEnabled(False)
        self._event_console.add_info("Envio ao CLP autorizado pelo operador")
    
    def _status_message_for_state(self, state_value: str) -> str:
        """Mensagem amigavel para a barra de status conforme estado do robo."""
        from control.robot_controller import RobotControlState
        messages = {
            RobotControlState.INITIALIZING.value: "Inicializando conexao com CLP...",
            RobotControlState.WAITING_AUTHORIZATION.value: "Aguardando autorizacao do CLP para deteccao...",
            RobotControlState.DETECTING.value: "Aguardando deteccao de embalagem...",
            RobotControlState.WAITING_SEND_AUTHORIZATION.value: "Objeto detectado. Aguardando autorizacao para envio ao CLP.",
            RobotControlState.SENDING_DATA.value: "Enviando coordenadas ao CLP...",
            RobotControlState.WAITING_ACK.value: "Aguardando ACK do robo...",
            RobotControlState.ACK_CONFIRMED.value: "ACK recebido. Aguardando PICK...",
            RobotControlState.WAITING_PICK.value: "Aguardando PICK (coleta)...",
            RobotControlState.WAITING_PLACE.value: "Aguardando PLACE (posicionamento)...",
            RobotControlState.WAITING_CYCLE_START.value: "Aguardando sinal de ciclo completo...",
            RobotControlState.READY_FOR_NEXT.value: "Ciclo finalizado. Aguardando 'Novo Ciclo' (modo manual).",
            RobotControlState.ERROR.value: "Erro no ciclo.",
            RobotControlState.TIMEOUT.value: "Timeout. Aguardando novo ciclo.",
            RobotControlState.SAFETY_BLOCKED.value: "Seguranca ativa. Aguardando liberacao.",
            RobotControlState.STOPPED.value: "Parado.",
        }
        return messages.get(state_value, state_value)
    
    @Slot(str)
    def _on_robot_state_changed(self, state_value: str) -> None:
        """Handler para mudanca de estado do robo: botoes e barra de status."""
        from control.robot_controller import RobotControlState
        
        # Barra de status
        self._status_step_label.setText(self._status_message_for_state(state_value))
        
        # Botao Novo Ciclo
        if (
            state_value == RobotControlState.READY_FOR_NEXT.value
            and self._robot_controller.cycle_mode == "manual"
            and self._is_running
        ):
            self._new_cycle_btn.setEnabled(True)
        else:
            self._new_cycle_btn.setEnabled(False)
        
        # Botao Autorizar envio ao CLP (modo manual, apos deteccao)
        if (
            state_value == RobotControlState.WAITING_SEND_AUTHORIZATION.value
            and self._robot_controller.cycle_mode == "manual"
            and self._is_running
        ):
            self._authorize_send_btn.setVisible(True)
            self._authorize_send_btn.setEnabled(True)
        else:
            self._authorize_send_btn.setVisible(False)
            self._authorize_send_btn.setEnabled(False)
    
    @Slot(str)
    def _on_cycle_step(self, step: str) -> None:
        """Handler para etapa do ciclo — exibe no console e na barra de status."""
        self._event_console.add_info(f"[Ciclo] {step}", "Robo")
        self._status_step_label.setText(step)
    
    @Slot(list)
    def _on_cycle_summary(self, steps: list) -> None:
        """Handler para resumo do ciclo completo — exibe sumário formatado."""
        if not steps:
            return
        
        cycle_num = self._robot_controller.cycle_count
        
        # Calcula duração total
        if len(steps) >= 2:
            t0 = steps[0]["timestamp"]
            t1 = steps[-1]["timestamp"]
            duration = (t1 - t0).total_seconds()
        else:
            duration = 0.0
        
        self._event_console.add_success(
            f"===== CICLO #{cycle_num} COMPLETO ({duration:.1f}s) =====",
            "Ciclo"
        )
        for i, s in enumerate(steps, 1):
            ts = s["timestamp"].strftime("%H:%M:%S")
            self._event_console.add_info(
                f"  {i}. [{ts}] {s['step']}",
                "Ciclo"
            )
        self._event_console.add_success(
            f"{'=' * 45}",
            "Ciclo"
        )
        
        # Em modo manual, informa que aguarda autorização
        if self._robot_controller.cycle_mode == "manual":
            self._event_console.add_warning(
                "Aguardando operador clicar 'Novo Ciclo' para continuar.",
                "Ciclo"
            )
    
    @Slot(str)
    def _on_cip_error(self, error: str) -> None:
        """Handler para erro CIP (RF-06: último erro na UI)."""
        self._error_count += 1
        self._event_console.add_error(f"Erro CIP: {error}", "CLP")
        self._status_panel.set_last_error(error)
        self._status_panel.set_error_count(self._error_count)
    
    @Slot(str)
    def _on_robot_error(self, error: str) -> None:
        """Handler para erro do robô (RF-06: último erro na UI)."""
        self._error_count += 1
        self._event_console.add_error(f"Erro do robô: {error}", "Robô")
        self._status_panel.set_last_error(error)
        self._status_panel.set_error_count(self._error_count)

# -*- coding: utf-8 -*-
"""
Página de Operação - Aba principal para operação do sistema.
"""

import asyncio
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QComboBox, QLabel, QFileDialog,
    QSplitter, QGroupBox
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QFont, QKeySequence, QShortcut

from config import get_settings
from core.logger import get_logger
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
        
        self._setup_ui()
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
        console_layout.addWidget(self._event_console)
        central_layout.addWidget(console_group, stretch=1)
        
        main_splitter.addWidget(central_widget)
        
        # Painel de status (direita)
        self._status_panel = StatusPanel()
        main_splitter.addWidget(self._status_panel)
        
        # Proporções do splitter
        main_splitter.setSizes([800, 280])
        
        layout.addWidget(main_splitter, stretch=1)
        
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
        
        layout.addWidget(controls_frame)
    
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
        self._robot_controller.cycle_completed.connect(self._on_cycle_completed)
        self._robot_controller.error_occurred.connect(self._on_robot_error)
        
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
        
        self._event_console.add_info("Iniciando sistema...")
        
        # Atualiza fonte de vídeo
        source_type = ["video", "usb", "rtsp", "gige"][self._source_combo.currentIndex()]
        self._settings.streaming.source_type = source_type
        
        # Se for vídeo, verifica se o arquivo existe e pode ser aberto
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
        
        # Atualiza configuração do stream manager antes de iniciar
        # Isso garante que use o caminho atualizado
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
        
        # Inicia stream
        if not self._stream_manager.start():
            self._event_console.add_error("Falha ao iniciar stream")
            return
        
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
        
        # Conecta ao CLP primeiro, depois inicia controlador de robô
        asyncio.create_task(self._connect_plc_and_start_robot())
        
        self._is_running = True
        self._update_ui_state()
        
        self._event_console.add_success("Sistema iniciado")
        self._status_panel.set_system_status("RUNNING")
    
    async def _connect_plc_and_start_robot(self) -> None:
        """Conecta ao CLP e inicia controlador de robô."""
        try:
            # Tenta conectar ao CLP
            connected = await self._cip_client.connect()
            
            if connected:
                self._event_console.add_success("Conectado ao CLP")
            else:
                self._event_console.add_warning("CLP em modo simulado")
            
            # Inicia controlador de robô apenas se conectado (ou simulado)
            if self._cip_client._state.is_connected:
                self._robot_controller.start()
                self._event_console.add_info("Controlador de robô iniciado")
            else:
                self._event_console.add_warning(
                    "Robô não iniciado: CLP não conectado. Sistema funcionará em modo simulado."
                )
                
        except Exception as e:
            self._event_console.add_warning(f"CLP em modo simulado: {e}")
            # Mesmo em modo simulado, tenta iniciar o robô
            if self._cip_client._state.is_connected:
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
        
        Chamado a cada 25 frames para simulação.
        Usa as TAGs definidas: CENTROID_X, CENTROID_Y, CONFIDENCE, etc.
        """
        if self._last_best_detection is None:
            return
        
        if not self._cip_client._state.is_connected:
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
        Envia dados de detecção ao CLP via TAGs.
        
        TAGs utilizadas:
        - PRODUCT_DETECTED: bool
        - CENTROID_X: float
        - CENTROID_Y: float
        - CONFIDENCE: float
        - DETECTION_COUNT: int
        - PROCESSING_TIME: float
        """
        try:
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
            )
            
        except Exception as e:
            self._logger.warning("failed_to_send_detection", error=str(e))
    
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
        
        # Desconecta CLP
        asyncio.create_task(self._cip_client.disconnect())
        
        self._is_running = False
        self._update_ui_state()
        
        self._video_widget.clear()
        
        self._event_console.add_info("Sistema parado")
        self._status_panel.set_system_status("STOPPED")
    
    @Slot()
    def _toggle_pause(self) -> None:
        """Alterna pause."""
        if not self._is_running:
            return
        
        # Toggle stream
        # TODO: Implementar pause
        self._event_console.add_info("Pause não implementado")
    
    def _update_ui_state(self) -> None:
        """Atualiza estado da UI."""
        self._play_btn.setEnabled(not self._is_running)
        self._pause_btn.setEnabled(self._is_running)
        self._stop_btn.setEnabled(self._is_running)
        self._source_combo.setEnabled(not self._is_running)
        # Permite seleção de vídeo mesmo durante execução para trocar vídeo sem parar
        # self._source_path_btn.setEnabled(not self._is_running)
        self._source_path_btn.setEnabled(True)  # Sempre habilitado
        
        self._status_panel.set_stream_running(self._is_running)
        self._status_panel.set_inference_running(self._is_running)
    
    def _on_source_changed(self, index: int) -> None:
        """Handler para mudança de fonte."""
        # Mostra botão de seleção apenas para vídeo
        self._source_path_btn.setVisible(index == 0)
    
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
                # Muda a fonte mantendo o stream ativo
                # O change_source já reinicia automaticamente se estava rodando
                success = self._stream_manager.change_source(
                    source_type="video",
                    video_path=abs_path_str,
                    loop_video=self._settings.streaming.loop_video,
                )
                
                if success:
                    self._event_console.add_success(f"Stream atualizado para: {file_path_obj.name}")
                    self._logger.info("video_changed_during_runtime", path=abs_path_str)
                else:
                    self._event_console.add_error("Falha ao atualizar stream")
            else:
                # Sistema não está rodando, apenas atualiza configuração
                self._stream_manager.change_source(
                    source_type="video",
                    video_path=abs_path_str,
                    loop_video=self._settings.streaming.loop_video,
                )
    
    def _toggle_fullscreen(self) -> None:
        """Alterna fullscreen do vídeo."""
        # TODO: Implementar fullscreen
        pass
    
    def _update_fps(self) -> None:
        """Atualiza FPS no widget de vídeo."""
        if self._stream_manager.is_running:
            fps = self._stream_manager.get_fps()
            self._video_widget.set_fps(fps)
    
    @Slot()
    def _on_stream_started(self) -> None:
        """Handler para stream iniciado."""
        self._event_console.add_info("Stream iniciado", "Stream")
    
    @Slot()
    def _on_stream_stopped(self) -> None:
        """Handler para stream parado."""
        self._event_console.add_info("Stream parado", "Stream")
    
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
            
            self._event_console.add_success(
                f"Detectado: {event.class_name} ({event.confidence:.0%})",
                "Detecção"
            )
            self._status_panel.update_detection(event)
            
            # Processa no controlador de robô
            self._robot_controller.process_detection(event)
    
    @Slot(int)
    def _on_cycle_completed(self, cycle_number: int) -> None:
        """Handler para ciclo completado."""
        self._event_console.add_success(f"Ciclo {cycle_number} completado", "Robô")
        self._status_panel.set_cycle_count(cycle_number)
    
    @Slot(str)
    def _on_cip_error(self, error: str) -> None:
        """Handler para erro CIP."""
        self._event_console.add_error(f"Erro CIP: {error}", "CLP")
    
    @Slot(str)
    def _on_robot_error(self, error: str) -> None:
        """Handler para erro do robô."""
        self._event_console.add_error(f"Erro do robô: {error}", "Robô")

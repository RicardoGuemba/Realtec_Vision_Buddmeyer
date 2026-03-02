# -*- coding: utf-8 -*-
"""
Janela principal do sistema Realtec Vision Buddmeyer v2.0.
"""

import sys
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QStatusBar, QMenuBar, QMenu, QMessageBox,
    QLabel, QFrame, QHBoxLayout
)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QAction, QKeySequence, QFont, QIcon

from config import get_settings
from core.logger import get_logger, setup_logging

logger = get_logger("ui.main")


class MainWindow(QMainWindow):
    """
    Janela principal do sistema Realtec Vision Buddmeyer v2.0.
    
    Contém:
    - Menu bar
    - Tab widget com 3 abas
    - Status bar
    """
    
    def __init__(self):
        super().__init__()
        
        self._settings = get_settings()
        self._stream_manager = None
        self._inference_engine = None
        self._cip_client = None
        
        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._apply_theme()
        self._schedule_model_preload()
        
        logger.info("main_window_initialized")
    
    def _setup_ui(self) -> None:
        """Configura a interface."""
        self.setWindowTitle("Realtec Vision Buddmeyer v2.1.0")
        self.setMinimumSize(1280, 720)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        
        # Placeholders leves — páginas pesadas (torch, etc.) carregadas após exibir janela
        from PySide6.QtWidgets import QLabel
        from PySide6.QtCore import QTimer
        self._placeholder_op = QLabel("Carregando...")
        self._placeholder_op.setAlignment(Qt.AlignCenter)
        self._placeholder_cfg = QLabel("Carregando...")
        self._placeholder_cfg.setAlignment(Qt.AlignCenter)
        self._placeholder_diag = QLabel("Carregando...")
        self._placeholder_diag.setAlignment(Qt.AlignCenter)
        
        self._tabs.addTab(self._placeholder_op, "🎯 Operação")
        self._tabs.addTab(self._placeholder_cfg, "⚙️ Configuração")
        self._tabs.addTab(self._placeholder_diag, "📊 Diagnósticos")
        
        layout.addWidget(self._tabs)
        
        # Carrega páginas reais após a janela ser exibida (evita bloqueio na inicialização)
        QTimer.singleShot(0, self._deferred_load_pages)
    
    def _deferred_load_pages(self) -> None:
        """Carrega páginas pesadas após a janela estar visível (evita 'não responde')."""
        from PySide6.QtWidgets import QApplication
        
        from streaming import StreamManager
        QApplication.processEvents()
        
        from detection import InferenceEngine
        from communication import CIPClient
        QApplication.processEvents()
        
        from .pages.operation_page import OperationPage
        from .pages.configuration_page import ConfigurationPage
        from .pages.diagnostics_page import DiagnosticsPage
        QApplication.processEvents()
        
        self._stream_manager = StreamManager()
        self._inference_engine = InferenceEngine()
        self._cip_client = CIPClient()
        QApplication.processEvents()
        
        self._operation_page = OperationPage()
        self._configuration_page = ConfigurationPage()
        self._diagnostics_page = DiagnosticsPage()
        
        self._tabs.removeTab(2)
        self._tabs.removeTab(1)
        self._tabs.removeTab(0)
        self._tabs.addTab(self._operation_page, "🎯 Operação")
        self._tabs.addTab(self._configuration_page, "⚙️ Configuração")
        self._tabs.addTab(self._diagnostics_page, "📊 Diagnósticos")
        
        self._start_action.triggered.connect(self._operation_page._start_system)
        self._stop_action.triggered.connect(self._operation_page._stop_system)
        
        self._setup_connections()
    
    def _setup_menu(self) -> None:
        """Configura o menu."""
        menubar = self.menuBar()
        
        # Menu Arquivo
        file_menu = menubar.addMenu("&Arquivo")
        
        save_config_action = QAction("Salvar Configurações", self)
        save_config_action.setShortcut(QKeySequence.Save)
        save_config_action.triggered.connect(self._save_config)
        file_menu.addAction(save_config_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Sair", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self._request_exit)
        file_menu.addAction(exit_action)
        
        # Menu Sistema
        system_menu = menubar.addMenu("&Sistema")
        
        self._start_action = QAction("Iniciar Sistema", self)
        self._start_action.setShortcut(QKeySequence("F5"))
        system_menu.addAction(self._start_action)
        
        self._stop_action = QAction("Parar Sistema", self)
        self._stop_action.setShortcut(QKeySequence("F6"))
        system_menu.addAction(self._stop_action)
        
        system_menu.addSeparator()
        
        reload_model_action = QAction("Recarregar Modelo", self)
        reload_model_action.triggered.connect(self._reload_model)
        system_menu.addAction(reload_model_action)
        
        # Menu Ajuda
        help_menu = menubar.addMenu("A&juda")
        
        about_action = QAction("Sobre", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_statusbar(self) -> None:
        """Configura a barra de status."""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        
        # Status do sistema
        self._system_status = QLabel("Sistema: Parado")
        self._system_status.setStyleSheet("color: #6c757d;")
        self._statusbar.addWidget(self._system_status)
        
        # Separador
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setStyleSheet("color: #3d4852;")
        self._statusbar.addWidget(separator1)
        
        # FPS
        self._fps_label = QLabel("FPS: --")
        self._fps_label.setStyleSheet("color: #17a2b8;")
        self._statusbar.addWidget(self._fps_label)
        
        # Separador
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setStyleSheet("color: #3d4852;")
        self._statusbar.addWidget(separator2)
        
        # Status CLP
        self._plc_status = QLabel("CLP: Desconectado")
        self._plc_status.setStyleSheet("color: #6c757d;")
        self._statusbar.addWidget(self._plc_status)
        
        # Espaçador
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy(), spacer.sizePolicy().verticalPolicy())
        self._statusbar.addWidget(spacer, 1)
        
        # Timestamp
        self._timestamp_label = QLabel()
        self._statusbar.addPermanentWidget(self._timestamp_label)
        
        # Timer para atualizar status
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_statusbar)
        self._status_timer.start(500)
    
    def _setup_connections(self) -> None:
        """Configura conexões de sinais."""
        # Stream
        self._stream_manager.stream_started.connect(
            lambda: self._update_system_status("Rodando", "#28a745")
        )
        self._stream_manager.stream_stopped.connect(
            lambda: self._update_system_status("Parado", "#6c757d")
        )
        
        # CLP
        self._cip_client.connected.connect(
            lambda: self._update_plc_status("Conectado", "#28a745")
        )
        self._cip_client.disconnected.connect(
            lambda: self._update_plc_status("Desconectado", "#6c757d")
        )
        self._cip_client.state_changed.connect(self._on_plc_state_changed)
        
        # Pré-carregamento do modelo (página de operação)
        self._operation_page.model_preload_finished.connect(self._on_model_preload_finished)
    
    def _schedule_model_preload(self) -> None:
        """Agenda o pré-carregamento do modelo 2 s após abrir a janela (evita espera ao clicar Iniciar)."""
        QTimer.singleShot(2000, self._trigger_model_preload)
    
    def _trigger_model_preload(self) -> None:
        """Inicia o carregamento do modelo em segundo plano na página de operação."""
        self._statusbar.showMessage("Preparando modelo em segundo plano...", 0)
        self._operation_page.start_model_preload()
    
    @Slot(bool)
    def _on_model_preload_finished(self, success: bool) -> None:
        """Chamado quando o pré-carregamento do modelo termina."""
        if success:
            self._statusbar.showMessage("Modelo pronto para uso.", 5000)
        else:
            self._statusbar.showMessage("Modelo será carregado ao clicar em Iniciar.", 5000)
    
    def _apply_theme(self) -> None:
        """Aplica tema industrial."""
        theme_path = Path(__file__).parent / "styles" / "industrial.qss"
        
        if theme_path.exists():
            with open(theme_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        else:
            # Tema inline se arquivo não existir
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #0f1419;
                }
                QWidget {
                    background-color: #0f1419;
                    color: #e0e0e0;
                    font-family: "Segoe UI", Arial, sans-serif;
                }
                QTabWidget::pane {
                    border: 1px solid #2d3748;
                    background-color: #1a1a2e;
                }
                QTabBar::tab {
                    background-color: #1e2836;
                    color: #adb5bd;
                    padding: 10px 20px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #1a1a2e;
                    color: #00d4ff;
                    font-weight: bold;
                }
                QTabBar::tab:hover:!selected {
                    background-color: #2d3748;
                }
                QMenuBar {
                    background-color: #1e2836;
                    color: #e0e0e0;
                    padding: 4px;
                }
                QMenuBar::item:selected {
                    background-color: #2d3748;
                }
                QMenu {
                    background-color: #1e2836;
                    color: #e0e0e0;
                    border: 1px solid #3d4852;
                }
                QMenu::item:selected {
                    background-color: #00d4ff;
                    color: #000;
                }
                QStatusBar {
                    background-color: #1e2836;
                    color: #adb5bd;
                    border-top: 1px solid #2d3748;
                }
                QPushButton {
                    background-color: #2d3748;
                    color: #e0e0e0;
                    border: 1px solid #3d4852;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #3d4852;
                }
                QPushButton:pressed {
                    background-color: #4a5568;
                }
                QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                    background-color: #1e2836;
                    color: #e0e0e0;
                    border: 1px solid #3d4852;
                    padding: 6px;
                    border-radius: 4px;
                }
                QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                    border-color: #00d4ff;
                }
                QGroupBox {
                    color: #e0e0e0;
                    border: 1px solid #3d4852;
                    border-radius: 4px;
                    margin-top: 12px;
                    padding-top: 12px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
                QScrollBar:vertical {
                    background-color: #1e2836;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #3d4852;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #4a5568;
                }
                QSlider::groove:horizontal {
                    background: #2d3748;
                    height: 6px;
                    border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    background: #00d4ff;
                    width: 16px;
                    height: 16px;
                    margin: -5px 0;
                    border-radius: 8px;
                }
                QCheckBox {
                    color: #e0e0e0;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 4px;
                    border: 1px solid #3d4852;
                    background-color: #1e2836;
                }
                QCheckBox::indicator:checked {
                    background-color: #00d4ff;
                    border-color: #00d4ff;
                }
            """)
    
    def _update_statusbar(self) -> None:
        """Atualiza a barra de status."""
        if self._stream_manager is None:
            return
        # FPS
        if self._stream_manager.is_running:
            fps = self._stream_manager.get_fps()
            self._fps_label.setText(f"FPS: {fps:.1f}")
        else:
            self._fps_label.setText("FPS: --")
        
        # Timestamp
        self._timestamp_label.setText(datetime.now().strftime("%H:%M:%S"))
    
    def _update_system_status(self, status: str, color: str) -> None:
        """Atualiza status do sistema."""
        self._system_status.setText(f"Sistema: {status}")
        self._system_status.setStyleSheet(f"color: {color};")
    
    def _update_plc_status(self, status: str, color: str) -> None:
        """Atualiza status do CLP."""
        self._plc_status.setText(f"CLP: {status}")
        self._plc_status.setStyleSheet(f"color: {color};")
    
    @Slot(object)
    def _on_plc_state_changed(self, state) -> None:
        """Handler para mudança de estado do CLP."""
        status = state.status.value.capitalize()
        
        if state.is_connected:
            if state.is_simulated:
                self._update_plc_status("Simulado", "#17a2b8")
            else:
                self._update_plc_status("Conectado", "#28a745")
        else:
            self._update_plc_status(status, "#dc3545")
    
    def _save_config(self) -> None:
        """Salva configurações."""
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        self._settings.to_yaml(config_path)
        self._statusbar.showMessage("Configurações salvas!", 3000)
    
    def _reload_model(self) -> None:
        """Recarrega o modelo de detecção."""
        if self._inference_engine is None:
            return
        if self._inference_engine.is_running:
            QMessageBox.warning(
                self,
                "Aviso",
                "Pare o sistema antes de recarregar o modelo."
            )
            return
        
        self._statusbar.showMessage("Recarregando modelo...", 3000)
        
        if self._inference_engine.load_model():
            self._statusbar.showMessage("Modelo recarregado com sucesso!", 3000)
        else:
            QMessageBox.critical(
                self,
                "Erro",
                "Falha ao recarregar modelo."
            )
    
    def _show_about(self) -> None:
        """Mostra diálogo sobre."""
        QMessageBox.about(
            self,
            "Sobre Realtec Vision Buddmeyer",
            """
            <h2>Realtec Vision Buddmeyer v2.1.0</h2>
            <p>Sistema de visão computacional para automação de expedição.</p>
            <p><b>Tecnologias:</b></p>
            <ul>
                <li>PySide6 (Qt for Python)</li>
                <li>PyTorch + RT-DETR</li>
                <li>OpenCV</li>
                <li>aphyt (CIP/EtherNet-IP)</li>
            </ul>
            <p><b>Plataforma:</b> Windows 10/11</p>
            <p>© 2025 Sistema de Automação Industrial</p>
            """
        )
    
    def _request_exit(self) -> None:
        """Solicita saída, parando todos os processos antes de fechar."""
        self._force_shutdown()
        self.close()

    def _force_shutdown(self) -> None:
        """Para todos os processos (stream, inferência, CLP, robô, MJPEG)."""
        if self._stream_manager is None:
            return
        if hasattr(self, "_operation_page"):
            try:
                self._operation_page._stop_system()
            except Exception as e:
                logger.warning("shutdown_stop_system_error", error=str(e))

    def closeEvent(self, event) -> None:
        """Evento de fechamento — para todos os processos antes de sair."""
        if self._stream_manager is None:
            event.accept()
            logger.info("application_closed")
            return
        if self._stream_manager.is_running:
            reply = QMessageBox.question(
                self,
                "Confirmar Saída",
                "O sistema está em execução. Deseja parar e sair?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
        self._force_shutdown()
        event.accept()
        logger.info("application_closed")

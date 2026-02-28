# -*- coding: utf-8 -*-
"""
Classe principal singleton da aplicação.
"""

import asyncio
from threading import Lock
from typing import Optional, Dict, Any

from PySide6.QtCore import QObject, Signal

from config import get_settings
from core.logger import get_logger
from core.metrics import MetricsCollector
from streaming import StreamManager
from detection import InferenceEngine
from communication import CIPClient
from control import RobotController

logger = get_logger("app")


class Application(QObject):
    """
    Classe principal singleton que gerencia todos os componentes.
    
    Signals:
        started: Emitido quando aplicação inicia
        stopped: Emitido quando aplicação para
        error: Emitido em caso de erro
    """
    
    started = Signal()
    stopped = Signal()
    error = Signal(str)
    
    _instance: Optional["Application"] = None
    _lock = Lock()
    
    def __new__(cls) -> "Application":
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        
        super().__init__()
        self._initialized = True
        
        self._settings = get_settings()
        self._metrics = MetricsCollector()
        
        # Componentes
        self._stream_manager = StreamManager()
        self._inference_engine = InferenceEngine()
        self._cip_client = CIPClient()
        self._robot_controller = RobotController()
        
        self._is_running = False
        
        # Conecta sinais
        self._connect_signals()
    
    def _connect_signals(self) -> None:
        """Conecta sinais entre componentes."""
        # Stream → Inferência
        self._stream_manager.frame_info_available.connect(
            lambda info: self._inference_engine.process_frame(info.frame, info.frame_id)
        )
        
        # Inferência → Robô
        self._inference_engine.detection_event.connect(
            self._robot_controller.process_detection
        )
    
    async def start(self) -> bool:
        """
        Inicia todos os componentes.
        
        Returns:
            True se iniciado com sucesso
        """
        if self._is_running:
            logger.warning("application_already_running")
            return True
        
        logger.info("application_starting")
        
        try:
            # Carrega modelo
            if not self._inference_engine.is_model_loaded:
                if not self._inference_engine.load_model():
                    raise RuntimeError("Falha ao carregar modelo")
            
            # Conecta ao CLP
            await self._cip_client.connect()
            
            # Inicia stream
            if not self._stream_manager.start():
                raise RuntimeError("Falha ao iniciar stream")
            
            # Inicia inferência
            if not self._inference_engine.start():
                raise RuntimeError("Falha ao iniciar inferência")
            
            # Inicia controlador de robô
            self._robot_controller.start()
            
            self._is_running = True
            self.started.emit()
            
            logger.info("application_started")
            return True
            
        except Exception as e:
            logger.error("application_start_failed", error=str(e))
            self.error.emit(str(e))
            await self.stop()
            return False
    
    async def stop(self) -> None:
        """Para todos os componentes."""
        if not self._is_running:
            return
        
        logger.info("application_stopping")
        
        # Para componentes na ordem inversa
        self._robot_controller.stop()
        self._inference_engine.stop()
        self._stream_manager.stop()
        await self._cip_client.disconnect()
        
        self._is_running = False
        self.stopped.emit()
        
        logger.info("application_stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status de todos os componentes."""
        return {
            "running": self._is_running,
            "stream": self._stream_manager.get_status(),
            "inference": self._inference_engine.get_status(),
            "cip": self._cip_client.get_status(),
            "robot": self._robot_controller.get_status(),
            "metrics": self._metrics.get_all_metrics(),
        }
    
    @property
    def is_running(self) -> bool:
        """Verifica se está rodando."""
        return self._is_running
    
    @property
    def stream_manager(self) -> StreamManager:
        """Retorna gerenciador de stream."""
        return self._stream_manager
    
    @property
    def inference_engine(self) -> InferenceEngine:
        """Retorna engine de inferência."""
        return self._inference_engine
    
    @property
    def cip_client(self) -> CIPClient:
        """Retorna cliente CIP."""
        return self._cip_client
    
    @property
    def robot_controller(self) -> RobotController:
        """Retorna controlador de robô."""
        return self._robot_controller


# Função de conveniência
def get_application() -> Application:
    """Retorna a instância da aplicação."""
    return Application()

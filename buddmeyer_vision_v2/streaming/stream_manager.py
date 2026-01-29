# -*- coding: utf-8 -*-
"""
Gerenciador principal de streaming de vídeo.
"""

import time
from pathlib import Path
from threading import Lock
from typing import Optional, Dict, Any

import numpy as np
from PySide6.QtCore import QObject, Signal, QThread, QMutex, QWaitCondition

from config import get_settings
from core.logger import get_logger
from core.metrics import MetricsCollector
from core.exceptions import StreamError

from .source_adapters import BaseSourceAdapter, SourceType, create_adapter
from .frame_buffer import FrameBuffer, FrameInfo
from .stream_health import StreamHealth, HealthStatus

logger = get_logger("streaming.manager")


class StreamWorker(QThread):
    """
    Thread de captura de frames.
    
    Signals:
        frame_captured: Emitido quando um frame é capturado
        error_occurred: Emitido em caso de erro
    """
    
    frame_captured = Signal(object)  # FrameInfo
    error_occurred = Signal(str)
    
    def __init__(self, adapter: BaseSourceAdapter, target_fps: float = 30.0):
        super().__init__()
        
        self._adapter = adapter
        self._target_fps = target_fps
        self._running = False
        self._paused = False
        self._mutex = QMutex()
        self._pause_condition = QWaitCondition()
    
    def run(self) -> None:
        """Loop principal de captura."""
        self._running = True
        frame_interval = 1.0 / self._target_fps if self._target_fps > 0 else 0.033
        
        logger.info("stream_worker_started", target_fps=self._target_fps)
        
        while self._running:
            # Verifica pause
            self._mutex.lock()
            while self._paused and self._running:
                self._pause_condition.wait(self._mutex)
            self._mutex.unlock()
            
            if not self._running:
                break
            
            start_time = time.perf_counter()
            
            try:
                frame_info = self._adapter.read()
                
                if frame_info is not None:
                    self.frame_captured.emit(frame_info)
                else:
                    logger.warning("stream_read_none")
                    time.sleep(0.1)
                    continue
                    
            except Exception as e:
                logger.error("stream_read_error", error=str(e))
                self.error_occurred.emit(str(e))
                time.sleep(0.5)
                continue
            
            # Controle de FPS
            elapsed = time.perf_counter() - start_time
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        logger.info("stream_worker_stopped")
    
    def pause(self) -> None:
        """Pausa a captura."""
        self._mutex.lock()
        self._paused = True
        self._mutex.unlock()
    
    def resume(self) -> None:
        """Retoma a captura."""
        self._mutex.lock()
        self._paused = False
        self._pause_condition.wakeAll()
        self._mutex.unlock()
    
    def stop(self) -> None:
        """Para a captura."""
        self._running = False
        self._mutex.lock()
        self._paused = False
        self._pause_condition.wakeAll()
        self._mutex.unlock()
        self.wait()


class StreamManager(QObject):
    """
    Gerenciador central de streaming de vídeo.
    
    Singleton que gerencia:
    - Adaptador de fonte de vídeo
    - Thread de captura
    - Buffer de frames
    - Health check
    
    Signals:
        frame_available: Emitido quando um novo frame está disponível
        stream_started: Emitido quando o stream inicia
        stream_stopped: Emitido quando o stream para
        stream_error: Emitido em caso de erro
        health_changed: Emitido quando status de saúde muda
    """
    
    frame_available = Signal(np.ndarray)
    frame_info_available = Signal(object)  # FrameInfo
    stream_started = Signal()
    stream_stopped = Signal()
    stream_error = Signal(str)
    health_changed = Signal(object)  # StreamHealthInfo
    
    _instance: Optional["StreamManager"] = None
    _lock = Lock()
    
    def __new__(cls) -> "StreamManager":
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
        self._adapter: Optional[BaseSourceAdapter] = None
        self._worker: Optional[StreamWorker] = None
        self._buffer: FrameBuffer = FrameBuffer(
            max_size=self._settings.streaming.max_frame_buffer_size
        )
        self._health = StreamHealth()
        self._metrics = MetricsCollector()
        
        self._is_running = False
        self._current_frame: Optional[FrameInfo] = None
        
        # Conecta sinais de health
        self._health.health_changed.connect(self.health_changed.emit)
    
    def start(self) -> bool:
        """
        Inicia o streaming.
        
        Returns:
            True se iniciado com sucesso
        """
        if self._is_running:
            logger.warning("stream_already_running")
            return True
        
        try:
            # Recarrega configurações para garantir que está atualizado
            # Força reload para pegar mudanças feitas na UI
            self._settings = get_settings(reload=True)
            
            # Cria adaptador
            settings = self._settings.streaming
            
            # Valida e normaliza caminho do vídeo se for arquivo
            if settings.source_type == "video":
                video_path_str = settings.video_path
                video_path_obj = Path(video_path_str)
                
                # Tenta resolver caminho relativo
                if not video_path_obj.is_absolute():
                    base_path = Path(__file__).parent.parent
                    video_path_obj = base_path / video_path_str
                
                # Normaliza caminho (resolve .., ./, etc)
                try:
                    video_path_obj = video_path_obj.resolve()
                except Exception:
                    pass
                
                if not video_path_obj.exists():
                    error_msg = f"Arquivo de vídeo não encontrado: {video_path_obj}"
                    logger.error("video_file_not_found", path=str(video_path_obj))
                    self.stream_error.emit(error_msg)
                    return False
                
                # Atualiza configuração com caminho normalizado
                settings.video_path = str(video_path_obj)
                logger.info("using_video_path", path=str(video_path_obj))
            
            self._adapter = create_adapter(
                source_type=settings.source_type,
                video_path=settings.video_path,
                camera_index=settings.usb_camera_index,
                rtsp_url=settings.rtsp_url,
                gige_ip=settings.gige_ip,
                gige_port=settings.gige_port,
                loop_video=settings.loop_video,
            )
            
            # Abre fonte
            self._adapter.open()
            
            # Obtém FPS da fonte
            props = self._adapter.get_properties()
            target_fps = props.get("fps", 30.0)
            if target_fps <= 0:
                target_fps = 30.0
            
            # Cria worker
            self._worker = StreamWorker(self._adapter, target_fps)
            self._worker.frame_captured.connect(self._on_frame_captured)
            self._worker.error_occurred.connect(self._on_error)
            
            # Inicia
            self._worker.start()
            self._is_running = True
            self._health.reset()
            
            logger.info(
                "stream_started",
                source_type=settings.source_type,
                target_fps=target_fps,
            )
            
            self.stream_started.emit()
            return True
            
        except Exception as e:
            logger.error("stream_start_failed", error=str(e))
            self.stream_error.emit(str(e))
            return False
    
    def stop(self) -> None:
        """Para o streaming."""
        if not self._is_running:
            return
        
        # Para worker
        if self._worker is not None:
            self._worker.stop()
            self._worker.deleteLater()
            self._worker = None
        
        # Fecha adaptador
        if self._adapter is not None:
            self._adapter.close()
            self._adapter = None
        
        # Limpa buffer
        self._buffer.clear()
        
        self._is_running = False
        self._current_frame = None
        
        logger.info("stream_stopped")
        self.stream_stopped.emit()
    
    def pause(self) -> None:
        """Pausa o streaming."""
        if self._worker is not None:
            self._worker.pause()
            logger.info("stream_paused")
    
    def resume(self) -> None:
        """Retoma o streaming."""
        if self._worker is not None:
            self._worker.resume()
            logger.info("stream_resumed")
    
    def change_source(
        self,
        source_type: str,
        video_path: str = "",
        camera_index: int = 0,
        rtsp_url: str = "",
        gige_ip: str = "",
        gige_port: int = 3956,
        loop_video: bool = True,
        **kwargs
    ) -> bool:
        """
        Muda a fonte de vídeo.
        
        Args:
            source_type: Tipo de fonte
            video_path: Caminho do vídeo
            camera_index: Índice da câmera
            rtsp_url: URL RTSP
            gige_ip: IP GigE
            gige_port: Porta GigE
            loop_video: Loop do vídeo
        
        Returns:
            True se mudou com sucesso
        """
        was_running = self._is_running
        
        # Para stream atual apenas se estava rodando
        if was_running:
            # Para worker e fecha adaptador atual
            if self._worker is not None:
                self._worker.stop()
                self._worker.wait(5000)  # Aguarda thread terminar
                self._worker.deleteLater()
                self._worker = None
            
            if self._adapter is not None:
                self._adapter.close()
                self._adapter = None
            
            self._is_running = False
        
        # Usa as configurações atuais (NÃO recarrega do arquivo para não perder mudanças)
        # self._settings = get_settings()  # Removido para preservar mudanças em memória
        
        # Atualiza configuração em memória
        settings = self._settings.streaming
        settings.source_type = source_type
        
        if video_path:
            settings.video_path = video_path
        if camera_index >= 0:
            settings.usb_camera_index = camera_index
        if rtsp_url:
            settings.rtsp_url = rtsp_url
        if gige_ip:
            settings.gige_ip = gige_ip
        if gige_port > 0:
            settings.gige_port = gige_port
        if loop_video is not None:
            settings.loop_video = loop_video
        
        logger.info(
            "source_changed",
            source_type=source_type,
            video_path=video_path if video_path else None,
        )
        
        # Reinicia se estava rodando
        if was_running:
            return self._start_with_current_settings()
        
        return True
    
    def _start_with_current_settings(self) -> bool:
        """
        Inicia stream usando as configurações atuais em memória.
        Usado internamente pelo change_source para não recarregar do arquivo.
        
        Returns:
            True se iniciado com sucesso
        """
        if self._is_running:
            logger.warning("stream_already_running")
            return True
        
        try:
            # Usa configurações atuais em memória (NÃO recarrega do arquivo)
            settings = self._settings.streaming
            
            # Valida e normaliza caminho do vídeo se for arquivo
            if settings.source_type == "video":
                video_path_str = settings.video_path
                video_path_obj = Path(video_path_str)
                
                # Tenta resolver caminho relativo
                if not video_path_obj.is_absolute():
                    base_path = Path(__file__).parent.parent
                    video_path_obj = base_path / video_path_str
                
                # Normaliza caminho (resolve .., ./, etc)
                try:
                    video_path_obj = video_path_obj.resolve()
                except Exception:
                    pass
                
                if not video_path_obj.exists():
                    error_msg = f"Arquivo de vídeo não encontrado: {video_path_obj}"
                    logger.error("video_file_not_found", path=str(video_path_obj))
                    self.stream_error.emit(error_msg)
                    return False
                
                # Atualiza configuração com caminho normalizado
                settings.video_path = str(video_path_obj)
                logger.info("using_video_path", path=str(video_path_obj))
            
            self._adapter = create_adapter(
                source_type=settings.source_type,
                video_path=settings.video_path,
                camera_index=settings.usb_camera_index,
                rtsp_url=settings.rtsp_url,
                gige_ip=settings.gige_ip,
                gige_port=settings.gige_port,
                loop_video=settings.loop_video,
            )
            
            # Abre fonte
            self._adapter.open()
            
            # Obtém FPS da fonte
            props = self._adapter.get_properties()
            target_fps = props.get("fps", 30.0)
            if target_fps <= 0:
                target_fps = 30.0
            
            # Cria worker
            self._worker = StreamWorker(self._adapter, target_fps)
            self._worker.frame_captured.connect(self._on_frame_captured)
            self._worker.error_occurred.connect(self._on_error)
            
            # Inicia
            self._worker.start()
            self._is_running = True
            self._health.reset()
            
            logger.info(
                "stream_restarted_with_new_source",
                source_type=settings.source_type,
                video_path=settings.video_path if settings.source_type == "video" else None,
                target_fps=target_fps,
            )
            
            self.stream_started.emit()
            return True
            
        except Exception as e:
            logger.error("stream_restart_failed", error=str(e))
            self.stream_error.emit(str(e))
            return False
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        Retorna o frame atual.
        
        Returns:
            Frame numpy ou None
        """
        if self._current_frame is not None:
            return self._current_frame.frame.copy()
        return None
    
    def get_current_frame_info(self) -> Optional[FrameInfo]:
        """Retorna informações do frame atual."""
        return self._current_frame
    
    def get_fps(self) -> float:
        """Retorna FPS atual."""
        return self._health.current_fps
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna status do stream.
        
        Returns:
            Dict com status completo
        """
        health = self._health.check_health()
        
        return {
            "running": self._is_running,
            "source_type": self._settings.streaming.source_type,
            "fps": self._health.current_fps,
            "frame_count": self._health.frame_count,
            "drop_count": self._health.drop_count,
            "buffer_size": self._buffer.size,
            "buffer_usage": self._buffer.usage_percent,
            "health": health.to_dict(),
        }
    
    @property
    def is_running(self) -> bool:
        """Verifica se está rodando."""
        return self._is_running
    
    def _on_frame_captured(self, frame_info: FrameInfo) -> None:
        """Handler para frame capturado."""
        # Atualiza frame atual
        self._current_frame = frame_info
        
        # Adiciona ao buffer
        self._buffer.put(frame_info)
        
        # Atualiza health
        self._health.record_frame()
        self._health.set_buffer_usage(self._buffer.usage_percent)
        
        # Métricas
        self._metrics.record("stream_fps", self._health.current_fps)
        
        # Emite sinais
        self.frame_available.emit(frame_info.frame)
        self.frame_info_available.emit(frame_info)
    
    def _on_error(self, error: str) -> None:
        """Handler para erro."""
        logger.error("stream_error", error=error)
        self._health.record_drop()
        self.stream_error.emit(error)


# Função de conveniência
def get_stream_manager() -> StreamManager:
    """Retorna a instância do gerenciador de stream."""
    return StreamManager()

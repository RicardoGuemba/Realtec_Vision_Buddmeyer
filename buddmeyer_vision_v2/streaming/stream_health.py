# -*- coding: utf-8 -*-
"""
Health check para streaming de vídeo.
"""

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from PySide6.QtCore import QObject, Signal

from core.logger import get_logger

logger = get_logger("streaming.health")


class HealthStatus(str, Enum):
    """Status de saúde do stream."""
    
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class StreamHealthInfo:
    """Informações de saúde do stream."""
    
    status: HealthStatus
    fps: float
    expected_fps: float
    frame_drops: int
    last_frame_time: Optional[datetime]
    latency_ms: float
    buffer_usage: float
    message: str
    
    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY
    
    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "fps": self.fps,
            "expected_fps": self.expected_fps,
            "frame_drops": self.frame_drops,
            "last_frame_time": self.last_frame_time.isoformat() if self.last_frame_time else None,
            "latency_ms": self.latency_ms,
            "buffer_usage": self.buffer_usage,
            "message": self.message,
        }


class StreamHealth(QObject):
    """
    Monitoramento de saúde do stream.
    
    Signals:
        health_changed: Emitido quando status de saúde muda
    """
    
    health_changed = Signal(object)  # StreamHealthInfo
    
    def __init__(
        self,
        expected_fps: float = 30.0,
        fps_threshold: float = 0.5,  # % do esperado
        frame_timeout: float = 5.0,  # segundos sem frame
        max_drops: int = 30,  # máximo de drops antes de degraded
    ):
        super().__init__()
        
        self.expected_fps = expected_fps
        self.fps_threshold = fps_threshold
        self.frame_timeout = frame_timeout
        self.max_drops = max_drops
        
        self._fps_history: list = []
        self._frame_count = 0
        self._drop_count = 0
        self._last_frame_time: Optional[datetime] = None
        self._last_check_time: Optional[float] = None
        self._last_status = HealthStatus.UNKNOWN
        self._buffer_usage = 0.0
    
    def record_frame(self, latency_ms: float = 0.0) -> None:
        """
        Registra recebimento de um frame.
        
        Args:
            latency_ms: Latência de captura em ms
        """
        now = datetime.now()
        self._frame_count += 1
        self._last_frame_time = now
        
        # Calcula FPS instantâneo
        if self._last_check_time is not None:
            elapsed = time.time() - self._last_check_time
            if elapsed > 0:
                instant_fps = 1.0 / elapsed
                self._fps_history.append(instant_fps)
                # Mantém apenas últimos 30 valores
                if len(self._fps_history) > 30:
                    self._fps_history.pop(0)
        
        self._last_check_time = time.time()
    
    def record_drop(self) -> None:
        """Registra um frame dropado."""
        self._drop_count += 1
    
    def set_buffer_usage(self, usage: float) -> None:
        """Define uso do buffer (0-100)."""
        self._buffer_usage = usage
    
    def check_health(self) -> StreamHealthInfo:
        """
        Verifica saúde do stream.
        
        Returns:
            StreamHealthInfo com status atual
        """
        now = datetime.now()
        
        # Calcula FPS médio
        current_fps = 0.0
        if self._fps_history:
            current_fps = sum(self._fps_history) / len(self._fps_history)
        
        # Calcula latência estimada
        latency_ms = 0.0
        if self._last_check_time:
            latency_ms = (time.time() - self._last_check_time) * 1000
        
        # Verifica timeout de frame
        if self._last_frame_time is None:
            status = HealthStatus.UNKNOWN
            message = "Aguardando primeiro frame"
        elif (now - self._last_frame_time) > timedelta(seconds=self.frame_timeout):
            status = HealthStatus.UNHEALTHY
            message = f"Sem frames há {(now - self._last_frame_time).seconds}s"
        elif current_fps < (self.expected_fps * self.fps_threshold):
            status = HealthStatus.DEGRADED
            message = f"FPS baixo: {current_fps:.1f} (esperado: {self.expected_fps})"
        elif self._drop_count > self.max_drops:
            status = HealthStatus.DEGRADED
            message = f"Alto número de drops: {self._drop_count}"
        else:
            status = HealthStatus.HEALTHY
            message = "Stream funcionando normalmente"
        
        # Emite sinal se status mudou
        if status != self._last_status:
            self._last_status = status
            logger.info(
                "stream_health_changed",
                status=status.value,
                fps=current_fps,
                drops=self._drop_count,
            )
        
        info = StreamHealthInfo(
            status=status,
            fps=current_fps,
            expected_fps=self.expected_fps,
            frame_drops=self._drop_count,
            last_frame_time=self._last_frame_time,
            latency_ms=latency_ms,
            buffer_usage=self._buffer_usage,
            message=message,
        )
        
        self.health_changed.emit(info)
        return info
    
    def reset(self) -> None:
        """Reseta estatísticas de saúde."""
        self._fps_history.clear()
        self._frame_count = 0
        self._drop_count = 0
        self._last_frame_time = None
        self._last_check_time = None
        self._last_status = HealthStatus.UNKNOWN
        self._buffer_usage = 0.0
    
    @property
    def current_fps(self) -> float:
        """Retorna FPS atual."""
        if not self._fps_history:
            return 0.0
        return sum(self._fps_history) / len(self._fps_history)
    
    @property
    def frame_count(self) -> int:
        """Retorna total de frames recebidos."""
        return self._frame_count
    
    @property
    def drop_count(self) -> int:
        """Retorna total de frames dropados."""
        return self._drop_count

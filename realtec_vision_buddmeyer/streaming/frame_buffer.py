# -*- coding: utf-8 -*-
"""
Buffer de frames thread-safe para streaming de vídeo.
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from threading import Lock, Event
from typing import Optional, Deque

import numpy as np


@dataclass
class FrameInfo:
    """Informações de um frame capturado."""
    
    frame: np.ndarray
    frame_id: int
    timestamp: datetime
    source_type: str
    width: int
    height: int
    channels: int
    
    @classmethod
    def from_frame(
        cls,
        frame: np.ndarray,
        frame_id: int,
        source_type: str,
    ) -> "FrameInfo":
        """Cria FrameInfo a partir de um frame numpy."""
        h, w = frame.shape[:2]
        channels = frame.shape[2] if len(frame.shape) > 2 else 1
        
        return cls(
            frame=frame,
            frame_id=frame_id,
            timestamp=datetime.now(),
            source_type=source_type,
            width=w,
            height=h,
            channels=channels,
        )
    
    @property
    def shape(self) -> tuple:
        """Retorna shape do frame."""
        return self.frame.shape
    
    @property
    def size_bytes(self) -> int:
        """Retorna tamanho em bytes."""
        return self.frame.nbytes


class FrameBuffer:
    """
    Buffer circular thread-safe para frames de vídeo.
    
    Características:
    - Thread-safe (Lock)
    - Tamanho máximo configurável
    - Suporte a espera por novo frame (Event)
    - Estatísticas de uso
    """
    
    def __init__(self, max_size: int = 30):
        """
        Inicializa o buffer.
        
        Args:
            max_size: Tamanho máximo do buffer
        """
        self._max_size = max_size
        self._buffer: Deque[FrameInfo] = deque(maxlen=max_size)
        self._lock = Lock()
        self._new_frame_event = Event()
        self._frame_count = 0
        self._dropped_count = 0
    
    def put(self, frame_info: FrameInfo) -> bool:
        """
        Adiciona um frame ao buffer.
        
        Args:
            frame_info: Informações do frame
        
        Returns:
            True se adicionado com sucesso
        """
        with self._lock:
            # Verifica se vai dropar frame
            if len(self._buffer) >= self._max_size:
                self._dropped_count += 1
            
            self._buffer.append(frame_info)
            self._frame_count += 1
        
        # Sinaliza novo frame disponível
        self._new_frame_event.set()
        
        return True
    
    def get(self, timeout: float = None) -> Optional[FrameInfo]:
        """
        Obtém o frame mais recente do buffer.
        
        Args:
            timeout: Timeout em segundos para aguardar
        
        Returns:
            FrameInfo ou None se buffer vazio/timeout
        """
        # Aguarda novo frame se timeout especificado
        if timeout is not None:
            self._new_frame_event.wait(timeout)
            self._new_frame_event.clear()
        
        with self._lock:
            if not self._buffer:
                return None
            
            return self._buffer[-1]  # Retorna mais recente
    
    def get_and_remove(self, timeout: float = None) -> Optional[FrameInfo]:
        """
        Obtém e remove o frame mais antigo do buffer (FIFO).
        
        Args:
            timeout: Timeout em segundos para aguardar
        
        Returns:
            FrameInfo ou None se buffer vazio/timeout
        """
        if timeout is not None:
            if not self._new_frame_event.wait(timeout):
                return None
            self._new_frame_event.clear()
        
        with self._lock:
            if not self._buffer:
                return None
            
            return self._buffer.popleft()
    
    def peek(self) -> Optional[FrameInfo]:
        """
        Espia o frame mais recente sem remover.
        
        Returns:
            FrameInfo ou None se buffer vazio
        """
        with self._lock:
            if not self._buffer:
                return None
            return self._buffer[-1]
    
    def clear(self) -> int:
        """
        Limpa o buffer.
        
        Returns:
            Número de frames removidos
        """
        with self._lock:
            count = len(self._buffer)
            self._buffer.clear()
            self._new_frame_event.clear()
            return count
    
    @property
    def size(self) -> int:
        """Retorna número atual de frames no buffer."""
        with self._lock:
            return len(self._buffer)
    
    @property
    def max_size(self) -> int:
        """Retorna tamanho máximo do buffer."""
        return self._max_size
    
    @property
    def is_empty(self) -> bool:
        """Verifica se buffer está vazio."""
        with self._lock:
            return len(self._buffer) == 0
    
    @property
    def is_full(self) -> bool:
        """Verifica se buffer está cheio."""
        with self._lock:
            return len(self._buffer) >= self._max_size
    
    @property
    def frame_count(self) -> int:
        """Retorna total de frames processados."""
        return self._frame_count
    
    @property
    def dropped_count(self) -> int:
        """Retorna total de frames dropados."""
        return self._dropped_count
    
    @property
    def usage_percent(self) -> float:
        """Retorna porcentagem de uso do buffer."""
        with self._lock:
            return (len(self._buffer) / self._max_size) * 100
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do buffer."""
        with self._lock:
            return {
                "size": len(self._buffer),
                "max_size": self._max_size,
                "frame_count": self._frame_count,
                "dropped_count": self._dropped_count,
                "usage_percent": (len(self._buffer) / self._max_size) * 100,
            }

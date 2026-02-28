# -*- coding: utf-8 -*-
"""
Adaptadores de fonte de vídeo para diferentes tipos de entrada.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any
import time

import cv2
import numpy as np

from core.logger import get_logger
from core.exceptions import StreamSourceError
from .frame_buffer import FrameInfo

logger = get_logger("streaming.adapters")


class SourceType(str, Enum):
    """Tipos de fonte de vídeo suportados — apenas câmeras reais."""

    USB = "usb"       # Câmera USB/USB-C
    GIGE = "gige"     # Câmera GigE (Gigabit Ethernet)


class BaseSourceAdapter(ABC):
    """
    Interface base para adaptadores de fonte de vídeo.
    """
    
    def __init__(self, source_type: SourceType):
        self.source_type = source_type
        self._capture: Optional[cv2.VideoCapture] = None
        self._is_open = False
        self._frame_count = 0
        self._start_time: Optional[float] = None
    
    @abstractmethod
    def open(self) -> bool:
        """
        Abre a fonte de vídeo.
        
        Returns:
            True se aberto com sucesso
        """
        pass
    
    @abstractmethod
    def read(self) -> Optional[FrameInfo]:
        """
        Lê um frame da fonte.
        
        Returns:
            FrameInfo ou None se falhar
        """
        pass
    
    def close(self) -> None:
        """Fecha a fonte de vídeo."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._is_open = False
        logger.info("source_closed", source_type=self.source_type.value)
    
    def get_properties(self) -> Dict[str, Any]:
        """Retorna propriedades da fonte."""
        if self._capture is None:
            return {}
        
        return {
            "width": int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": self._capture.get(cv2.CAP_PROP_FPS),
            "frame_count": int(self._capture.get(cv2.CAP_PROP_FRAME_COUNT)),
            "fourcc": int(self._capture.get(cv2.CAP_PROP_FOURCC)),
        }
    
    def get_fps(self) -> float:
        """Retorna FPS real de captura."""
        if self._start_time is None or self._frame_count == 0:
            return 0.0
        
        elapsed = time.time() - self._start_time
        return self._frame_count / elapsed if elapsed > 0 else 0.0
    
    @property
    def is_open(self) -> bool:
        """Verifica se a fonte está aberta."""
        return self._is_open
    
    def _create_frame_info(self, frame: np.ndarray) -> FrameInfo:
        """Cria FrameInfo a partir de um frame."""
        self._frame_count += 1
        return FrameInfo.from_frame(
            frame=frame,
            frame_id=self._frame_count,
            source_type=self.source_type.value,
        )


class USBCameraAdapter(BaseSourceAdapter):
    """
    Adaptador para câmeras USB/USB-C.
    """
    
    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480):
        """
        Inicializa o adaptador.
        
        Args:
            camera_index: Índice da câmera USB
            width: Largura desejada
            height: Altura desejada
        """
        super().__init__(SourceType.USB)
        self.camera_index = camera_index
        self.width = width
        self.height = height
    
    def open(self) -> bool:
        """Abre a câmera USB."""
        # Tenta DirectShow no Windows primeiro
        self._capture = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        
        if not self._capture.isOpened():
            # Fallback para default
            self._capture = cv2.VideoCapture(self.camera_index)
        
        if not self._capture.isOpened():
            logger.error("usb_camera_open_failed", index=self.camera_index)
            raise StreamSourceError(
                f"Não foi possível abrir a câmera USB: {self.camera_index}",
                {"camera_index": self.camera_index}
            )
        
        # Configura resolução
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        self._is_open = True
        self._start_time = time.time()
        
        props = self.get_properties()
        logger.info(
            "usb_camera_opened",
            index=self.camera_index,
            width=props["width"],
            height=props["height"],
        )
        
        return True
    
    def read(self) -> Optional[FrameInfo]:
        """Lê um frame da câmera."""
        if not self._is_open or self._capture is None:
            return None
        
        ret, frame = self._capture.read()
        
        if not ret:
            logger.warning("usb_camera_read_failed", index=self.camera_index)
            return None
        
        return self._create_frame_info(frame)


class GigECameraAdapter(BaseSourceAdapter):
    """
    Adaptador para câmeras GigE Vision.
    
    Nota: Requer drivers GigE instalados.
    """
    
    def __init__(self, ip: str, port: int = 3956):
        """
        Inicializa o adaptador.
        
        Args:
            ip: Endereço IP da câmera
            port: Porta GigE (padrão: 3956)
        """
        super().__init__(SourceType.GIGE)
        self.ip = ip
        self.port = port
    
    def open(self) -> bool:
        """Abre a câmera GigE."""
        # Formato de URL para câmeras GigE
        gige_url = f"gige://{self.ip}:{self.port}"
        
        # Tenta abrir via GStreamer
        gst_pipeline = (
            f"udpsrc address={self.ip} port={self.port} ! "
            "application/x-rtp,encoding-name=JPEG,payload=26 ! "
            "rtpjpegdepay ! jpegdec ! videoconvert ! appsink"
        )
        
        try:
            self._capture = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        except Exception:
            # Fallback para OpenCV padrão
            self._capture = cv2.VideoCapture(gige_url)
        
        if not self._capture.isOpened():
            logger.error("gige_open_failed", ip=self.ip, port=self.port)
            raise StreamSourceError(
                f"Não foi possível abrir câmera GigE: {self.ip}:{self.port}",
                {"ip": self.ip, "port": self.port}
            )
        
        self._is_open = True
        self._start_time = time.time()
        
        props = self.get_properties()
        logger.info(
            "gige_opened",
            ip=self.ip,
            port=self.port,
            width=props.get("width"),
            height=props.get("height"),
        )
        
        return True
    
    def read(self) -> Optional[FrameInfo]:
        """Lê um frame da câmera."""
        if not self._is_open or self._capture is None:
            return None
        
        ret, frame = self._capture.read()
        
        if not ret:
            logger.warning("gige_read_failed", ip=self.ip)
            return None
        
        return self._create_frame_info(frame)


def create_adapter(
    source_type: str,
    camera_index: int = 0,
    gige_ip: str = "",
    gige_port: int = 3956,
    **kwargs
) -> BaseSourceAdapter:
    """
    Factory para criar adaptadores de fonte (somente câmeras USB e GigE).
    """
    source = SourceType(source_type)

    if source == SourceType.USB:
        return USBCameraAdapter(camera_index)
    elif source == SourceType.GIGE:
        return GigECameraAdapter(gige_ip, gige_port)
    else:
        raise ValueError(f"Tipo de fonte não suportado: {source_type}. Use: usb, gige")

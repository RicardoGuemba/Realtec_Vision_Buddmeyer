# -*- coding: utf-8 -*-
"""
Pipeline de pré-processamento de imagens.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
import numpy as np

from PySide6.QtCore import QObject, Signal

from config import get_settings
from core.logger import get_logger
from .roi_manager import ROIManager, ROI
from .transforms import ImageTransforms

logger = get_logger("preprocessing.pipeline")


@dataclass
class PreprocessProfile:
    """Perfil de pré-processamento."""
    
    name: str
    brightness: float = 0.0
    contrast: float = 0.0
    blur: int = 0  # 0 = desativado
    sharpen: bool = False
    equalize: bool = False
    clahe: bool = False
    clahe_clip_limit: float = 2.0


# Perfis pré-definidos
PREPROCESS_PROFILES: Dict[str, PreprocessProfile] = {
    "default": PreprocessProfile(name="default"),
    "bright": PreprocessProfile(name="bright", brightness=0.2),
    "dark": PreprocessProfile(name="dark", brightness=-0.2),
    "high_contrast": PreprocessProfile(name="high_contrast", contrast=0.3),
    "low_contrast": PreprocessProfile(name="low_contrast", contrast=-0.3),
    "enhanced": PreprocessProfile(name="enhanced", clahe=True),
    "smooth": PreprocessProfile(name="smooth", blur=5),
    "sharp": PreprocessProfile(name="sharp", sharpen=True),
}


class PreprocessPipeline(QObject):
    """
    Pipeline de pré-processamento de imagens.
    
    Signals:
        settings_changed: Emitido quando configurações mudam
    """
    
    settings_changed = Signal()
    
    def __init__(self):
        super().__init__()
        
        self._settings = get_settings()
        self._roi_manager = ROIManager()
        self._transforms = ImageTransforms()
        
        # Configurações atuais
        self._brightness = self._settings.preprocess.brightness
        self._contrast = self._settings.preprocess.contrast
        self._profile = self._settings.preprocess.profile
        
        # Carrega perfil inicial
        if self._profile in PREPROCESS_PROFILES:
            self._apply_profile(PREPROCESS_PROFILES[self._profile])
        
        # Configura ROI
        if self._settings.preprocess.roi:
            self._roi_manager.set_roi_from_tuple(
                tuple(self._settings.preprocess.roi)
            )
    
    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Processa um frame.
        
        Args:
            frame: Frame de entrada (BGR)
        
        Returns:
            Frame processado (BGR)
        """
        result = frame.copy()
        
        # Aplica ROI
        if self._roi_manager.has_roi():
            result = self._roi_manager.apply_roi(result)
        
        # Aplica ajustes
        if self._brightness != 0:
            result = self._transforms.adjust_brightness(result, self._brightness)
        
        if self._contrast != 0:
            result = self._transforms.adjust_contrast(result, self._contrast)
        
        return result
    
    def set_roi(self, roi: Optional[Tuple[int, int, int, int]]) -> None:
        """
        Define o ROI.
        
        Args:
            roi: Tupla (x, y, width, height) ou None
        """
        self._roi_manager.set_roi_from_tuple(roi)
        self.settings_changed.emit()
    
    def clear_roi(self) -> None:
        """Remove o ROI."""
        self._roi_manager.clear_roi()
        self.settings_changed.emit()
    
    def set_brightness(self, value: float) -> None:
        """
        Define o brilho.
        
        Args:
            value: Valor de -1.0 a 1.0
        """
        self._brightness = max(-1.0, min(1.0, value))
        self.settings_changed.emit()
    
    def set_contrast(self, value: float) -> None:
        """
        Define o contraste.
        
        Args:
            value: Valor de -1.0 a 1.0
        """
        self._contrast = max(-1.0, min(1.0, value))
        self.settings_changed.emit()
    
    def set_profile(self, profile_name: str) -> bool:
        """
        Define perfil de pré-processamento.
        
        Args:
            profile_name: Nome do perfil
        
        Returns:
            True se perfil encontrado
        """
        if profile_name not in PREPROCESS_PROFILES:
            logger.warning("unknown_profile", profile=profile_name)
            return False
        
        self._apply_profile(PREPROCESS_PROFILES[profile_name])
        self._profile = profile_name
        self.settings_changed.emit()
        
        logger.info("profile_applied", profile=profile_name)
        return True
    
    def _apply_profile(self, profile: PreprocessProfile) -> None:
        """Aplica um perfil."""
        self._brightness = profile.brightness
        self._contrast = profile.contrast
    
    def get_roi_manager(self) -> ROIManager:
        """Retorna o gerenciador de ROI."""
        return self._roi_manager
    
    def transform_coordinates_to_frame(
        self,
        x: float,
        y: float,
    ) -> Tuple[float, float]:
        """
        Transforma coordenadas de ROI para frame completo.
        
        Args:
            x: Coordenada X no ROI
            y: Coordenada Y no ROI
        
        Returns:
            Coordenadas no frame completo
        """
        return self._roi_manager.transform_coordinates(x, y, from_roi=True)
    
    def transform_bbox_to_frame(
        self,
        bbox: Tuple[float, float, float, float],
    ) -> Tuple[float, float, float, float]:
        """
        Transforma bounding box de ROI para frame completo.
        
        Args:
            bbox: (x1, y1, x2, y2) no ROI
        
        Returns:
            Bounding box no frame completo
        """
        return self._roi_manager.transform_bbox(bbox, from_roi=True)
    
    @property
    def brightness(self) -> float:
        return self._brightness
    
    @property
    def contrast(self) -> float:
        return self._contrast
    
    @property
    def current_profile(self) -> str:
        return self._profile
    
    @property
    def has_roi(self) -> bool:
        return self._roi_manager.has_roi()
    
    @property
    def roi(self) -> Optional[ROI]:
        return self._roi_manager.get_roi()
    
    @staticmethod
    def get_available_profiles() -> List[str]:
        """Retorna lista de perfis disponíveis."""
        return list(PREPROCESS_PROFILES.keys())

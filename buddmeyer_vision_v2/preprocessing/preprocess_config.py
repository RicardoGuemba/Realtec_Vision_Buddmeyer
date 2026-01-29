# -*- coding: utf-8 -*-
"""
Configurações de pré-processamento.
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class PreprocessConfig:
    """Configuração de pré-processamento."""
    
    # ROI
    roi_enabled: bool = False
    roi_x: int = 0
    roi_y: int = 0
    roi_width: int = 640
    roi_height: int = 480
    
    # Ajustes de imagem
    brightness: float = 0.0
    contrast: float = 0.0
    
    # Perfil
    profile: str = "default"
    
    # Filtros
    blur_enabled: bool = False
    blur_kernel: int = 5
    sharpen_enabled: bool = False
    equalize_enabled: bool = False
    clahe_enabled: bool = False
    clahe_clip_limit: float = 2.0
    
    def get_roi_tuple(self) -> Optional[tuple]:
        """Retorna ROI como tupla ou None se desativado."""
        if not self.roi_enabled:
            return None
        return (self.roi_x, self.roi_y, self.roi_width, self.roi_height)
    
    def set_roi(self, x: int, y: int, width: int, height: int) -> None:
        """Define ROI."""
        self.roi_enabled = True
        self.roi_x = x
        self.roi_y = y
        self.roi_width = width
        self.roi_height = height
    
    def clear_roi(self) -> None:
        """Limpa ROI."""
        self.roi_enabled = False
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "roi_enabled": self.roi_enabled,
            "roi_x": self.roi_x,
            "roi_y": self.roi_y,
            "roi_width": self.roi_width,
            "roi_height": self.roi_height,
            "brightness": self.brightness,
            "contrast": self.contrast,
            "profile": self.profile,
            "blur_enabled": self.blur_enabled,
            "blur_kernel": self.blur_kernel,
            "sharpen_enabled": self.sharpen_enabled,
            "equalize_enabled": self.equalize_enabled,
            "clahe_enabled": self.clahe_enabled,
            "clahe_clip_limit": self.clahe_clip_limit,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PreprocessConfig":
        """Cria a partir de dicionário."""
        return cls(**data)

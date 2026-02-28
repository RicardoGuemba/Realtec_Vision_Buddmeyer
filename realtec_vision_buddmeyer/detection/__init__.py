# -*- coding: utf-8 -*-
"""
Módulo de detecção do sistema Buddmeyer Vision v2.0
"""

from .inference_engine import InferenceEngine
from .model_loader import ModelLoader
from .postprocess import PostProcessor
from .events import BoundingBox, Detection, DetectionResult, DetectionEvent

__all__ = [
    "InferenceEngine",
    "ModelLoader",
    "PostProcessor",
    "BoundingBox",
    "Detection",
    "DetectionResult",
    "DetectionEvent",
]

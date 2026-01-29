# -*- coding: utf-8 -*-
"""
Dataclasses para eventos de detecção.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any


@dataclass
class BoundingBox:
    """Bounding box de uma detecção."""
    
    x1: float  # Esquerda
    y1: float  # Topo
    x2: float  # Direita
    y2: float  # Base
    
    @property
    def center(self) -> Tuple[float, float]:
        """Retorna centro do bbox."""
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    @property
    def width(self) -> float:
        """Retorna largura do bbox."""
        return abs(self.x2 - self.x1)
    
    @property
    def height(self) -> float:
        """Retorna altura do bbox."""
        return abs(self.y2 - self.y1)
    
    @property
    def area(self) -> float:
        """Retorna área do bbox."""
        return self.width * self.height
    
    def to_list(self) -> List[float]:
        """Converte para lista [x1, y1, x2, y2]."""
        return [self.x1, self.y1, self.x2, self.y2]
    
    def to_xywh(self) -> List[float]:
        """Converte para formato [x, y, width, height]."""
        return [self.x1, self.y1, self.width, self.height]
    
    @classmethod
    def from_list(cls, bbox: List[float]) -> "BoundingBox":
        """Cria a partir de lista [x1, y1, x2, y2]."""
        return cls(x1=bbox[0], y1=bbox[1], x2=bbox[2], y2=bbox[3])
    
    @classmethod
    def from_xywh(cls, x: float, y: float, w: float, h: float) -> "BoundingBox":
        """Cria a partir de formato [x, y, width, height]."""
        return cls(x1=x, y1=y, x2=x + w, y2=y + h)


@dataclass
class Detection:
    """Uma detecção individual."""
    
    bbox: BoundingBox
    confidence: float
    class_id: int
    class_name: str
    
    @property
    def centroid(self) -> Tuple[float, float]:
        """Retorna centroide (centro do bbox)."""
        return self.bbox.center
    
    @property
    def centroid_x(self) -> float:
        """Retorna coordenada X do centroide."""
        return self.centroid[0]
    
    @property
    def centroid_y(self) -> float:
        """Retorna coordenada Y do centroide."""
        return self.centroid[1]
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "bbox": self.bbox.to_list(),
            "confidence": self.confidence,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "centroid": self.centroid,
        }


@dataclass
class DetectionResult:
    """Resultado de uma inferência."""
    
    detections: List[Detection] = field(default_factory=list)
    inference_time_ms: float = 0.0
    frame_id: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def best_detection(self) -> Optional[Detection]:
        """Retorna a detecção com maior confiança."""
        if not self.detections:
            return None
        return max(self.detections, key=lambda d: d.confidence)
    
    @property
    def count(self) -> int:
        """Retorna número de detecções."""
        return len(self.detections)
    
    @property
    def has_detections(self) -> bool:
        """Verifica se há detecções."""
        return len(self.detections) > 0
    
    def filter_by_confidence(self, threshold: float) -> List[Detection]:
        """Filtra detecções por threshold de confiança."""
        return [d for d in self.detections if d.confidence >= threshold]
    
    def filter_by_class(self, class_names: List[str]) -> List[Detection]:
        """Filtra detecções por classe."""
        return [d for d in self.detections if d.class_name in class_names]
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "detections": [d.to_dict() for d in self.detections],
            "inference_time_ms": self.inference_time_ms,
            "frame_id": self.frame_id,
            "timestamp": self.timestamp.isoformat(),
            "count": self.count,
        }


@dataclass
class DetectionEvent:
    """
    Evento de detecção para comunicação com CLP.
    
    Contém os dados necessários para enviar ao CLP.
    """
    
    detected: bool
    class_name: str = ""
    confidence: float = 0.0
    bbox: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    centroid: Tuple[float, float] = (0.0, 0.0)
    source_id: str = ""
    frame_id: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    inference_time_ms: float = 0.0
    detection_count: int = 0
    
    @classmethod
    def from_result(
        cls,
        result: DetectionResult,
        source_id: str = "main",
    ) -> "DetectionEvent":
        """
        Cria evento a partir de DetectionResult.
        
        Usa a melhor detecção (maior confiança).
        """
        best = result.best_detection
        
        if best is None:
            return cls(
                detected=False,
                source_id=source_id,
                frame_id=result.frame_id,
                timestamp=result.timestamp,
                inference_time_ms=result.inference_time_ms,
            )
        
        return cls(
            detected=True,
            class_name=best.class_name,
            confidence=best.confidence,
            bbox=best.bbox.to_list(),
            centroid=best.centroid,
            source_id=source_id,
            frame_id=result.frame_id,
            timestamp=result.timestamp,
            inference_time_ms=result.inference_time_ms,
            detection_count=result.count,
        )
    
    def to_plc_data(self) -> Dict[str, Any]:
        """
        Converte para dados do CLP.
        
        Returns:
            Dict com tags e valores para o CLP
        """
        return {
            "product_detected": self.detected,
            "centroid_x": self.centroid[0],
            "centroid_y": self.centroid[1],
            "confidence": self.confidence,
            "detection_count": self.detection_count,
            "processing_time": self.inference_time_ms,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário completo."""
        return {
            "detected": self.detected,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox": self.bbox,
            "centroid": {
                "x": self.centroid[0],
                "y": self.centroid[1],
            },
            "source_id": self.source_id,
            "frame_id": self.frame_id,
            "timestamp": self.timestamp.isoformat(),
            "inference_time_ms": self.inference_time_ms,
            "detection_count": self.detection_count,
        }

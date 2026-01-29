# -*- coding: utf-8 -*-
"""
Overlay de detecções para o widget de vídeo.
"""

from typing import List, Optional, Tuple

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush

from detection.events import Detection


class OverlayStyle:
    """Estilo do overlay."""
    
    def __init__(
        self,
        box_thickness: int = 2,
        box_corner_radius: int = 4,
        label_font_size: int = 10,
        centroid_size: int = 8,
        show_label: bool = True,
        show_confidence: bool = True,
        show_centroid: bool = True,
        color_high: QColor = None,
        color_medium: QColor = None,
        color_low: QColor = None,
        color_very_low: QColor = None,
    ):
        self.box_thickness = box_thickness
        self.box_corner_radius = box_corner_radius
        self.label_font_size = label_font_size
        self.centroid_size = centroid_size
        self.show_label = show_label
        self.show_confidence = show_confidence
        self.show_centroid = show_centroid
        
        # Cores por threshold de confiança
        self.color_high = color_high or QColor(0, 255, 0)      # > 0.8
        self.color_medium = color_medium or QColor(255, 255, 0)  # > 0.5
        self.color_low = color_low or QColor(255, 165, 0)     # > 0.3
        self.color_very_low = color_very_low or QColor(255, 0, 0)  # < 0.3


class DetectionOverlay:
    """
    Classe para desenhar overlay de detecções.
    
    Pode ser usada por qualquer widget que precise desenhar detecções.
    """
    
    def __init__(self, style: Optional[OverlayStyle] = None):
        self._style = style or OverlayStyle()
        self._detections: List[Detection] = []
        self._scale_x = 1.0
        self._scale_y = 1.0
        self._offset_x = 0
        self._offset_y = 0
    
    def set_detections(self, detections: List[Detection]) -> None:
        """Define as detecções a serem exibidas."""
        self._detections = detections
    
    def set_transform(
        self,
        scale_x: float,
        scale_y: float,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> None:
        """Define a transformação de coordenadas."""
        self._scale_x = scale_x
        self._scale_y = scale_y
        self._offset_x = offset_x
        self._offset_y = offset_y
    
    def set_style(self, style: OverlayStyle) -> None:
        """Define o estilo do overlay."""
        self._style = style
    
    def draw(self, painter: QPainter) -> None:
        """Desenha as detecções."""
        for detection in self._detections:
            self._draw_detection(painter, detection)
    
    def _draw_detection(self, painter: QPainter, detection: Detection) -> None:
        """Desenha uma detecção individual."""
        color = self._get_color(detection.confidence)
        
        # Transforma coordenadas
        bbox = detection.bbox
        x1 = bbox.x1 * self._scale_x + self._offset_x
        y1 = bbox.y1 * self._scale_y + self._offset_y
        x2 = bbox.x2 * self._scale_x + self._offset_x
        y2 = bbox.y2 * self._scale_y + self._offset_y
        
        width = x2 - x1
        height = y2 - y1
        
        # Bounding box
        pen = QPen(color, self._style.box_thickness)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        rect = QRectF(x1, y1, width, height)
        painter.drawRoundedRect(
            rect,
            self._style.box_corner_radius,
            self._style.box_corner_radius,
        )
        
        # Centroide
        if self._style.show_centroid:
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            size = self._style.centroid_size
            
            painter.setBrush(QBrush(color))
            painter.drawEllipse(
                QPointF(cx, cy),
                size / 2,
                size / 2,
            )
            
            # Cruz no centroide
            painter.setPen(QPen(Qt.black, 1))
            painter.drawLine(
                QPointF(cx - size/2, cy),
                QPointF(cx + size/2, cy),
            )
            painter.drawLine(
                QPointF(cx, cy - size/2),
                QPointF(cx, cy + size/2),
            )
        
        # Label
        if self._style.show_label:
            self._draw_label(painter, detection, x1, y1, color)
    
    def _draw_label(
        self,
        painter: QPainter,
        detection: Detection,
        x: float,
        y: float,
        color: QColor,
    ) -> None:
        """Desenha o label da detecção."""
        # Texto do label
        if self._style.show_confidence:
            text = f"{detection.class_name} {detection.confidence:.0%}"
        else:
            text = detection.class_name
        
        # Fonte
        font = QFont("Segoe UI", self._style.label_font_size, QFont.Bold)
        painter.setFont(font)
        
        # Calcula tamanho do texto
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(text) + 8
        text_height = metrics.height() + 4
        
        # Background do label
        label_rect = QRectF(x, y - text_height - 2, text_width, text_height)
        painter.fillRect(label_rect, color)
        
        # Borda do label
        painter.setPen(QPen(color.darker(120), 1))
        painter.drawRect(label_rect)
        
        # Texto
        painter.setPen(QPen(Qt.black))
        painter.drawText(label_rect, Qt.AlignCenter, text)
    
    def _get_color(self, confidence: float) -> QColor:
        """Retorna a cor baseada na confiança."""
        if confidence >= 0.8:
            return self._style.color_high
        elif confidence >= 0.5:
            return self._style.color_medium
        elif confidence >= 0.3:
            return self._style.color_low
        else:
            return self._style.color_very_low
    
    def get_detection_at_point(
        self,
        x: float,
        y: float,
    ) -> Optional[Detection]:
        """
        Retorna a detecção no ponto especificado.
        
        Args:
            x: Coordenada X (em coordenadas do widget)
            y: Coordenada Y (em coordenadas do widget)
        
        Returns:
            Detection se houver uma no ponto, None caso contrário
        """
        # Converte para coordenadas da imagem
        img_x = (x - self._offset_x) / self._scale_x
        img_y = (y - self._offset_y) / self._scale_y
        
        for detection in reversed(self._detections):  # Mais recente primeiro
            bbox = detection.bbox
            if (bbox.x1 <= img_x <= bbox.x2 and
                bbox.y1 <= img_y <= bbox.y2):
                return detection
        
        return None

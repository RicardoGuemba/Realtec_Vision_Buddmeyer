# -*- coding: utf-8 -*-
"""
Widget de gráficos de métricas.
"""

from typing import List, Deque
from collections import deque
from datetime import datetime

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QPainterPath

from core.metrics import MetricsCollector


class MetricsChart(QWidget):
    """
    Widget para exibição de gráfico de métricas.
    
    Exibe um gráfico de linha simples com histórico de valores.
    """
    
    def __init__(
        self,
        metric_name: str,
        title: str = "",
        unit: str = "",
        max_points: int = 60,
        parent=None,
    ):
        super().__init__(parent)
        
        self._metric_name = metric_name
        self._title = title or metric_name
        self._unit = unit
        self._max_points = max_points
        
        self._values: Deque[float] = deque(maxlen=max_points)
        self._min_value = 0.0
        self._max_value = 100.0
        self._current_value = 0.0
        
        # Cores
        self._line_color = QColor(0, 212, 255)  # Cyan
        self._grid_color = QColor(45, 55, 72)
        self._bg_color = QColor(26, 26, 46)
        self._text_color = QColor(224, 224, 224)
        
        self._setup_ui()
        
        # Timer para atualização
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_from_metrics)
        self._update_timer.start(1000)  # 1 segundo
    
    def _setup_ui(self) -> None:
        """Configura a interface."""
        self.setMinimumHeight(120)
        self.setStyleSheet(f"background-color: {self._bg_color.name()};")
    
    def add_value(self, value: float) -> None:
        """Adiciona um valor ao gráfico."""
        self._values.append(value)
        self._current_value = value
        
        # Atualiza min/max
        if self._values:
            values_list = list(self._values)
            data_min = min(values_list)
            data_max = max(values_list)
            
            # Padding de 10%
            range_val = data_max - data_min
            if range_val < 1:
                range_val = 1
            
            self._min_value = max(0, data_min - range_val * 0.1)
            self._max_value = data_max + range_val * 0.1
        
        self.update()
    
    def set_range(self, min_val: float, max_val: float) -> None:
        """Define range fixo do gráfico."""
        self._min_value = min_val
        self._max_value = max_val
        self.update()
    
    def set_color(self, color: QColor) -> None:
        """Define cor da linha."""
        self._line_color = color
        self.update()
    
    def clear(self) -> None:
        """Limpa os dados."""
        self._values.clear()
        self._current_value = 0.0
        self.update()
    
    def paintEvent(self, event) -> None:
        """Evento de pintura."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dimensões
        width = self.width()
        height = self.height()
        margin_top = 25
        margin_bottom = 20
        margin_left = 50
        margin_right = 10
        
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom
        
        # Background
        painter.fillRect(self.rect(), self._bg_color)
        
        # Título e valor atual
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.setPen(QPen(self._text_color))
        title_text = f"{self._title}: {self._current_value:.1f} {self._unit}"
        painter.drawText(margin_left, 18, title_text)
        
        # Grade
        painter.setPen(QPen(self._grid_color, 1, Qt.DashLine))
        
        # Linhas horizontais
        for i in range(5):
            y = margin_top + i * chart_height / 4
            painter.drawLine(margin_left, int(y), width - margin_right, int(y))
            
            # Labels
            value = self._max_value - i * (self._max_value - self._min_value) / 4
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(5, int(y + 4), f"{value:.0f}")
        
        # Desenha linha do gráfico
        if len(self._values) > 1:
            self._draw_line(
                painter,
                margin_left,
                margin_top,
                chart_width,
                chart_height,
            )
        
        painter.end()
    
    def _draw_line(
        self,
        painter: QPainter,
        x_offset: int,
        y_offset: int,
        width: int,
        height: int,
    ) -> None:
        """Desenha a linha do gráfico."""
        values = list(self._values)
        n = len(values)
        
        if n < 2:
            return
        
        # Calcula pontos
        points = []
        for i, value in enumerate(values):
            x = x_offset + i * width / (n - 1)
            y = y_offset + height - (value - self._min_value) / (self._max_value - self._min_value) * height
            points.append((x, y))
        
        # Desenha área preenchida
        path = QPainterPath()
        path.moveTo(points[0][0], y_offset + height)
        
        for x, y in points:
            path.lineTo(x, y)
        
        path.lineTo(points[-1][0], y_offset + height)
        path.closeSubpath()
        
        fill_color = QColor(self._line_color)
        fill_color.setAlpha(30)
        painter.fillPath(path, fill_color)
        
        # Desenha linha
        painter.setPen(QPen(self._line_color, 2))
        
        for i in range(len(points) - 1):
            painter.drawLine(
                int(points[i][0]), int(points[i][1]),
                int(points[i+1][0]), int(points[i+1][1]),
            )
        
        # Ponto atual
        if points:
            last_x, last_y = points[-1]
            painter.setBrush(self._line_color)
            painter.drawEllipse(int(last_x) - 4, int(last_y) - 4, 8, 8)
    
    def _update_from_metrics(self) -> None:
        """Atualiza do coletor de métricas."""
        metrics = MetricsCollector()
        value = metrics.get_last_value(self._metric_name)
        if value is not None:
            self.add_value(value)

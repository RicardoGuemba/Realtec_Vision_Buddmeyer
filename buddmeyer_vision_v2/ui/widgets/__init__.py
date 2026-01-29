# -*- coding: utf-8 -*-
"""
Widgets customizados para a interface do sistema Buddmeyer Vision v2.0
"""

from .video_widget import VideoWidget
from .detection_overlay import DetectionOverlay
from .status_panel import StatusPanel
from .metrics_chart import MetricsChart
from .event_console import EventConsole
from .log_viewer import LogViewer

__all__ = [
    "VideoWidget",
    "DetectionOverlay",
    "StatusPanel",
    "MetricsChart",
    "EventConsole",
    "LogViewer",
]

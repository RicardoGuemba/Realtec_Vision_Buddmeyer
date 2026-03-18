# -*- coding: utf-8 -*-
"""
Widgets customizados para a interface do sistema Buddmeyer Vision v2.0
"""

from .video_widget import VideoWidget
from .status_panel import StatusPanel
from .metrics_chart import MetricsChart
from .event_console import EventConsole
from .log_viewer import LogViewer
from .gentl_camera_settings_dialog import GenTLCameraSettingsDialog

__all__ = [
    "VideoWidget",
    "StatusPanel",
    "MetricsChart",
    "EventConsole",
    "LogViewer",
    "GenTLCameraSettingsDialog",
]

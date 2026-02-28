# -*- coding: utf-8 -*-
"""
Módulo core do sistema Buddmeyer Vision v2.0
"""

from .logger import setup_logging, get_logger
from .exceptions import (
    BuddmeyerVisionError,
    StreamError,
    DetectionError,
    CIPError,
    ConfigurationError,
)
from .metrics import MetricsCollector

__all__ = [
    "setup_logging",
    "get_logger",
    "BuddmeyerVisionError",
    "StreamError",
    "DetectionError",
    "CIPError",
    "ConfigurationError",
    "MetricsCollector",
]

# -*- coding: utf-8 -*-
"""
Módulo de saída de stream para supervisório web.
"""

from .mjpeg_stream import MjpegStreamServer, StreamFrameProvider

__all__ = ["MjpegStreamServer", "StreamFrameProvider"]

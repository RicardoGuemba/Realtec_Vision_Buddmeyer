# -*- coding: utf-8 -*-
"""Testes unitários para output.mjpeg_stream."""

import pytest
import numpy as np

from detection.events import Detection, BoundingBox
from output.mjpeg_stream import StreamFrameProvider, MjpegStreamServer


class TestStreamFrameProvider:
    """Testes para StreamFrameProvider."""

    def test_update_get_jpeg_empty(self):
        p = StreamFrameProvider()
        assert p.get_jpeg_bytes() is None

    def test_update_frame_get_jpeg(self, sample_frame_640x480):
        p = StreamFrameProvider()
        p.update(sample_frame_640x480, None)
        jpeg = p.get_jpeg_bytes()
        assert jpeg is not None
        assert len(jpeg) > 100
        assert jpeg[:2] == b"\xff\xd8"  # JPEG magic

    def test_update_detections(self, sample_frame_640x480, sample_detection):
        p = StreamFrameProvider()
        p.update(sample_frame_640x480, [sample_detection])
        jpeg = p.get_jpeg_bytes()
        assert jpeg is not None

    def test_update_none_preserves_previous(self, sample_frame_640x480):
        p = StreamFrameProvider()
        p.update(sample_frame_640x480, None)
        j1 = p.get_jpeg_bytes()
        p.update(None, None)  # Só detecções vazias
        j2 = p.get_jpeg_bytes()
        assert j2 is not None


class TestMjpegStreamServer:
    """Testes para MjpegStreamServer."""

    def test_start_stop(self):
        p = StreamFrameProvider()
        p.update(np.zeros((10, 10, 3), dtype=np.uint8), None)
        s = MjpegStreamServer(p, port=18766, fps=5)
        assert s.start() is True
        s.stop()

# -*- coding: utf-8 -*-
"""Testes unitários para streaming.frame_buffer."""

import pytest
import numpy as np

from streaming.frame_buffer import FrameBuffer, FrameInfo


@pytest.fixture
def sample_frame_info():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    return FrameInfo.from_frame(frame, frame_id=1, source_type="usb")


class TestFrameInfo:
    """Testes para FrameInfo."""

    def test_from_frame(self, sample_frame_640x480):
        fi = FrameInfo.from_frame(sample_frame_640x480, frame_id=5, source_type="video")
        assert fi.frame_id == 5
        assert fi.source_type == "video"
        assert fi.width == 640
        assert fi.height == 480
        assert fi.channels == 3

    def test_shape_size_bytes(self, sample_frame_info):
        assert sample_frame_info.shape == (480, 640, 3)
        assert sample_frame_info.size_bytes == 480 * 640 * 3


class TestFrameBuffer:
    """Testes para FrameBuffer."""

    def test_put_get(self, sample_frame_info):
        buf = FrameBuffer(max_size=5)
        buf.put(sample_frame_info)
        out = buf.get()
        assert out is not None
        assert out.frame_id == sample_frame_info.frame_id

    def test_peek_empty(self):
        buf = FrameBuffer(max_size=5)
        assert buf.peek() is None

    def test_peek_returns_latest(self, sample_frame_info):
        buf = FrameBuffer(max_size=5)
        buf.put(sample_frame_info)
        assert buf.peek() is not None
        assert buf.size == 1

    def test_clear(self, sample_frame_info):
        buf = FrameBuffer(max_size=5)
        buf.put(sample_frame_info)
        buf.put(sample_frame_info)
        count = buf.clear()
        assert count == 2
        assert buf.is_empty
        assert buf.peek() is None

    def test_max_size_drop(self, sample_frame_info):
        buf = FrameBuffer(max_size=2)
        buf.put(sample_frame_info)
        buf.put(FrameInfo.from_frame(sample_frame_info.frame, 2, "usb"))
        buf.put(FrameInfo.from_frame(sample_frame_info.frame, 3, "usb"))
        assert buf.size == 2
        assert buf.dropped_count >= 1

    def test_usage_percent(self, sample_frame_info):
        buf = FrameBuffer(max_size=10)
        buf.put(sample_frame_info)
        assert buf.usage_percent == 10.0

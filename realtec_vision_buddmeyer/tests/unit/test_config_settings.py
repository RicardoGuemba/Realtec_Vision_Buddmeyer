# -*- coding: utf-8 -*-
"""Testes unitários para config.settings."""

import pytest
from pathlib import Path
import tempfile

from config.settings import (
    StreamingSettings,
    DetectionSettings,
    PreprocessSettings,
    OutputSettings,
    Settings,
)


class TestStreamingSettings:
    """Testes para StreamingSettings."""

    def test_default_source_type(self):
        s = StreamingSettings()
        assert s.source_type == "usb"

    def test_invalid_source_type_raises(self):
        with pytest.raises(ValueError):
            StreamingSettings(source_type="invalid")


class TestDetectionSettings:
    """Testes para DetectionSettings."""

    def test_invalid_device_raises(self):
        with pytest.raises(ValueError):
            DetectionSettings(device="invalid")


class TestPreprocessSettings:
    """Testes para PreprocessSettings."""

    def test_mm_per_pixel_default(self):
        s = PreprocessSettings()
        assert s.mm_per_pixel == 1.0


class TestOutputSettings:
    """Testes para OutputSettings."""

    def test_stream_http_defaults(self):
        s = OutputSettings()
        assert s.stream_http_enabled is True
        assert s.stream_http_port == 8765
        assert s.stream_http_fps == 10


class TestSettings:
    """Testes para Settings."""

    def test_default_creation(self):
        s = Settings()
        assert s.streaming is not None
        assert s.detection is not None
        assert s.preprocess is not None
        assert s.output is not None

    def test_from_yaml_nonexistent(self):
        s = Settings.from_yaml(Path("/nonexistent/config.yaml"))
        assert s is not None
        assert isinstance(s, Settings)

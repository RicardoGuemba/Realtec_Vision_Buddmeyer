# -*- coding: utf-8 -*-
"""Fixtures e configuração do pytest."""

import sys
from pathlib import Path

import pytest
import numpy as np

# Garante que o package buddmeyer_vision_v2 está no path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@pytest.fixture
def sample_frame_640x480():
    """Frame numpy 640x480 BGR para testes."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_bbox():
    """BoundingBox de exemplo."""
    from detection.events import BoundingBox
    return BoundingBox(x1=100, y1=50, x2=200, y2=150)


@pytest.fixture
def sample_detection(sample_bbox):
    """Detection de exemplo."""
    from detection.events import Detection
    return Detection(
        bbox=sample_bbox,
        confidence=0.85,
        class_id=0,
        class_name="Embalagem",
    )

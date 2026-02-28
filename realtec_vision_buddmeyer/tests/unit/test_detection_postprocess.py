# -*- coding: utf-8 -*-
"""Testes unitários para detection.postprocess (PostProcessor)."""

import pytest
import numpy as np

from detection.postprocess import PostProcessor


class TestPostProcessorNms:
    """Testes para NMS do PostProcessor."""

    def test_nms_empty(self):
        pp = PostProcessor()
        keep = pp._nms(np.array([]), np.array([]), 0.5)
        assert keep == []

    def test_nms_single_box(self):
        pp = PostProcessor()
        boxes = np.array([[0, 0, 10, 10]])
        scores = np.array([0.9])
        keep = pp._nms(boxes, scores, 0.5)
        assert keep == [0]

    def test_nms_overlapping_keeps_highest(self):
        pp = PostProcessor()
        boxes = np.array([
            [0, 0, 20, 20],
            [5, 5, 25, 25],
            [100, 100, 120, 120],
        ])
        scores = np.array([0.5, 0.9, 0.7])  # Middle has highest
        keep = pp._nms(boxes, scores, 0.3)
        assert 1 in keep  # Highest score
        assert 2 in keep  # Non-overlapping


class TestPostProcessorSetters:
    """Testes para setters do PostProcessor."""

    def test_set_confidence_clamps(self):
        pp = PostProcessor(confidence_threshold=0.5)
        pp.set_confidence_threshold(1.5)
        assert pp.confidence_threshold == 1.0
        pp.set_confidence_threshold(-0.1)
        assert pp.confidence_threshold == 0.0

    def test_set_max_detections_min_one(self):
        pp = PostProcessor(max_detections=10)
        pp.set_max_detections(0)
        assert pp.max_detections == 1

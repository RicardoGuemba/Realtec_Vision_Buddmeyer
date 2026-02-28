# -*- coding: utf-8 -*-
"""Testes unitários para detection.events."""

import pytest
from datetime import datetime

from detection.events import (
    BoundingBox,
    Detection,
    DetectionResult,
    DetectionEvent,
)


class TestBoundingBox:
    """Testes para BoundingBox."""

    def test_center(self):
        b = BoundingBox(x1=0, y1=0, x2=100, y2=50)
        assert b.center == (50.0, 25.0)

    def test_width_height(self):
        b = BoundingBox(x1=10, y1=20, x2=110, y2=70)
        assert b.width == 100
        assert b.height == 50

    def test_area(self):
        b = BoundingBox(x1=0, y1=0, x2=10, y2=20)
        assert b.area == 200.0

    def test_to_list(self):
        b = BoundingBox(x1=1, y1=2, x2=3, y2=4)
        assert b.to_list() == [1, 2, 3, 4]

    def test_from_list(self):
        b = BoundingBox.from_list([10, 20, 30, 40])
        assert b.x1 == 10 and b.y1 == 20 and b.x2 == 30 and b.y2 == 40

    def test_from_xywh(self):
        b = BoundingBox.from_xywh(10, 20, 50, 30)
        assert b.x1 == 10 and b.y1 == 20
        assert b.x2 == 60 and b.y2 == 50
        assert b.width == 50 and b.height == 30


class TestDetection:
    """Testes para Detection."""

    def test_centroid(self, sample_detection):
        assert sample_detection.centroid == (150.0, 100.0)

    def test_centroid_x_y(self, sample_detection):
        assert sample_detection.centroid_x == 150.0
        assert sample_detection.centroid_y == 100.0

    def test_to_dict(self, sample_detection):
        d = sample_detection.to_dict()
        assert d["class_name"] == "Embalagem"
        assert d["confidence"] == 0.85
        assert d["bbox"] == [100, 50, 200, 150]
        assert d["centroid"] == (150.0, 100.0)


class TestDetectionResult:
    """Testes para DetectionResult."""

    def test_empty_best_detection(self):
        r = DetectionResult(detections=[])
        assert r.best_detection is None
        assert r.count == 0
        assert not r.has_detections

    def test_best_detection(self, sample_detection):
        low = Detection(
            bbox=sample_detection.bbox,
            confidence=0.3,
            class_id=0,
            class_name="X",
        )
        r = DetectionResult(detections=[low, sample_detection])
        assert r.best_detection.confidence == 0.85
        assert r.count == 2
        assert r.has_detections

    def test_filter_by_confidence(self, sample_detection):
        low = Detection(
            bbox=sample_detection.bbox,
            confidence=0.2,
            class_id=0,
            class_name="X",
        )
        r = DetectionResult(detections=[low, sample_detection])
        filt = r.filter_by_confidence(0.5)
        assert len(filt) == 1
        assert filt[0].confidence == 0.85

    def test_filter_by_class(self, sample_detection):
        other = Detection(
            bbox=sample_detection.bbox,
            confidence=0.9,
            class_id=1,
            class_name="Outro",
        )
        r = DetectionResult(detections=[sample_detection, other])
        filt = r.filter_by_class(["Embalagem"])
        assert len(filt) == 1
        assert filt[0].class_name == "Embalagem"


class TestDetectionEvent:
    """Testes para DetectionEvent."""

    def test_from_result_empty(self):
        r = DetectionResult(detections=[], frame_id=1)
        e = DetectionEvent.from_result(r)
        assert not e.detected
        assert e.frame_id == 1

    def test_from_result_with_detection(self, sample_detection):
        r = DetectionResult(detections=[sample_detection], frame_id=5)
        e = DetectionEvent.from_result(r)
        assert e.detected
        assert e.class_name == "Embalagem"
        assert e.confidence == 0.85
        assert e.centroid == (150.0, 100.0)
        assert e.frame_id == 5

    def test_to_plc_data(self, sample_detection):
        r = DetectionResult(detections=[sample_detection])
        e = DetectionEvent.from_result(r)
        plc = e.to_plc_data()
        assert plc["product_detected"] is True
        assert plc["centroid_x"] == 150.0
        assert plc["centroid_y"] == 100.0
        assert "confidence" in plc
        assert "detection_count" in plc

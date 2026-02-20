# -*- coding: utf-8 -*-
"""Testes unitários para preprocessing.roi_manager (ROI dataclass)."""

import pytest

from preprocessing.roi_manager import ROI


class TestROI:
    """Testes para ROI."""

    def test_center(self):
        r = ROI(x=0, y=0, width=100, height=50)
        assert r.center == (50, 25)

    def test_area(self):
        r = ROI(x=10, y=20, width=30, height=40)
        assert r.area == 1200

    def test_x2_y2(self):
        r = ROI(x=5, y=10, width=20, height=30)
        assert r.x2 == 25
        assert r.y2 == 40

    def test_from_tuple(self):
        r = ROI.from_tuple((10, 20, 50, 60))
        assert r.x == 10 and r.y == 20
        assert r.width == 50 and r.height == 60

    def test_from_xyxy(self):
        r = ROI.from_xyxy(10, 20, 60, 80)
        assert r.x == 10 and r.y == 20
        assert r.width == 50 and r.height == 60

    def test_contains_point(self):
        r = ROI(x=10, y=10, width=20, height=20)
        assert r.contains_point(15, 15) is True
        assert r.contains_point(5, 5) is False
        assert r.contains_point(10, 10) is True
        assert r.contains_point(29, 29) is True
        assert r.contains_point(30, 30) is False

    def test_clip_to_frame(self):
        r = ROI(x=-10, y=0, width=200, height=100)
        clipped = r.clip_to_frame(100, 100)
        assert clipped.x >= 0
        assert clipped.x + clipped.width <= 100
        assert clipped.y + clipped.height <= 100

    def test_scale(self):
        r = ROI(x=10, y=20, width=50, height=30)
        s = r.scale(2.0, 0.5)
        assert s.x == 20 and s.y == 10
        assert s.width == 100 and s.height == 15

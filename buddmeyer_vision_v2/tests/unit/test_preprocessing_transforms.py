# -*- coding: utf-8 -*-
"""Testes unitários para preprocessing.transforms."""

import pytest
import numpy as np

from preprocessing.transforms import pixel_to_mm, ImageTransforms


class TestPixelToMm:
    """Testes para pixel_to_mm."""

    def test_identity(self):
        out = pixel_to_mm((100.0, 200.0), 1.0)
        assert out == (100.0, 200.0)

    def test_conversion(self):
        out = pixel_to_mm((100.0, 200.0), 0.25)
        assert out == (25.0, 50.0)

    def test_zero_mm_per_pixel_returns_unchanged(self):
        out = pixel_to_mm((50.0, 75.0), 0)
        assert out == (50.0, 75.0)

    def test_negative_mm_per_pixel_returns_unchanged(self):
        out = pixel_to_mm((10.0, 20.0), -0.5)
        assert out == (10.0, 20.0)


class TestImageTransforms:
    """Testes para ImageTransforms."""

    def test_adjust_brightness_zero_unchanged(self, sample_frame_640x480):
        result = ImageTransforms.adjust_brightness(sample_frame_640x480, 0)
        np.testing.assert_array_equal(result, sample_frame_640x480)

    def test_adjust_brightness_positive(self):
        img = np.full((10, 10, 3), 100, dtype=np.uint8)
        result = ImageTransforms.adjust_brightness(img, 0.2)
        assert result.mean() > 100

    def test_adjust_contrast_zero_unchanged(self, sample_frame_640x480):
        result = ImageTransforms.adjust_contrast(sample_frame_640x480, 0)
        np.testing.assert_array_equal(result, sample_frame_640x480)

    def test_normalize_denormalize_roundtrip(self):
        img = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
        norm = ImageTransforms.normalize(img)
        denorm = ImageTransforms.denormalize(norm)
        np.testing.assert_allclose(denorm, img, atol=1)

    def test_resize_keep_aspect(self):
        img = np.zeros((100, 200, 3), dtype=np.uint8)
        resized = ImageTransforms.resize(img, 400, 400, keep_aspect=True)
        h, w = resized.shape[:2]
        assert w == 400
        assert h == 200  # 100 * (400/200) = 200

    def test_crop_bounds(self):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cropped = ImageTransforms.crop(img, 10, 20, 30, 40)
        assert cropped.shape == (40, 30, 3)

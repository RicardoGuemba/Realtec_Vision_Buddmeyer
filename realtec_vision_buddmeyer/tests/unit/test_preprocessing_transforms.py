# -*- coding: utf-8 -*-
"""Testes unitários para preprocessing.transforms."""

import pytest
import numpy as np

from preprocessing.transforms import pixel_to_mm, clamp_centroid_to_confinement, ImageTransforms


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


class TestClampCentroidToConfinement:
    """Testes para clamp_centroid_to_confinement."""

    def test_inside_unchanged(self):
        """Centroide dentro da ROI permanece inalterado."""
        result = clamp_centroid_to_confinement(
            centroid_mm=(320.0, 240.0),
            image_center_mm=(320.0, 240.0),
            x_pos_mm=200.0, x_neg_mm=200.0,
            y_pos_mm=150.0, y_neg_mm=150.0,
        )
        assert result == (320.0, 240.0)

    def test_outside_right_clamped(self):
        """Centroide à direita é projetado para o limite X+."""
        result = clamp_centroid_to_confinement(
            centroid_mm=(600.0, 240.0),
            image_center_mm=(320.0, 240.0),
            x_pos_mm=100.0, x_neg_mm=100.0,
            y_pos_mm=100.0, y_neg_mm=100.0,
        )
        assert result[0] == pytest.approx(420.0)
        assert result[1] == pytest.approx(240.0)

    def test_outside_left_clamped(self):
        """Centroide à esquerda é projetado para o limite X-."""
        result = clamp_centroid_to_confinement(
            centroid_mm=(50.0, 240.0),
            image_center_mm=(320.0, 240.0),
            x_pos_mm=100.0, x_neg_mm=100.0,
            y_pos_mm=100.0, y_neg_mm=100.0,
        )
        assert result[0] == pytest.approx(220.0)

    def test_outside_top_clamped(self):
        """Centroide acima (valor Y menor) é projetado para o limite Y+."""
        result = clamp_centroid_to_confinement(
            centroid_mm=(320.0, 10.0),
            image_center_mm=(320.0, 240.0),
            x_pos_mm=200.0, x_neg_mm=200.0,
            y_pos_mm=150.0, y_neg_mm=150.0,
        )
        assert result[1] == pytest.approx(90.0)

    def test_outside_bottom_clamped(self):
        """Centroide abaixo (valor Y maior) é projetado para o limite Y-."""
        result = clamp_centroid_to_confinement(
            centroid_mm=(320.0, 500.0),
            image_center_mm=(320.0, 240.0),
            x_pos_mm=200.0, x_neg_mm=200.0,
            y_pos_mm=150.0, y_neg_mm=150.0,
        )
        assert result[1] == pytest.approx(390.0)

    def test_corner_clamped(self):
        """Centroide no canto é projetado para o canto da ROI."""
        result = clamp_centroid_to_confinement(
            centroid_mm=(999.0, 999.0),
            image_center_mm=(320.0, 240.0),
            x_pos_mm=100.0, x_neg_mm=100.0,
            y_pos_mm=80.0, y_neg_mm=80.0,
        )
        assert result[0] == pytest.approx(420.0)
        assert result[1] == pytest.approx(320.0)

    def test_asymmetric_limits(self):
        """Limites assimétricos (X-=50, X+=300) funcionam corretamente."""
        cx = 320.0 + 400.0  # 720.0 — fora de X+
        result = clamp_centroid_to_confinement(
            centroid_mm=(cx, 240.0),
            image_center_mm=(320.0, 240.0),
            x_pos_mm=300.0, x_neg_mm=50.0,
            y_pos_mm=100.0, y_neg_mm=100.0,
        )
        assert result[0] == pytest.approx(620.0)

        cx_left = 320.0 - 100.0  # 220.0 — fora de X- (=50)
        result2 = clamp_centroid_to_confinement(
            centroid_mm=(cx_left, 240.0),
            image_center_mm=(320.0, 240.0),
            x_pos_mm=300.0, x_neg_mm=50.0,
            y_pos_mm=100.0, y_neg_mm=100.0,
        )
        assert result2[0] == pytest.approx(270.0)


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

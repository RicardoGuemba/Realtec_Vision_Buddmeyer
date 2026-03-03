# -*- coding: utf-8 -*-
"""Testes unitários para VideoWidget — ROI de confinamento."""

import sys
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPainter, QImage

if QApplication.instance() is None:
    _app = QApplication(sys.argv)


class TestVideoWidgetConfinementROI:
    """Testes para o desenho da ROI de confinamento (X e Y relativos ao centro)."""

    def test_draw_confinement_roi_draws_with_confinement_config(self):
        """ROI desenha retângulo quando preprocess.confinement (X-, X+, Y+, Y- em mm) está definido."""
        from config import get_settings

        settings = get_settings(reload=True)
        settings.preprocess.mm_per_pixel = 1.0
        settings.preprocess.confinement.x_positive_mm = 100.0
        settings.preprocess.confinement.x_negative_mm = 100.0
        settings.preprocess.confinement.y_positive_mm = 75.0
        settings.preprocess.confinement.y_negative_mm = 75.0

        from ui.widgets.video_widget import VideoWidget

        widget = VideoWidget()
        widget._current_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        widget._show_confinement_roi = True

        painter = MagicMock(spec=QPainter)
        widget._draw_confinement_roi(painter, 0, 0, 1.0, 1.0)
        painter.drawRect.assert_called_once()

    def test_draw_confinement_roi_draws_with_default_confinement(self):
        """ROI desenha retângulo com valores padrão de confinement (X-, X+, Y+, Y- em mm)."""
        from config import get_settings

        settings = get_settings(reload=True)
        # Valores padrão: x_positive=200, x_negative=200, y_positive=150, y_negative=150
        settings.preprocess.mm_per_pixel = 1.0

        from ui.widgets.video_widget import VideoWidget

        widget = VideoWidget()
        widget._current_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        widget._show_confinement_roi = True

        painter = MagicMock(spec=QPainter)
        widget._draw_confinement_roi(painter, 0, 0, 1.0, 1.0)
        painter.drawRect.assert_called_once()

# -*- coding: utf-8 -*-
"""Testes unitários para ui.pages.operation_page — mm/px em operação."""

import sys
import pytest
from unittest.mock import MagicMock, patch

# QApplication precisa existir antes de criar widgets Qt
from PySide6.QtWidgets import QApplication

if QApplication.instance() is None:
    _app = QApplication(sys.argv)


class TestOperationPageMmPerPixel:
    """Testes para o controle mm/px na aba Operação."""

    def test_mm_per_pixel_spinbox_exists_and_has_correct_range(self):
        """Verifica que o spinbox mm/px existe com range 0.001–1000."""
        from ui.pages.operation_page import OperationPage

        page = OperationPage()
        assert hasattr(page, "_mm_per_pixel_op")
        assert page._mm_per_pixel_op.minimum() == 0.001
        assert page._mm_per_pixel_op.maximum() == 1000.0

    def test_on_mm_per_pixel_changed_updates_settings(self):
        """Verifica que _on_mm_per_pixel_changed atualiza settings em memória."""
        from config import get_settings

        settings = get_settings(reload=True)
        settings.preprocess.mm_per_pixel = 1.0

        from ui.pages.operation_page import OperationPage

        page = OperationPage()
        page._on_mm_per_pixel_changed(0.25)

        assert page._settings.preprocess.mm_per_pixel == 0.25
        assert get_settings().preprocess.mm_per_pixel == 0.25

    def test_sync_combo_to_settings_syncs_mm_per_pixel(self):
        """Verifica que _sync_combo_to_settings sincroniza mm/px do settings."""
        from config import get_settings

        settings = get_settings(reload=True)
        settings.preprocess.mm_per_pixel = 0.5

        from ui.pages.operation_page import OperationPage

        page = OperationPage()
        page._settings.preprocess.mm_per_pixel = 0.5
        # Bloqueia sinais para setValue não disparar _on_mm_per_pixel_changed
        page._mm_per_pixel_op.blockSignals(True)
        page._mm_per_pixel_op.setValue(1.0)  # valor diferente no widget
        page._mm_per_pixel_op.blockSignals(False)
        page._sync_combo_to_settings()

        assert page._mm_per_pixel_op.value() == 0.5

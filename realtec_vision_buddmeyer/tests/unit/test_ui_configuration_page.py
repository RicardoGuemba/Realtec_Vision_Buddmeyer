# -*- coding: utf-8 -*-
"""Testes unitários para ui.pages.configuration_page — save não bloqueante, showEvent."""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

if QApplication.instance() is None:
    _app = QApplication(sys.argv)


class TestConfigurationPageSaveFeedback:
    """Testes para feedback não bloqueante ao salvar."""

    def test_save_uses_statusbar_when_in_mainwindow(self):
        """Verifica que _save_settings usa statusBar quando widget está em MainWindow."""
        from ui.pages.configuration_page import ConfigurationPage

        page = ConfigurationPage()
        mock_statusbar = MagicMock()
        mock_window = MagicMock()
        mock_window.statusBar.return_value = mock_statusbar
        page.window = MagicMock(return_value=mock_window)

        with patch("config.settings.Settings.to_yaml", MagicMock()):
            page._save_settings()

        mock_statusbar.showMessage.assert_called_once_with(
            "Configurações salvas com sucesso!", 3000
        )

    def test_save_uses_messagebox_when_no_statusbar(self):
        """Verifica fallback para QMessageBox quando não há statusBar."""
        from PySide6.QtWidgets import QMessageBox
        from ui.pages.configuration_page import ConfigurationPage

        page = ConfigurationPage()
        page.window = MagicMock(return_value=None)  # sem janela pai

        with patch("config.settings.Settings.to_yaml", MagicMock()):
            with patch.object(QMessageBox, "information") as mock_info:
                page._save_settings()
                mock_info.assert_called_once()

    def test_show_event_calls_load_settings(self):
        """Verifica que showEvent chama _load_settings ao exibir a aba."""
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QShowEvent
        from ui.pages.configuration_page import ConfigurationPage

        page = ConfigurationPage()
        with patch.object(page, "_load_settings") as mock_load:
            event = QShowEvent()
            page.showEvent(event)
            mock_load.assert_called_once()

    def test_roi_confinement_combo_loads_and_saves(self):
        """Verifica que o combo ROI de confinamento carrega e salva show_roi corretamente."""
        from config import get_settings

        settings = get_settings(reload=True)
        settings.preprocess.confinement.show_roi = True

        from ui.pages.configuration_page import ConfigurationPage

        page = ConfigurationPage()
        assert hasattr(page, "_show_roi_combo")
        assert page._show_roi_combo.count() == 2
        assert page._show_roi_combo.currentIndex() == 0  # Ligado

        settings.preprocess.confinement.show_roi = False
        page._load_settings()
        assert page._show_roi_combo.currentIndex() == 1  # Desligado

        page._show_roi_combo.setCurrentIndex(0)
        with patch("config.settings.Settings.to_yaml", MagicMock()):
            page._save_settings()
        assert settings.preprocess.confinement.show_roi is True

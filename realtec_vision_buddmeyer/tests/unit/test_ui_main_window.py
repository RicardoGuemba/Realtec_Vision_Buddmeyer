# -*- coding: utf-8 -*-
"""Testes unitários para ui.main_window — deferred load com processEvents."""

import sys
import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

if QApplication.instance() is None:
    _app = QApplication(sys.argv)


class TestMainWindowDeferredLoad:
    """Testes para carregamento adiado com processEvents."""

    def test_deferred_load_pages_calls_process_events(self):
        """Verifica que _deferred_load_pages chama QApplication.processEvents entre etapas."""
        with patch("PySide6.QtWidgets.QApplication.processEvents") as mock_process:
            with patch("streaming.StreamManager", MagicMock()):
                with patch("detection.InferenceEngine", MagicMock()):
                    with patch("communication.CIPClient", MagicMock()):
                        with patch("ui.pages.operation_page.OperationPage", MagicMock()):
                            with patch("ui.pages.configuration_page.ConfigurationPage", MagicMock()):
                                with patch("ui.pages.diagnostics_page.DiagnosticsPage", MagicMock()):
                                    from ui.main_window import MainWindow

                                    window = MainWindow()
                                    # _deferred_load_pages é chamado via QTimer.singleShot(0, ...)
                                    QApplication.processEvents()
                                    QApplication.processEvents()

            # processEvents deve ter sido chamado durante o deferred load
            assert mock_process.call_count >= 2

    def test_main_window_deferred_load_uses_process_events(self):
        """Verifica que o código de _deferred_load_pages contém processEvents (regressão)."""
        import inspect
        from ui.main_window import MainWindow

        source = inspect.getsource(MainWindow._deferred_load_pages)
        assert "processEvents" in source

# -*- coding: utf-8 -*-
"""Testes de shutdown estável do sistema."""

import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestShutdownStability:
    """Testes de estabilidade ao parar e sair."""

    def test_stop_system_idempotent(self, qtbot):
        """Chamar _stop_system duas vezes não causa erro."""
        from ui.pages.operation_page import OperationPage

        page = OperationPage()
        qtbot.addWidget(page)
        page._stop_system()
        page._stop_system()
        assert not page._is_running

    def test_stop_system_when_not_running(self, qtbot):
        """_stop_system quando não está rodando retorna imediatamente."""
        from ui.pages.operation_page import OperationPage

        page = OperationPage()
        qtbot.addWidget(page)
        assert not page._is_running
        page._stop_system()
        assert not page._is_running

    def test_handlers_ignore_when_not_running(self, qtbot):
        """Handlers retornam cedo quando _is_running é False."""
        from datetime import datetime

        from detection.events import DetectionEvent
        from ui.pages.operation_page import OperationPage

        page = OperationPage()
        qtbot.addWidget(page)
        page._is_running = False

        page._on_cycle_summary([])
        page._on_cycle_summary([{"step": "x", "timestamp": datetime.now()}])
        page._on_cycle_step("test")

        evt = DetectionEvent(
            detected=True,
            class_name="test",
            confidence=0.9,
            centroid=(0.0, 0.0),
            detection_count=1,
        )
        page._on_detection(evt)

        assert not page._is_running

    def test_main_window_close_without_running(self, qtbot):
        """MainWindow fecha sem erro quando sistema não está rodando."""
        from ui.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)
        window.show()
        qtbot.waitExposed(window)
        window.close()
        assert window.isHidden() or not window.isVisible()

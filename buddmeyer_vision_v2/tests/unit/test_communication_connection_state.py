# -*- coding: utf-8 -*-
"""Testes unitários para communication.connection_state."""

import pytest
from datetime import datetime

from communication.connection_state import ConnectionStatus, ConnectionState


class TestConnectionStatus:
    """Testes para ConnectionStatus."""

    def test_values(self):
        assert ConnectionStatus.DISCONNECTED.value == "disconnected"
        assert ConnectionStatus.CONNECTED.value == "connected"
        assert ConnectionStatus.SIMULATED.value == "simulated"


class TestConnectionState:
    """Testes para ConnectionState."""

    def test_is_connected_false_when_disconnected(self):
        s = ConnectionState(status=ConnectionStatus.DISCONNECTED, ip="1.2.3.4", port=44818)
        assert not s.is_connected

    def test_is_connected_true_when_connected(self):
        s = ConnectionState(status=ConnectionStatus.CONNECTED, ip="1.2.3.4", port=44818)
        assert s.is_connected

    def test_is_connected_true_when_simulated(self):
        s = ConnectionState(status=ConnectionStatus.SIMULATED, ip="1.2.3.4", port=44818)
        assert s.is_connected

    def test_is_healthy_only_when_connected_no_errors(self):
        s = ConnectionState(status=ConnectionStatus.CONNECTED, ip="1.2.3.4", port=44818, error_count=0)
        assert s.is_healthy

    def test_is_healthy_false_when_errors(self):
        s = ConnectionState(status=ConnectionStatus.CONNECTED, ip="1.2.3.4", port=44818, error_count=1)
        assert not s.is_healthy

    def test_to_dict(self):
        s = ConnectionState(status=ConnectionStatus.CONNECTED, ip="192.168.1.10", port=44818)
        d = s.to_dict()
        assert d["status"] == "connected"
        assert d["ip"] == "192.168.1.10"
        assert d["port"] == 44818
        assert "is_connected" in d
        assert "is_healthy" in d

# -*- coding: utf-8 -*-
"""Testes unitários para core.windows_startup."""

import sys
import pytest

from core.windows_startup import is_windows, is_auto_start_enabled, set_auto_start


class TestWindowsStartup:
    """Testes para o módulo windows_startup."""

    def test_is_windows_on_win32(self):
        """Verifica is_windows() em ambiente Windows."""
        if sys.platform == "win32":
            assert is_windows() is True
        else:
            assert is_windows() is False

    def test_set_auto_start_disable_idempotent(self):
        """Desabilitar auto-start deve ser idempotente (não falhar se já desabilitado)."""
        result = set_auto_start(False)
        assert result is True

    def test_is_auto_start_enabled_returns_bool(self):
        """is_auto_start_enabled deve retornar bool."""
        result = is_auto_start_enabled()
        assert isinstance(result, bool)

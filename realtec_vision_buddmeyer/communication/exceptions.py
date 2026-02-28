# -*- coding: utf-8 -*-
"""
Exceções específicas para comunicação CIP.
"""

from core.exceptions import CIPError


class CIPConnectionError(CIPError):
    """Erro de conexão CIP."""
    pass


class CIPTimeoutError(CIPError):
    """Timeout na comunicação CIP."""
    pass


class CIPTagError(CIPError):
    """Erro ao acessar TAG CIP."""
    pass


class CIPWriteError(CIPError):
    """Erro ao escrever TAG."""
    pass


class CIPReadError(CIPError):
    """Erro ao ler TAG."""
    pass

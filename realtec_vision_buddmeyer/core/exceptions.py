# -*- coding: utf-8 -*-
"""
Exceções customizadas do sistema Buddmeyer Vision v2.0
"""


class BuddmeyerVisionError(Exception):
    """Exceção base do sistema."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class ConfigurationError(BuddmeyerVisionError):
    """Erro de configuração do sistema."""
    pass


class StreamError(BuddmeyerVisionError):
    """Erro relacionado ao streaming de vídeo."""
    pass


class StreamSourceError(StreamError):
    """Erro ao acessar fonte de stream."""
    pass


class StreamTimeoutError(StreamError):
    """Timeout ao aguardar frame do stream."""
    pass


class DetectionError(BuddmeyerVisionError):
    """Erro relacionado à detecção de objetos."""
    pass


class ModelLoadError(DetectionError):
    """Erro ao carregar modelo de ML."""
    pass


class InferenceError(DetectionError):
    """Erro durante inferência."""
    pass


class CIPError(BuddmeyerVisionError):
    """Erro relacionado à comunicação CIP."""
    pass


class CIPConnectionError(CIPError):
    """Erro de conexão CIP."""
    pass


class CIPTimeoutError(CIPError):
    """Timeout na comunicação CIP."""
    pass


class CIPTagError(CIPError):
    """Erro ao acessar TAG CIP."""
    pass


class RobotControlError(BuddmeyerVisionError):
    """Erro no controle do robô."""
    pass


class StateTransitionError(RobotControlError):
    """Erro em transição de estado da máquina de estados."""
    pass

# -*- coding: utf-8 -*-
"""
Estado da conexão CIP.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ConnectionStatus(str, Enum):
    """Status da conexão CIP."""
    
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DEGRADED = "degraded"  # Conectado mas com erros
    SIMULATED = "simulated"
    ERROR = "error"


@dataclass
class ConnectionState:
    """Estado completo da conexão."""
    
    status: ConnectionStatus
    ip: str
    port: int
    last_connected: Optional[datetime] = None
    last_error: Optional[str] = None
    error_count: int = 0
    reconnect_attempts: int = 0
    is_simulated: bool = False
    
    @property
    def is_connected(self) -> bool:
        """Verifica se está conectado."""
        return self.status in (ConnectionStatus.CONNECTED, ConnectionStatus.SIMULATED)
    
    @property
    def is_healthy(self) -> bool:
        """Verifica se conexão está saudável."""
        return self.status == ConnectionStatus.CONNECTED and self.error_count == 0
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "status": self.status.value,
            "ip": self.ip,
            "port": self.port,
            "last_connected": self.last_connected.isoformat() if self.last_connected else None,
            "last_error": self.last_error,
            "error_count": self.error_count,
            "reconnect_attempts": self.reconnect_attempts,
            "is_simulated": self.is_simulated,
            "is_connected": self.is_connected,
            "is_healthy": self.is_healthy,
        }

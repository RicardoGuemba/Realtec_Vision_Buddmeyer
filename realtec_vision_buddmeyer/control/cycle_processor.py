# -*- coding: utf-8 -*-
"""
Processador de ciclos de produção.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import deque
from threading import Lock

from PySide6.QtCore import QObject, Signal

from core.logger import get_logger
from core.metrics import MetricsCollector
from detection.events import DetectionEvent

logger = get_logger("control.cycle")


@dataclass
class CycleRecord:
    """Registro de um ciclo de produção."""
    
    cycle_number: int
    start_time: datetime
    end_time: Optional[datetime] = None
    detection_event: Optional[DetectionEvent] = None
    success: bool = False
    error: Optional[str] = None
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Duração do ciclo."""
        if self.end_time is None:
            return None
        return self.end_time - self.start_time
    
    @property
    def duration_seconds(self) -> float:
        """Duração em segundos."""
        duration = self.duration
        return duration.total_seconds() if duration else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_number": self.cycle_number,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "error": self.error,
            "detection": self.detection_event.to_dict() if self.detection_event else None,
        }


class CycleProcessor(QObject):
    """
    Processador de ciclos de produção.
    
    Mantém histórico de ciclos e calcula estatísticas.
    
    Signals:
        cycle_started: Emitido quando ciclo inicia
        cycle_completed: Emitido quando ciclo completa
        stats_updated: Emitido quando estatísticas são atualizadas
    """
    
    cycle_started = Signal(int)  # Número do ciclo
    cycle_completed = Signal(object)  # CycleRecord
    stats_updated = Signal(dict)
    
    def __init__(self, max_history: int = 1000):
        super().__init__()
        
        self._metrics = MetricsCollector()
        self._lock = Lock()
        
        self._history: deque = deque(maxlen=max_history)
        self._current_cycle: Optional[CycleRecord] = None
        self._cycle_count = 0
        self._success_count = 0
        self._error_count = 0
        
        # Estatísticas de tempo
        self._cycle_times: deque = deque(maxlen=100)
    
    def start_cycle(self) -> int:
        """
        Inicia um novo ciclo.
        
        Returns:
            Número do ciclo
        """
        with self._lock:
            self._cycle_count += 1
            cycle_number = self._cycle_count
            
            self._current_cycle = CycleRecord(
                cycle_number=cycle_number,
                start_time=datetime.now(),
            )
        
        logger.info("cycle_started", cycle_number=cycle_number)
        self.cycle_started.emit(cycle_number)
        
        return cycle_number
    
    def complete_cycle(
        self,
        success: bool = True,
        detection_event: Optional[DetectionEvent] = None,
        error: Optional[str] = None,
    ) -> Optional[CycleRecord]:
        """
        Completa o ciclo atual.
        
        Args:
            success: Se o ciclo foi bem sucedido
            detection_event: Evento de detecção do ciclo
            error: Mensagem de erro (se houver)
        
        Returns:
            Registro do ciclo completado
        """
        with self._lock:
            if self._current_cycle is None:
                logger.warning("no_active_cycle_to_complete")
                return None
            
            cycle = self._current_cycle
            cycle.end_time = datetime.now()
            cycle.success = success
            cycle.detection_event = detection_event
            cycle.error = error
            
            # Atualiza estatísticas
            if success:
                self._success_count += 1
            else:
                self._error_count += 1
            
            # Registra tempo do ciclo
            if cycle.duration_seconds > 0:
                self._cycle_times.append(cycle.duration_seconds)
                self._metrics.record("cycle_time", cycle.duration_seconds * 1000)
            
            # Adiciona ao histórico
            self._history.append(cycle)
            self._current_cycle = None
        
        logger.info(
            "cycle_completed",
            cycle_number=cycle.cycle_number,
            success=success,
            duration=cycle.duration_seconds,
        )
        
        self.cycle_completed.emit(cycle)
        self._emit_stats()
        
        return cycle
    
    def cancel_cycle(self, reason: str = "cancelled") -> None:
        """Cancela o ciclo atual."""
        self.complete_cycle(success=False, error=reason)
    
    def get_current_cycle(self) -> Optional[CycleRecord]:
        """Retorna o ciclo atual."""
        return self._current_cycle
    
    def get_history(self, count: int = 100) -> List[CycleRecord]:
        """Retorna histórico de ciclos."""
        with self._lock:
            return list(self._history)[-count:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de produção."""
        with self._lock:
            total = self._cycle_count
            success_rate = (self._success_count / total * 100) if total > 0 else 0
            
            avg_time = 0.0
            min_time = 0.0
            max_time = 0.0
            
            if self._cycle_times:
                times = list(self._cycle_times)
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
            
            return {
                "total_cycles": total,
                "success_count": self._success_count,
                "error_count": self._error_count,
                "success_rate": success_rate,
                "avg_cycle_time": avg_time,
                "min_cycle_time": min_time,
                "max_cycle_time": max_time,
                "cycles_per_minute": self._calculate_cpm(),
            }
    
    def _calculate_cpm(self) -> float:
        """Calcula ciclos por minuto."""
        if len(self._history) < 2:
            return 0.0
        
        with self._lock:
            recent = list(self._history)[-10:]
        
        if len(recent) < 2:
            return 0.0
        
        first = recent[0].start_time
        last = recent[-1].end_time or datetime.now()
        
        elapsed_minutes = (last - first).total_seconds() / 60
        
        if elapsed_minutes <= 0:
            return 0.0
        
        return len(recent) / elapsed_minutes
    
    def _emit_stats(self) -> None:
        """Emite estatísticas atualizadas."""
        stats = self.get_stats()
        self.stats_updated.emit(stats)
    
    def reset(self) -> None:
        """Reseta todas as estatísticas."""
        with self._lock:
            self._history.clear()
            self._current_cycle = None
            self._cycle_count = 0
            self._success_count = 0
            self._error_count = 0
            self._cycle_times.clear()
        
        logger.info("cycle_processor_reset")
        self._emit_stats()
    
    @property
    def cycle_count(self) -> int:
        """Retorna contagem total de ciclos."""
        return self._cycle_count
    
    @property
    def is_cycle_active(self) -> bool:
        """Verifica se há ciclo ativo."""
        return self._current_cycle is not None

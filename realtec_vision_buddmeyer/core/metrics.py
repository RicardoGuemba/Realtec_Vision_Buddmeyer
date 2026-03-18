# -*- coding: utf-8 -*-
"""
Sistema de coleta e armazenamento de métricas.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional, Deque

from PySide6.QtCore import QObject, Signal


@dataclass
class MetricPoint:
    """Ponto de métrica com timestamp."""
    
    timestamp: datetime
    value: float


@dataclass
class MetricSeries:
    """Série temporal de métricas."""
    
    name: str
    unit: str
    max_points: int = 300  # ~5 minutos a 1 ponto/segundo
    points: Deque[MetricPoint] = field(default_factory=lambda: deque(maxlen=300))
    
    def add(self, value: float) -> None:
        """Adiciona um ponto à série."""
        self.points.append(MetricPoint(datetime.now(), value))
    
    @property
    def last_value(self) -> Optional[float]:
        """Retorna o último valor."""
        return self.points[-1].value if self.points else None
    
    @property
    def average(self) -> Optional[float]:
        """Retorna a média dos valores."""
        if not self.points:
            return None
        return sum(p.value for p in self.points) / len(self.points)
    
    @property
    def min_value(self) -> Optional[float]:
        """Retorna o valor mínimo."""
        return min(p.value for p in self.points) if self.points else None
    
    @property
    def max_value(self) -> Optional[float]:
        """Retorna o valor máximo."""
        return max(p.value for p in self.points) if self.points else None
    
    def get_recent(self, count: int = 60) -> List[MetricPoint]:
        """Retorna os últimos N pontos."""
        return list(self.points)[-count:]


class MetricsCollector(QObject):
    """
    Coletor central de métricas do sistema.
    
    Signals:
        metric_updated: Emitido quando uma métrica é atualizada
    """
    
    metric_updated = Signal(str, float)  # nome, valor
    
    _instance: Optional["MetricsCollector"] = None
    _lock = Lock()
    
    def __new__(cls) -> "MetricsCollector":
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        
        super().__init__()
        self._initialized = True
        self._series: Dict[str, MetricSeries] = {}
        self._counters: Dict[str, int] = {}
        self._timers: Dict[str, float] = {}
        self._lock = Lock()
        
        # Criar séries padrão
        self._init_default_series()
    
    def _init_default_series(self) -> None:
        """Inicializa séries de métricas padrão."""
        default_series = [
            ("stream_fps", "fps"),
            ("inference_fps", "fps"),
            ("inference_time", "ms"),
            ("detection_count", "count"),
            ("detection_confidence", "%"),
            ("cip_response_time", "ms"),
            ("cip_errors", "count"),
            ("cpu_usage", "%"),
            ("memory_usage", "MB"),
            ("gpu_usage", "%"),
        ]
        
        for name, unit in default_series:
            self._series[name] = MetricSeries(name=name, unit=unit)
    
    def record(self, name: str, value: float, unit: str = "") -> None:
        """
        Registra um valor de métrica.
        
        Args:
            name: Nome da métrica
            value: Valor
            unit: Unidade (opcional, usado apenas na criação)
        """
        with self._lock:
            if name not in self._series:
                self._series[name] = MetricSeries(name=name, unit=unit)
            
            self._series[name].add(value)
        
        self.metric_updated.emit(name, value)
    
    def increment(self, name: str, amount: int = 1) -> int:
        """
        Incrementa um contador.
        
        Args:
            name: Nome do contador
            amount: Quantidade a incrementar
        
        Returns:
            Novo valor do contador
        """
        with self._lock:
            if name not in self._counters:
                self._counters[name] = 0
            
            self._counters[name] += amount
            return self._counters[name]
    
    def get_counter(self, name: str) -> int:
        """Retorna o valor de um contador."""
        return self._counters.get(name, 0)
    
    def reset_counter(self, name: str) -> None:
        """Reseta um contador para zero."""
        with self._lock:
            self._counters[name] = 0
    
    def start_timer(self, name: str) -> None:
        """Inicia um timer."""
        self._timers[name] = time.perf_counter()
    
    def stop_timer(self, name: str) -> float:
        """
        Para um timer e retorna o tempo decorrido em ms.
        
        Args:
            name: Nome do timer
        
        Returns:
            Tempo decorrido em milissegundos
        """
        if name not in self._timers:
            return 0.0
        
        elapsed = (time.perf_counter() - self._timers[name]) * 1000
        del self._timers[name]
        return elapsed
    
    def get_series(self, name: str) -> Optional[MetricSeries]:
        """Retorna uma série de métricas."""
        return self._series.get(name)
    
    def get_last_value(self, name: str) -> Optional[float]:
        """Retorna o último valor de uma métrica."""
        series = self._series.get(name)
        return series.last_value if series else None
    
    def get_stats(self, name: str) -> Dict[str, Optional[float]]:
        """
        Retorna estatísticas de uma métrica.
        
        Returns:
            Dict com last, avg, min, max
        """
        series = self._series.get(name)
        if not series:
            return {"last": None, "avg": None, "min": None, "max": None}
        
        return {
            "last": series.last_value,
            "avg": series.average,
            "min": series.min_value,
            "max": series.max_value,
        }
    
    def get_all_metrics(self) -> Dict[str, Dict]:
        """Retorna todas as métricas atuais."""
        result = {}
        
        with self._lock:
            for name, series in self._series.items():
                result[name] = {
                    "value": series.last_value,
                    "unit": series.unit,
                    "stats": self.get_stats(name),
                }
            
            for name, value in self._counters.items():
                result[f"counter_{name}"] = {
                    "value": value,
                    "unit": "count",
                }
        
        return result
    
    def reset_all(self) -> None:
        """Reseta todas as métricas."""
        with self._lock:
            self._series.clear()
            self._counters.clear()
            self._timers.clear()
            self._init_default_series()


# Funções de conveniência
def get_metrics() -> MetricsCollector:
    """Retorna a instância do coletor de métricas."""
    return MetricsCollector()


def record_metric(name: str, value: float, unit: str = "") -> None:
    """Registra um valor de métrica."""
    MetricsCollector().record(name, value, unit)


def increment_counter(name: str, amount: int = 1) -> int:
    """Incrementa um contador."""
    return MetricsCollector().increment(name, amount)

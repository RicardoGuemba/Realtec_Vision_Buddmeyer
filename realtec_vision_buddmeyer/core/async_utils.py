# -*- coding: utf-8 -*-
"""
Utilitários para execução assíncrona em ambiente Qt/qasync.

Garante que tarefas assíncronas só sejam agendadas quando o event loop
está ativo, evitando RuntimeError durante encerramento da aplicação.
"""

import asyncio
from typing import Optional, Coroutine, Any

from .logger import get_logger

logger = get_logger("core.async_utils")


def safe_create_task(coro: Coroutine[Any, Any, Any], name: Optional[str] = None) -> Optional[asyncio.Task]:
    """
    Agenda uma coroutine no event loop atual apenas se o loop estiver rodando.
    
    Uso típico em supervisório: sinais Qt disparam lógica async (PLC, robô).
    Durante o shutdown o loop pode estar fechando; criar task nesse momento
    gera RuntimeError. Esta função evita o crash e registra em log.
    
    Args:
        coro: Coroutine a executar (ex.: connect(), write_tag()).
        name: Nome opcional para o task (debug).
    
    Returns:
        Task criado ou None se não foi possível agendar.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            logger.debug("event_loop_closed_skipping_task", name=name)
            return None
        if not loop.is_running():
            logger.debug("event_loop_not_running_skipping_task", name=name)
            return None
        task = loop.create_task(coro)
        if name:
            task.set_name(name)
        return task
    except RuntimeError as e:
        logger.debug("create_task_runtime_error", error=str(e), name=name)
        return None
    except Exception as e:
        logger.warning("create_task_unexpected_error", error=str(e), name=name)
        return None

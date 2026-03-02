# -*- coding: utf-8 -*-
"""
Configuração de inicialização automática no Windows.

Permite adicionar/remover o sistema da pasta Inicialização do Windows,
para que o aplicativo seja iniciado automaticamente após login quando
o PC reiniciar (ex.: após falta de energia).

Usa a pasta Inicialização do usuário (sem privilégios de admin).
"""

import os
import sys
from pathlib import Path
from typing import Optional

from core.logger import get_logger

logger = get_logger("core.startup")

# Nome do arquivo na pasta Inicialização
STARTUP_FILENAME = "RealtecVisionBuddmeyer_Iniciar.bat"


def _get_project_root() -> Path:
    """Retorna o diretório raiz do projeto (contém venv e realtec_vision_buddmeyer)."""
    # main.py está em realtec_vision_buddmeyer/
    main_py = Path(__file__).resolve().parent.parent / "main.py"
    return main_py.parent.parent


def _get_startup_folder() -> Path:
    """Retorna o caminho da pasta Inicialização do usuário no Windows."""
    startup = os.environ.get("APPDATA", "")
    if not startup:
        return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return Path(startup) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _get_startup_bat_path() -> Path:
    """Retorna o caminho completo do arquivo .bat na pasta Inicialização."""
    return _get_startup_folder() / STARTUP_FILENAME


def is_windows() -> bool:
    """Verifica se o sistema operacional é Windows."""
    return sys.platform == "win32"


def is_auto_start_enabled() -> bool:
    """
    Verifica se o auto-início está habilitado.
    
    Returns:
        True se o arquivo de inicialização existe na pasta Startup.
    """
    if not is_windows():
        return False
    return _get_startup_bat_path().exists()


def enable_auto_start() -> bool:
    """
    Habilita o auto-início: cria arquivo .bat na pasta Inicialização.
    
    Returns:
        True se sucesso, False em caso de erro.
    """
    if not is_windows():
        logger.warning("auto_start_only_windows")
        return False
    
    project_root = _get_project_root()
    main_py = project_root / "realtec_vision_buddmeyer" / "main.py"
    venv_python = project_root / "venv" / "Scripts" / "python.exe"
    
    # Usa venv se existir, senão sys.executable
    if venv_python.exists():
        python_exe = str(venv_python)
    else:
        python_exe = sys.executable
    
    if not main_py.exists():
        logger.error("auto_start_main_not_found", path=str(main_py))
        return False
    
    bat_content = f'''@echo off
title Realtec Vision Buddmeyer - Auto-inicio
cd /d "{project_root}"
"{python_exe}" "{main_py}"
'''
    
    try:
        startup_folder = _get_startup_folder()
        startup_folder.mkdir(parents=True, exist_ok=True)
        bat_path = _get_startup_bat_path()
        bat_path.write_text(bat_content, encoding="utf-8")
        logger.info("auto_start_enabled", path=str(bat_path))
        return True
    except Exception as e:
        logger.error("auto_start_enable_failed", error=str(e))
        return False


def disable_auto_start() -> bool:
    """
    Desabilita o auto-início: remove o arquivo da pasta Inicialização.
    
    Returns:
        True se sucesso, False em caso de erro.
    """
    if not is_windows():
        return False
    
    bat_path = _get_startup_bat_path()
    try:
        if bat_path.exists():
            bat_path.unlink()
            logger.info("auto_start_disabled", path=str(bat_path))
        return True
    except Exception as e:
        logger.error("auto_start_disable_failed", error=str(e))
        return False


def set_auto_start(enabled: bool) -> bool:
    """
    Define o estado do auto-início.
    
    Args:
        enabled: True para habilitar, False para desabilitar.
    
    Returns:
        True se a operação foi bem-sucedida.
    """
    if enabled:
        return enable_auto_start()
    return disable_auto_start()

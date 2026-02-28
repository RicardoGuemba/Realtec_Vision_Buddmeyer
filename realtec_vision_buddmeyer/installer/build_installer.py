#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para construir o instalador .exe usando PyInstaller.
"""

import subprocess
import sys
from pathlib import Path

def build_installer():
    """Constrói o instalador .exe."""
    
    installer_dir = Path(__file__).parent
    install_script = installer_dir / "install.py"
    
    print("Construindo instalador .exe...")
    print("Isso pode levar alguns minutos...\n")
    
    # Adiciona dados do projeto
    project_dir = installer_dir.parent
    add_data = f"{project_dir};realtec_vision_buddmeyer"
    
    # Comando PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=BuddmeyerVisionInstaller",
        "--onefile",
        "--console",  # Com console para ver progresso
        "--clean",
        "--noconfirm",
        f"--add-data={add_data}",
        str(install_script)
    ]
    
    # Adiciona ícone se existir
    icon_file = installer_dir / "icon.ico"
    if icon_file.exists():
        cmd.extend(["--icon", str(icon_file)])
    
    try:
        subprocess.run(cmd, check=True)
        print("\n[OK] Instalador criado com sucesso!")
        print("Arquivo: dist/BuddmeyerVisionInstaller.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERRO] Erro ao criar instalador: {e}")
        return 1
    except FileNotFoundError:
        print("\n[ERRO] PyInstaller nao encontrado!")
        print("Instale com: pip install pyinstaller")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(build_installer())

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para construir o instalador completo .exe usando PyInstaller.
Inclui modelos e vídeos no pacote.
"""

import subprocess
import sys
import shutil
from pathlib import Path

def build_installer():
    """Constrói o instalador .exe completo."""
    
    installer_dir = Path(__file__).parent
    install_script = installer_dir / "install_complete.py"
    project_root = installer_dir.parent.parent
    project_dir = project_root / "realtec_vision_buddmeyer"
    
    print("=" * 70)
    print("CONSTRUINDO INSTALADOR COMPLETO - BUDDMEYER VISION v2.0")
    print("=" * 70)
    print("\nEste processo pode levar vários minutos...\n")
    
    # Verifica se PyInstaller está instalado
    try:
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            check=True,
            capture_output=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ERRO] PyInstaller não encontrado!")
        print("Instale com: pip install pyinstaller")
        return 1
    
    # Cria diretório temporário para dados
    temp_data_dir = installer_dir / "temp_data"
    if temp_data_dir.exists():
        shutil.rmtree(temp_data_dir)
    temp_data_dir.mkdir()
    
    # Copia modelos para diretório temporário
    models_source = project_dir / "models"
    models_temp = temp_data_dir / "models"
    if models_source.exists():
        print("[INFO] Copiando modelos...")
        shutil.copytree(models_source, models_temp)
        print("[OK] Modelos copiados")
    
    # Copia vídeos para diretório temporário
    videos_source = project_dir / "videos"
    videos_temp = temp_data_dir / "videos"
    if videos_source.exists():
        print("[INFO] Copiando vídeos...")
        shutil.copytree(videos_source, videos_temp)
        print("[OK] Vídeos copiados")
    
    # Copia projeto completo (sem venv, cache, etc)
    project_temp = temp_data_dir / "realtec_vision_buddmeyer"
    print("[INFO] Copiando projeto...")
    
    # Ignora padrões
    ignore_patterns = shutil.ignore_patterns(
        '__pycache__', '*.pyc', '*.pyo', '.pytest_cache',
        '*.log', 'venv', '.git', 'dist', 'build', '*.egg-info',
        '.cursor', '.vscode', '*.md', '*.txt'
    )
    
    shutil.copytree(project_dir, project_temp, ignore=ignore_patterns)
    print("[OK] Projeto copiado")
    
    # Prepara dados para PyInstaller
    add_data_args = []
    
    # Adiciona modelos
    if models_temp.exists():
        add_data_args.append(f"{models_temp};realtec_vision_buddmeyer/models")
    
    # Adiciona vídeos
    if videos_temp.exists():
        add_data_args.append(f"{videos_temp};realtec_vision_buddmeyer/videos")
    
    # Adiciona projeto
    add_data_args.append(f"{project_temp};realtec_vision_buddmeyer")
    
    # Comando PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=BuddmeyerVisionInstallerCompleto",
        "--onefile",
        "--console",  # Com console para ver progresso
        "--clean",
        "--noconfirm",
        "--noupx",  # Desabilita UPX para evitar problemas
    ]
    
    # Adiciona dados
    for add_data in add_data_args:
        cmd.append(f"--add-data={add_data}")
    
    # Adiciona script de instalação
    cmd.append(str(install_script))
    
    # Adiciona ícone se existir
    icon_file = installer_dir / "icon.ico"
    if icon_file.exists():
        cmd.extend(["--icon", str(icon_file)])
    
    print("\n[INFO] Executando PyInstaller...")
    print(f"[INFO] Comando: {' '.join(cmd[:5])} ...")
    
    try:
        result = subprocess.run(cmd, check=True)
        
        # Limpa diretório temporário
        if temp_data_dir.exists():
            shutil.rmtree(temp_data_dir)
        
        print("\n" + "=" * 70)
        print("[OK] INSTALADOR CRIADO COM SUCESSO!")
        print("=" * 70)
        print(f"\nArquivo: {installer_dir / 'dist' / 'BuddmeyerVisionInstallerCompleto.exe'}")
        print(f"Tamanho aproximado: ~50-100 MB")
        print("\nO instalador inclui:")
        print("  - Todas as dependências Python")
        print("  - Modelos de detecção")
        print("  - Vídeos de exemplo")
        print("  - Código fonte completo")
        print("\nPara distribuir, envie apenas o arquivo .exe")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n[ERRO] Erro ao criar instalador: {e}")
        # Limpa diretório temporário mesmo em caso de erro
        if temp_data_dir.exists():
            shutil.rmtree(temp_data_dir)
        return 1

if __name__ == "__main__":
    sys.exit(build_installer())

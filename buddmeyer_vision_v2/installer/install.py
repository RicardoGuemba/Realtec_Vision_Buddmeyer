#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Instalador do Buddmeyer Vision System v2.0
Instala Python, dependências e configura o sistema.
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path
import platform

# Cores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Imprime cabeçalho."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text):
    """Imprime mensagem de sucesso."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    """Imprime mensagem de erro."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text):
    """Imprime mensagem de aviso."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text):
    """Imprime informação."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")

def check_python():
    """Verifica se Python está instalado."""
    print_info("Verificando instalação do Python...")
    
    try:
        version = sys.version_info
        if version.major >= 3 and version.minor >= 10:
            print_success(f"Python {version.major}.{version.minor}.{version.micro} encontrado")
            return True
        else:
            print_error(f"Python {version.major}.{version.minor} encontrado, mas requer Python 3.10+")
            return False
    except Exception as e:
        print_error(f"Erro ao verificar Python: {e}")
        return False

def check_pip():
    """Verifica se pip está disponível."""
    print_info("Verificando pip...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success("pip disponível")
            return True
        else:
            print_error("pip não encontrado")
            return False
    except Exception as e:
        print_error(f"Erro ao verificar pip: {e}")
        return False

def create_venv(project_dir):
    """Cria ambiente virtual."""
    print_info("Criando ambiente virtual...")
    
    venv_path = project_dir / "venv"
    
    if venv_path.exists():
        print_warning("Ambiente virtual já existe. Removendo...")
        shutil.rmtree(venv_path)
    
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            cwd=project_dir
        )
        print_success("Ambiente virtual criado")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao criar ambiente virtual: {e}")
        return False

def upgrade_pip(venv_python):
    """Atualiza pip no ambiente virtual."""
    print_info("Atualizando pip...")
    
    try:
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True
        )
        print_success("pip atualizado")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao atualizar pip: {e}")
        return False

def install_dependencies(venv_python, requirements_file):
    """Instala dependências."""
    print_info("Instalando dependências...")
    print_info("Isso pode levar vários minutos...")
    
    # Instala dependências básicas primeiro
    basic_deps = [
        "PySide6",
        "pydantic",
        "pydantic-settings",
        "pyyaml",
        "opencv-python",
        "Pillow",
        "numpy",
        "structlog",
        "colorama",
        "qasync",
    ]
    
    print_info("Instalando dependências básicas...")
    try:
        subprocess.run(
            [str(venv_python), "-m", "pip", "install"] + basic_deps,
            check=True,
            capture_output=True
        )
        print_success("Dependências básicas instaladas")
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao instalar dependências básicas: {e}")
        return False
    
    # Instala PyTorch com CUDA
    print_info("Instalando PyTorch com suporte CUDA...")
    try:
        subprocess.run(
            [
                str(venv_python), "-m", "pip", "install",
                "torch", "torchvision",
                "--index-url", "https://download.pytorch.org/whl/cu118"
            ],
            check=True,
            capture_output=True
        )
        print_success("PyTorch instalado")
    except subprocess.CalledProcessError as e:
        print_warning(f"Erro ao instalar PyTorch com CUDA, tentando CPU...")
        try:
            subprocess.run(
                [str(venv_python), "-m", "pip", "install", "torch", "torchvision"],
                check=True,
                capture_output=True
            )
            print_success("PyTorch (CPU) instalado")
        except subprocess.CalledProcessError:
            print_error("Erro ao instalar PyTorch")
            return False
    
    # Instala bibliotecas ML
    print_info("Instalando bibliotecas de Machine Learning...")
    ml_deps = [
        "transformers",
        "accelerate",
        "safetensors",
        "aphyt",
    ]
    
    try:
        subprocess.run(
            [str(venv_python), "-m", "pip", "install"] + ml_deps,
            check=True,
            capture_output=True
        )
        print_success("Bibliotecas ML instaladas")
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao instalar bibliotecas ML: {e}")
        return False
    
    return True

def create_start_scripts(project_dir, venv_python):
    """Cria scripts de inicialização."""
    print_info("Criando scripts de inicialização...")
    
    # Script BAT
    bat_content = f"""@echo off
title Buddmeyer Vision System v2.0
cd /d "{project_dir}"
call venv\\Scripts\\activate.bat
python buddmeyer_vision_v2\\main.py
pause
"""
    
    bat_file = project_dir / "Iniciar_Buddmeyer_Vision.bat"
    with open(bat_file, "w", encoding="utf-8") as f:
        f.write(bat_content)
    print_success(f"Script criado: {bat_file.name}")
    
    # Script PowerShell
    ps_content = f"""# Buddmeyer Vision System v2.0
$ErrorActionPreference = "Stop"
Set-Location "{project_dir}"
& "{project_dir}\\venv\\Scripts\\Activate.ps1"
python "{project_dir}\\buddmeyer_vision_v2\\main.py"
"""
    
    ps_file = project_dir / "Iniciar_Buddmeyer_Vision.ps1"
    with open(ps_file, "w", encoding="utf-8") as f:
        f.write(ps_content)
    print_success(f"Script criado: {ps_file.name}")
    
    return True

def verify_installation(venv_python):
    """Verifica se a instalação foi bem-sucedida."""
    print_info("Verificando instalação...")
    
    packages = [
        "PySide6",
        "torch",
        "transformers",
        "opencv-python",
        "aphyt",
    ]
    
    all_ok = True
    for package in packages:
        try:
            result = subprocess.run(
                [str(venv_python), "-m", "pip", "show", package],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print_success(f"{package} instalado")
            else:
                print_error(f"{package} não encontrado")
                all_ok = False
        except Exception as e:
            print_error(f"Erro ao verificar {package}: {e}")
            all_ok = False
    
    return all_ok

def main():
    """Função principal do instalador."""
    print_header("BUDDMEYER VISION SYSTEM v2.0 - INSTALADOR")
    
    print_info(f"Sistema Operacional: {platform.system()} {platform.release()}")
    print_info(f"Arquitetura: {platform.machine()}")
    
    # Determina diretório de instalação
    if len(sys.argv) > 1:
        install_dir = Path(sys.argv[1])
    else:
        install_dir = Path.home() / "BuddmeyerVision"
    
    print_info(f"Diretório de instalação: {install_dir}")
    
    # Verifica Python
    if not check_python():
        print_error("\nPython 3.10+ é necessário!")
        print_info("Baixe em: https://www.python.org/downloads/")
        input("\nPressione Enter para sair...")
        return 1
    
    if not check_pip():
        print_error("\npip é necessário!")
        input("\nPressione Enter para sair...")
        return 1
    
    # Cria diretório de instalação
    print_info(f"Criando diretório: {install_dir}")
    install_dir.mkdir(parents=True, exist_ok=True)
    
    # Copia arquivos do projeto
    print_info("Copiando arquivos do projeto...")
    
    # Determina diretório fonte
    # Se executado como .exe, os arquivos estarão em _MEIPASS
    if hasattr(sys, '_MEIPASS'):
        # Modo executável - arquivos estão no diretório temporário
        source_dir = Path(sys._MEIPASS) / "buddmeyer_vision_v2"
    else:
        # Modo desenvolvimento
        source_dir = Path(__file__).parent.parent
    
    if not source_dir.exists():
        print_error(f"Diretório fonte não encontrado: {source_dir}")
        print_info("Tentando localizar projeto...")
        # Tenta encontrar o projeto no diretório atual
        current_dir = Path.cwd()
        if (current_dir / "buddmeyer_vision_v2").exists():
            source_dir = current_dir / "buddmeyer_vision_v2"
        elif (current_dir.parent / "buddmeyer_vision_v2").exists():
            source_dir = current_dir.parent / "buddmeyer_vision_v2"
        else:
            print_error("Não foi possível localizar os arquivos do projeto!")
            input("\nPressione Enter para sair...")
            return 1
    
    print_info(f"Diretório fonte: {source_dir}")
    
    # Copia todo o diretório buddmeyer_vision_v2
    dest_dir = install_dir / "buddmeyer_vision_v2"
    if dest_dir.exists():
        print_warning("Removendo instalação anterior...")
        shutil.rmtree(dest_dir)
    
    print_info("Copiando arquivos...")
    shutil.copytree(source_dir, dest_dir)
    print_success("Arquivos copiados")
    
    # Cria ambiente virtual
    if not create_venv(install_dir):
        input("\nPressione Enter para sair...")
        return 1
    
    # Configura ambiente virtual
    if platform.system() == "Windows":
        venv_python = install_dir / "venv" / "Scripts" / "python.exe"
    else:
        venv_python = install_dir / "venv" / "bin" / "python"
    
    if not venv_python.exists():
        print_error("Python do ambiente virtual não encontrado")
        input("\nPressione Enter para sair...")
        return 1
    
    # Atualiza pip
    if not upgrade_pip(venv_python):
        print_warning("Continuando mesmo com erro no pip...")
    
    # Instala dependências
    if not install_dependencies(venv_python, install_dir / "requirements.txt"):
        print_error("Falha na instalação de dependências")
        input("\nPressione Enter para sair...")
        return 1
    
    # Cria scripts de inicialização
    create_start_scripts(install_dir, venv_python)
    
    # Verifica instalação
    if verify_installation(venv_python):
        print_header("INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
        print_success(f"Sistema instalado em: {install_dir}")
        print_info("\nPara iniciar o sistema:")
        print_info(f"  1. Navegue até: {install_dir}")
        print_info(f"  2. Dê duplo clique em: Iniciar_Buddmeyer_Vision.bat")
        print_info("\nOu execute no terminal:")
        print_info(f"  cd {install_dir}")
        print_info(f"  .\\venv\\Scripts\\activate")
        print_info(f"  python buddmeyer_vision_v2\\main.py")
    else:
        print_warning("Instalação concluída com avisos")
        print_info("Algumas dependências podem não estar instaladas corretamente")
    
    input("\nPressione Enter para sair...")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInstalação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nErro inesperado: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")
        sys.exit(1)

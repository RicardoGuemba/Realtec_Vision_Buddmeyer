@echo off
title Criar Instalador - Buddmeyer Vision System
echo ========================================
echo Criando Instalador .exe
echo ========================================
echo.

cd /d "%~dp0"

REM Verifica se PyInstaller está instalado
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller nao encontrado. Instalando...
    python -m pip install pyinstaller
)

REM Cria o instalador
echo Criando instalador...
python build_installer.py

if exist "dist\BuddmeyerVisionInstaller.exe" (
    echo.
    echo ========================================
    echo INSTALADOR CRIADO COM SUCESSO!
    echo ========================================
    echo.
    echo Arquivo: dist\BuddmeyerVisionInstaller.exe
    echo.
    pause
) else (
    echo.
    echo ERRO: Instalador nao foi criado!
    echo.
    pause
)

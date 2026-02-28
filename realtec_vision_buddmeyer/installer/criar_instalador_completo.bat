@echo off
title Criar Instalador Completo - Buddmeyer Vision v2.0
echo ============================================================
echo CRIANDO INSTALADOR COMPLETO
echo ============================================================
echo.

cd /d "%~dp0"

REM Ativa ambiente virtual se existir
if exist "..\..\venv\Scripts\activate.bat" (
    call "..\..\venv\Scripts\activate.bat"
)

REM Executa script de construção
python build_complete_installer.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo INSTALADOR CRIADO COM SUCESSO!
    echo ============================================================
    echo.
    echo Arquivo criado em: dist\BuddmeyerVisionInstallerCompleto.exe
    echo.
) else (
    echo.
    echo ============================================================
    echo ERRO AO CRIAR INSTALADOR
    echo ============================================================
    echo.
)

pause

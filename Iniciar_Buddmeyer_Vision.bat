@echo off
title Realtec Vision Buddmeyer v2.0
setlocal

REM Diretorio onde esta este .bat (funciona ao clicar duas vezes)
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

cd /d "%ROOT%"

if not exist "venv\Scripts\activate.bat" (
    echo ERRO: venv nao encontrado em %ROOT%\venv
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

if exist "buddmeyer_vision_v2\main.py" (
    python buddmeyer_vision_v2\main.py
) else if exist "realtec_vision_buddmeyer\main.py" (
    python realtec_vision_buddmeyer\main.py
) else (
    echo ERRO: main.py nao encontrado.
    pause
    exit /b 1
)

pause

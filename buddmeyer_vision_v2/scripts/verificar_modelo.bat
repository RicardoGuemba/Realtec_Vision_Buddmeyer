@echo off
title Verificar Modelo - Buddmeyer Vision System
cd /d "%~dp0\.."
call venv\Scripts\activate.bat
python buddmeyer_vision_v2\scripts\check_model.py
pause

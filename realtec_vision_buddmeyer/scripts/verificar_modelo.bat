@echo off
title Verificar Modelo - Buddmeyer Vision System
cd /d "%~dp0\.."
call venv\Scripts\activate.bat
python realtec_vision_buddmeyer\scripts\check_model.py
pause

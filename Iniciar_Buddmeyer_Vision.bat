@echo off
title Buddmeyer Vision System v2.0
cd /d "%~dp0"
call venv\Scripts\activate.bat
python buddmeyer_vision_v2\main.py
pause

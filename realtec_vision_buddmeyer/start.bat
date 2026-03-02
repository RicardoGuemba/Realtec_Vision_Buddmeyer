@echo off
title Realtec Vision Buddmeyer v2.0
cd /d "%~dp0"
cd ..
call venv\Scripts\activate.bat
python realtec_vision_buddmeyer\main.py
pause

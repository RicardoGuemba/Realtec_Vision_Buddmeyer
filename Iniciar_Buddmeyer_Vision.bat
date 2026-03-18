@echo off
title Realtec Vision Buddmeyer
cd /d "%~dp0"
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
python realtec_vision_buddmeyer\main.py
pause

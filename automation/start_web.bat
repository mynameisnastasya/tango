@echo off
cd /d "%~dp0"
py -m pip install -r requirements-safe.txt
py web_launcher.py
pause

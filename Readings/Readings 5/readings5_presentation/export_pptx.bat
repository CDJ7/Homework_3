@echo off
REM Build output\Readings5_Presentation.pptx
cd /d "%~dp0"
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
"%PY%" export_pptx.py
pause

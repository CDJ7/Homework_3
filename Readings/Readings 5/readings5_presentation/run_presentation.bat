@echo off
REM Start the Readings 5 presentation in your browser.
cd /d "%~dp0"
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
"%PY%" -m streamlit run app.py
pause

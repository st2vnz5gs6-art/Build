@echo off
rem SPT Spec Assurance - start the app (opens in your browser at http://localhost:8501)
cd /d "%~dp0"
if not exist ".venv\Scripts\streamlit.exe" (
    echo Not installed yet - run install.bat first.
    pause
    exit /b 1
)
".venv\Scripts\streamlit.exe" run app.py
pause

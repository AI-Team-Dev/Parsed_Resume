@echo off
echo Starting Resume Parser Application...
echo.

echo Starting Backend Server...
start cmd /k "cd /d %~dp0 && python -m uvicorn backend.main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo Starting Frontend...
cd frontend
streamlit run app.py

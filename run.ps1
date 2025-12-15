Write-Host "Starting Resume Parser Application..." -ForegroundColor Green
Write-Host ""

# Start Backend Server (from project root)
Write-Host "Starting Backend Server..." -ForegroundColor Yellow
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; python -m uvicorn backend.main:app --reload --port 8000"

Start-Sleep -Seconds 3

# Start Frontend
Write-Host "Starting Frontend..." -ForegroundColor Yellow
cd frontend
streamlit run app.py

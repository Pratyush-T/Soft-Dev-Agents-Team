@echo off
title ProNet - Professional Network & Career Platform
echo =====================================================================
echo              ProNet Professional Network - Local Launch
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Python dependencies...
python -c "import fastapi, uvicorn, sqlalchemy, aiosqlite, pydantic, jwt, passlib, bleach, filetype" 2>nul
if %errorlevel% neq 0 (
    echo Installing backend dependencies...
    pip install -r src\backend\requirements.txt
)

echo [2/3] Verifying database and pre-seeding 10 personas...
cd src\backend
python seed_data.py
cd ..\..

echo [3/3] Starting Backend API and Frontend Dev Server...
echo.
echo Starting FastAPI on http://localhost:8000...
start "ProNet Backend (FastAPI)" cmd /k "cd src\backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting Vite React SPA on http://localhost:5173...
start "ProNet Frontend (React)" cmd /k "cd src\frontend && npm run dev"

echo.
echo =====================================================================
echo  ProNet is launching!
echo  - Frontend Web UI:  http://localhost:5173
echo  - Backend REST API: http://localhost:8000/docs
echo  - Use the top-right 'Quick Persona Switcher' to switch accounts in 1 click!
echo =====================================================================
timeout /t 3 >nul
start http://localhost:5173

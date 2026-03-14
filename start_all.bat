@echo off
echo ========================================
echo   Banking Audit AI System - Local Start
echo ========================================

REM Start backend in new window
start "Backend - FastAPI" cmd /k "cd /d %~dp0backend && (if not exist venv python -m venv venv) && call venv\Scripts\activate && pip install -r requirements.txt -q && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait 5 seconds for backend to start
timeout /t 5 /noisy

REM Start frontend in new window
start "Frontend - Vite" cmd /k "cd /d %~dp0frontend && (if not exist node_modules npm install) && npm run dev"

echo.
echo Services starting...
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo.
echo To share on local network, use your IP address:
echo   Frontend: http://YOUR_IP:5173
echo   Backend:  http://YOUR_IP:8000
echo.
pause

@echo off
echo Starting Banking Audit AI Frontend...
cd /d "%~dp0frontend"

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing npm dependencies...
    npm install
)

REM Start Vite dev server
echo Starting frontend on http://localhost:5173
npm run dev

pause

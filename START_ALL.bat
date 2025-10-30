@echo off
echo ============================================
echo Starting ConvoTravelInsure Full Stack
echo ============================================
echo.

echo Starting Backend...
start "Backend Server" cmd /k "cd /d %~dp0apps\backend && uvicorn app.main:app --reload"

timeout /t 3 /nobreak >nul

echo Starting Frontend...
start "Frontend Server" cmd /k "cd /d %~dp0apps\frontend && npm run dev"

echo.
echo ============================================
echo Both servers are starting!
echo ============================================
echo.
echo Backend:  http://localhost:8000
echo Backend Docs: http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.
echo Close the two windows that opened to stop servers
echo.
pause


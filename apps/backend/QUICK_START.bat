@echo off
echo ====================================
echo Starting ConvoTravelInsure Server
echo ====================================
echo.
echo Phase 4: Chat API Endpoints
echo.
echo Server will start on: http://localhost:8000
echo API Docs available at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.
echo ====================================
echo.

cd /d "%~dp0"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause


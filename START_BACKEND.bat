@echo off
echo Starting Backend Development Server...
echo.
cd /d %~dp0apps\backend
echo Current directory: %CD%
echo.
echo Starting FastAPI with Uvicorn...
echo Press Ctrl+C to stop
echo.
uvicorn app.main:app --reload


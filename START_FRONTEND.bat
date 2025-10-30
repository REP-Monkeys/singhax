@echo off
echo Starting Frontend Development Server...
echo.
cd /d %~dp0apps\frontend
echo Current directory: %CD%
echo.
echo Starting Next.js...
echo Press Ctrl+C to stop
echo.
npm run dev


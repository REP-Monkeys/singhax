@echo off
echo ========================================
echo Cleaning Python Cache and Restarting
echo ========================================

REM Kill all Python processes
echo Killing Python processes...
taskkill /F /IM python.exe /T 2>nul
timeout /t 2 /nobreak >nul

REM Delete Python cache
echo Removing Python cache...
if exist app\__pycache__ rd /s /q app\__pycache__
if exist app\agents\__pycache__ rd /s /q app\agents\__pycache__
if exist app\routers\__pycache__ rd /s /q app\routers\__pycache__
if exist app\services\__pycache__ rd /s /q app\services\__pycache__
if exist app\models\__pycache__ rd /s /q app\models\__pycache__
if exist app\core\__pycache__ rd /s /q app\core\__pycache__
if exist app\adapters\__pycache__ rd /s /q app\adapters\__pycache__
if exist app\adapters\insurer\__pycache__ rd /s /q app\adapters\insurer\__pycache__
if exist app\schemas\__pycache__ rd /s /q app\schemas\__pycache__

echo Cache cleaned!

REM Remove all Unicode from Python files
echo Removing Unicode characters from Python files...
python -c "import os, re; [open(os.path.join(r,f), 'w', encoding='utf-8').write(re.sub(r'[^\x00-\x7F]+', ' ', open(os.path.join(r,f), 'r', encoding='utf-8').read())) for r, _, files in os.walk('app') for f in files if f.endswith('.py')]; print('Unicode removed from all Python files')"

echo.
echo ========================================
echo Starting Server...
echo ========================================
echo.

REM Start the server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

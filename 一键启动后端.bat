@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "VENV=%BACKEND%\venv"
set "PY=%VENV%\Scripts\python.exe"
set "LAN_IP=127.0.0.1"

for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /c:"IPv4"') do (
  if "%LAN_IP%"=="127.0.0.1" set "LAN_IP=%%A"
)
set "LAN_IP=%LAN_IP: =%"

title TaskReminder Backend Launcher
echo.
echo ========================================
echo   TaskReminder Backend One-Click Start
echo ========================================
echo.

if not exist "%BACKEND%" (
  echo [ERROR] backend folder was not found.
  pause
  exit /b 1
)

if not exist "%VENV%" (
  echo [1/4] Creating Python virtual environment...
  python -m venv "%VENV%"
  if errorlevel 1 (
    echo [ERROR] Failed to create venv. Please install Python and add it to PATH.
    pause
    exit /b 1
  )
) else (
  echo [1/4] Python virtual environment already exists.
)

echo [2/4] Installing/checking backend dependencies...
"%PY%" -m pip install -r "%BACKEND%\requirements.txt"
if errorlevel 1 (
  echo [ERROR] Dependency installation failed. Please check network or pip settings.
  pause
  exit /b 1
)

if not exist "%BACKEND%\.env" (
  echo [3/4] Creating default .env...
  copy "%BACKEND%\.env.example" "%BACKEND%\.env" >nul
) else (
  echo [3/4] .env already exists.
)

echo [4/4] Opening API docs...
start "" "http://127.0.0.1:8000/docs"

echo.
echo Backend will start now:
echo   API docs: http://127.0.0.1:8000/docs
echo   Health:   http://127.0.0.1:8000/health
echo.
echo For phone access on the same Wi-Fi, use this PC's LAN IP in the app, for example:
echo   http://%LAN_IP%:8000
echo.
echo Close this window to stop the backend.
echo.

cd /d "%BACKEND%"
"%PY%" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

echo.
echo Backend stopped.
pause

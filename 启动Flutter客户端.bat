@echo off
setlocal

set "ROOT=%~dp0"
set "APP=%ROOT%app"
set "LAN_IP=127.0.0.1"

for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /c:"IPv4"') do (
  if "%LAN_IP%"=="127.0.0.1" set "LAN_IP=%%A"
)
set "LAN_IP=%LAN_IP: =%"

title TaskReminder Flutter Web Launcher
echo.
echo ========================================
echo   TaskReminder Flutter Web Launcher
echo ========================================
echo.

where flutter >nul 2>nul
if errorlevel 1 (
  echo [ERROR] flutter command was not found.
  echo Please install Flutter SDK first, then run this script again.
  pause
  exit /b 1
)

if not exist "%APP%\pubspec.yaml" (
  echo [ERROR] app\pubspec.yaml was not found.
  pause
  exit /b 1
)

cd /d "%APP%"

if not exist "%APP%\windows" if not exist "%APP%\android" if not exist "%APP%\web" (
  echo [1/4] Generating Flutter platform folders...
  flutter create --platforms=android,ios,windows,macos,linux,web .
  if errorlevel 1 (
    echo [ERROR] Failed to generate Flutter platform folders.
    pause
    exit /b 1
  )
) else (
  echo [1/4] Flutter platform folders already exist.
)

echo [2/4] Installing/checking Flutter dependencies...
flutter pub get
if errorlevel 1 (
  echo [ERROR] flutter pub get failed.
  pause
  exit /b 1
)

echo [3/4] Building Flutter web client...
flutter build web
if errorlevel 1 (
  echo [ERROR] flutter build web failed.
  pause
  exit /b 1
)

echo [4/4] Starting web server...
echo.
echo Open on this PC:
echo   http://127.0.0.1:8088
echo.
echo Open on phone on the same Wi-Fi:
echo   http://%LAN_IP%:8088
echo.
echo If the phone cannot connect, allow Python through Windows Firewall.
echo Close this window to stop the web client.
echo.

start "" "http://127.0.0.1:8088"
cd /d "%APP%\build\web"
where py >nul 2>nul
if errorlevel 1 (
  python -m http.server 8088 --bind 0.0.0.0
) else (
  py -3 -m http.server 8088 --bind 0.0.0.0
)

echo.
echo Flutter web client stopped.
pause

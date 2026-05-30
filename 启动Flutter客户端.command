#!/bin/zsh
set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
APP="$ROOT/app"
LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo 127.0.0.1)"

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
export FLUTTER_STORAGE_BASE_URL="${FLUTTER_STORAGE_BASE_URL:-https://storage.flutter-io.cn}"
export PUB_HOSTED_URL="${PUB_HOSTED_URL:-https://pub.flutter-io.cn}"

echo
echo "========================================"
echo "  TaskReminder Flutter Client Launcher"
echo "========================================"
echo

if ! command -v flutter >/dev/null 2>&1; then
  echo "[ERROR] flutter command was not found."
  echo "Please install Flutter SDK first, then run this script again."
  echo
  echo "After installing Flutter, you can also run:"
  echo "  cd app"
  echo "  flutter create --platforms=android,ios,windows,macos,linux,web ."
  echo "  flutter pub get"
  echo "  flutter run"
  echo
  read "REPLY?Press Enter to close..."
  exit 1
fi

if [ ! -f "$APP/pubspec.yaml" ]; then
  echo "[ERROR] app/pubspec.yaml was not found."
  echo
  read "REPLY?Press Enter to close..."
  exit 1
fi

cd "$APP"

if [ ! -d "$APP/macos" ] && [ ! -d "$APP/android" ] && [ ! -d "$APP/web" ]; then
  echo "[1/3] Generating Flutter platform folders..."
  flutter create --platforms=android,ios,windows,macos,linux,web .
  if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to generate Flutter platform folders."
    echo
    read "REPLY?Press Enter to close..."
    exit 1
  fi
else
  echo "[1/3] Flutter platform folders already exist."
fi

echo "[2/3] Installing/checking Flutter dependencies..."
flutter pub get
if [ $? -ne 0 ]; then
  echo "[ERROR] flutter pub get failed."
  echo
  read "REPLY?Press Enter to close..."
  exit 1
fi

echo "[3/3] Building and starting Flutter web client..."
echo "Opening Flutter web client:"
echo "  This Mac: http://127.0.0.1:8088"
echo "  Phone on same Wi-Fi: http://$LAN_IP:8088"
echo
flutter build web
if [ $? -ne 0 ]; then
  echo "[ERROR] flutter build web failed."
  echo
  read "REPLY?Press Enter to close..."
  exit 1
fi

if lsof -ti tcp:8088 >/dev/null 2>&1; then
  echo "[INFO] Port 8088 is already in use. Closing the old web server..."
  lsof -ti tcp:8088 | xargs kill >/dev/null 2>&1 || true
  sleep 1
fi

(sleep 2 && open "http://127.0.0.1:8088" >/dev/null 2>&1) &
cd "$APP/build/web"
if command -v python3 >/dev/null 2>&1; then
  python3 -m http.server 8088 --bind 0.0.0.0
else
  python -m http.server 8088 --bind 0.0.0.0
fi

echo
echo "Flutter client stopped."
read "REPLY?Press Enter to close..."

#!/bin/zsh
set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
VENV="$BACKEND/.venv"
PY="$VENV/bin/python"
PY_CERT_INSTALLER="/Applications/Python 3.13/Install Certificates.command"

echo
echo "========================================"
echo "  TaskReminder Backend One-Click Start"
echo "========================================"
echo

if [ ! -d "$BACKEND" ]; then
  echo "[ERROR] backend folder was not found."
  echo
  read "REPLY?Press Enter to close..."
  exit 1
fi

if [ ! -x "$PY" ]; then
  echo "[1/4] Creating Python virtual environment..."
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv "$VENV"
  elif command -v python >/dev/null 2>&1; then
    python -m venv "$VENV"
  else
    echo "[ERROR] Python was not found. Please install Python 3 first."
    echo
    read "REPLY?Press Enter to close..."
    exit 1
  fi
else
  echo "[1/4] Python virtual environment already exists."
fi

echo "[2/4] Installing/checking backend dependencies..."
if ! "$PY" -m pip install -r "$BACKEND/requirements.txt"; then
  echo
  echo "[INFO] pip SSL check failed or dependency installation failed."

  if [ -f "$PY_CERT_INSTALLER" ]; then
    echo "[INFO] Trying to repair Python certificates..."
    /bin/zsh "$PY_CERT_INSTALLER"
    echo "[INFO] Retrying dependency installation..."
  fi

  if ! "$PY" -m pip install -r "$BACKEND/requirements.txt"; then
    echo
    echo "[WARN] Normal PyPI SSL verification is still failing."
    echo "[INFO] Trying fallback PyPI download settings..."
    if ! "$PY" -m pip install \
      --trusted-host pypi.org \
      --trusted-host files.pythonhosted.org \
      --trusted-host pypi.python.org \
      -r "$BACKEND/requirements.txt"; then
      echo "[ERROR] Dependency installation failed."
      echo "Please check network, VPN/proxy, or run this manually:"
      echo "  /Applications/Python\\ 3.13/Install\\ Certificates.command"
      echo
      read "REPLY?Press Enter to close..."
      exit 1
    fi
  fi
fi

if [ ! -f "$BACKEND/.env" ]; then
  echo "[3/4] Creating default .env..."
  if [ -f "$BACKEND/.env.example" ]; then
    cp "$BACKEND/.env.example" "$BACKEND/.env"
  else
    echo "[WARN] .env.example was not found, skipping .env creation."
  fi
else
  echo "[3/4] .env already exists."
fi

echo "[4/4] Opening API docs..."
open "http://127.0.0.1:8000/docs" >/dev/null 2>&1 || true

echo
echo "Backend will start now:"
echo "  API docs: http://127.0.0.1:8000/docs"
echo "  Health:   http://127.0.0.1:8000/health"
echo
echo "For phone access on the same Wi-Fi, use this Mac's LAN IP in the app, for example:"
echo "  http://192.168.1.8:8000"
echo
echo "Close this window or press Ctrl+C to stop the backend."
echo

cd "$BACKEND"
"$PY" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

echo
echo "Backend stopped."
read "REPLY?Press Enter to close..."

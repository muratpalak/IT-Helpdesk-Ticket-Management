#!/bin/zsh
# NexaDesk Glass — double-click launcher for macOS.
# The script always starts from the folder where it lives.
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install it from https://www.python.org/downloads/"
  read '?Press Enter to close...'
  exit 1
fi

if [[ ! -f "requirements.txt" ]]; then
  echo "The project files are incomplete: requirements.txt not found."
  read '?Press Enter to close...'
  exit 1
fi

if [[ ! -d .venv ]]; then
  echo "[1/3] Creating a local Python environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate

echo "[2/3] Installing project dependencies (first run may take a minute)..."
python -m pip install -r requirements.txt

# If an earlier helpdesk project already uses port 8000, select an open port.
PORT=$(python - <<'PY'
import socket
for port in range(8000, 8010):
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            continue
        print(port)
        break
else:
    raise SystemExit("No free port between 8000 and 8009")
PY
)
URL="http://127.0.0.1:${PORT}"
echo "[3/3] Starting NexaDesk Glass at $URL"
echo "Leave this Terminal window open. Press Control+C to stop the application."

(sleep 3; open "$URL") &
python -m uvicorn app:app --host 127.0.0.1 --port "$PORT"

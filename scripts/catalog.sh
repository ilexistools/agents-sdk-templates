#!/usr/bin/env bash
# Start, stop or check the catalog dashboard on macOS and Linux.
#
#   scripts/catalog.sh start     install dependencies on first use, start in the
#                                background, wait until it answers, open the browser
#   scripts/catalog.sh stop      stop the dashboard started by this script
#   scripts/catalog.sh status    show whether it is running
#   scripts/catalog.sh restart   stop and start again
#
# Options: --no-browser. The port comes from PORT (default 8787).
# Logs: .run/catalog.log. PID: .run/catalog.pid.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Git Bash / MSYS / Cygwin on Windows: use the Windows script, which manages
# native process trees correctly.
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    args=()
    for arg in "$@"; do
      if [ "$arg" = "--no-browser" ]; then args+=("-NoBrowser"); else args+=("$arg"); fi
    done
    exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$ROOT/scripts/catalog.ps1")" "${args[@]}"
    ;;
esac
RUN_DIR="$ROOT/.run"
PID_FILE="$RUN_DIR/catalog.pid"
LOG_FILE="$RUN_DIR/catalog.log"
PORT="${PORT:-8787}"
URL="http://127.0.0.1:$PORT"
COMMAND="${1:-start}"
OPEN_BROWSER=1
for arg in "$@"; do [ "$arg" = "--no-browser" ] && OPEN_BROWSER=0; done

python_bin() {
  if [ -x "$ROOT/.venv/bin/python" ]; then echo "$ROOT/.venv/bin/python"
  elif [ -x "$ROOT/.venv/Scripts/python.exe" ]; then echo "$ROOT/.venv/Scripts/python.exe"  # Git Bash on Windows
  fi
}

running_pid() {
  [ -f "$PID_FILE" ] || return 1
  local pid
  pid="$(tr -d '[:space:]' < "$PID_FILE")"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then echo "$pid"; return 0; fi
  rm -f "$PID_FILE"
  return 1
}

healthy() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsS --max-time 2 "$URL/health" >/dev/null 2>&1
  else
    "$(python_bin)" -c "import urllib.request; urllib.request.urlopen('$URL/health', timeout=2)" >/dev/null 2>&1
  fi
}

open_browser() {
  [ "$OPEN_BROWSER" = 1 ] || return 0
  if [ "$(uname -s)" = "Darwin" ]; then open "$URL"                # macOS
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 &  # Linux
  elif command -v cmd.exe >/dev/null 2>&1; then cmd.exe /c start "" "$URL"         # Git Bash
  fi
}

start() {
  local pid
  if pid="$(running_pid)"; then
    echo "Already running (PID $pid) at $URL"
    open_browser
    return 0
  fi
  if healthy; then
    echo "Something is already answering at $URL (not started by this script)."
    echo "Stop it, or choose another port: PORT=8790 scripts/catalog.sh start"
    exit 1
  fi
  if [ -z "$(python_bin)" ]; then
    if ! command -v uv >/dev/null 2>&1; then
      echo "uv is required and was not found. Install it, then run this again:"
      echo "  https://docs.astral.sh/uv/getting-started/installation/"
      exit 1
    fi
    echo "Installing dependencies (first run)..."
    (cd "$ROOT" && uv sync --locked)
  fi
  mkdir -p "$RUN_DIR"
  (cd "$ROOT" && nohup "$(python_bin)" -m app serve --port "$PORT" >"$LOG_FILE" 2>&1 &
   echo $! >"$PID_FILE")
  pid="$(tr -d '[:space:]' < "$PID_FILE")"
  printf "Starting at %s " "$URL"
  for _ in $(seq 1 60); do
    if healthy; then
      echo
      echo "Running (PID $pid). Stop it with scripts/stop.command or scripts/catalog.sh stop"
      open_browser
      return 0
    fi
    kill -0 "$pid" 2>/dev/null || break
    printf "."
    sleep 0.5
  done
  echo
  echo "It did not start. Last lines of $LOG_FILE:"
  tail -n 15 "$LOG_FILE" 2>/dev/null || true
  stop quiet
  exit 1
}

stop() {
  local pid
  if ! pid="$(running_pid)"; then
    if [ "${1:-}" != "quiet" ]; then
      echo "Not running (no process started by this script)."
      if healthy; then echo "Note: something else is answering at $URL."; fi
    fi
    return 0
  fi
  kill "$pid" 2>/dev/null || true
  for _ in $(seq 1 20); do kill -0 "$pid" 2>/dev/null || break; sleep 0.25; done
  kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
  rm -f "$PID_FILE"
  [ "${1:-}" = "quiet" ] || echo "Stopped (PID $pid)."
}

status() {
  local pid
  if pid="$(running_pid)"; then
    if healthy; then echo "Running (PID $pid) at $URL"
    else echo "Process $pid exists but $URL is not answering yet. See $LOG_FILE"; fi
  else
    echo "Not running."
  fi
}

case "$COMMAND" in
  start) start ;;
  stop) stop ;;
  status) status ;;
  restart) stop quiet; start ;;
  *) echo "Usage: scripts/catalog.sh start|stop|status|restart [--no-browser]"; exit 2 ;;
esac

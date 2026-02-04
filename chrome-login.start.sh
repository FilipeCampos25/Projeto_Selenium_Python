#!/usr/bin/env bash
set -e

CHROME_DEBUG_PORT="${CHROME_DEBUG_PORT:-9222}"
VNC_PORT="${VNC_PORT:-5900}"
NOVNC_PORT="${NOVNC_PORT:-7900}"
START_URL="${START_URL:-about:blank}"

export DISPLAY=:99

echo "[chrome-login] Starting Xvfb..."
Xvfb :99 -screen 0 1920x1080x24 -ac +extension RANDR &

echo "[chrome-login] Starting window manager (openbox)..."
openbox &

echo "[chrome-login] Starting x11vnc..."
x11vnc -display :99 -forever -shared -rfbport "${VNC_PORT}" -nopw &

echo "[chrome-login] Starting noVNC..."
websockify --web=/usr/share/novnc/ "${NOVNC_PORT}" "localhost:${VNC_PORT}" &

echo "[chrome-login] Starting Google Chrome (NO WebDriver), DevTools port ${CHROME_DEBUG_PORT}..."
google-chrome \
  --no-sandbox \
  --disable-dev-shm-usage \
  --remote-debugging-address=0.0.0.0 \
  --remote-debugging-port="${CHROME_DEBUG_PORT}" \
  --user-data-dir="/profile" \
  --profile-directory=Default \
  --no-first-run \
  --no-default-browser-check \
  --new-tab "${START_URL}" &

echo "[chrome-login] Ready. noVNC :${NOVNC_PORT} | DevTools :${CHROME_DEBUG_PORT} (internal docker network)"
tail -f /dev/null

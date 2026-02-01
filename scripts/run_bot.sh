#!/usr/bin/env bash
set -euo pipefail

# Run the bot in a restart loop and log output
# Use project-relative paths so no absolute user paths are stored in the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."
cd "$PROJECT_ROOT" || exit 1

# Prefer .venv python if present
if [ -x ".venv/bin/python" ]; then
  PYEXEC=".venv/bin/python"
else
  PYEXEC="python"
fi

LOG="bot.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') - starting bot" >> "$LOG"
while true; do
  "$PYEXEC" main.py >> "$LOG" 2>&1 || true
  echo "$(date '+%Y-%m-%d %H:%M:%S') - bot exited, restarting in 5s" >> "$LOG"
  sleep 5
done

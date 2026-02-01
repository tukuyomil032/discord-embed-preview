#!/usr/bin/env bash
# Restart the tmux bot session named "discord-bot"
set -euo pipefail
SESSION="discord-bot"
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# Stop if running
if tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux kill-session -t "$SESSION"
fi
# Start fresh
tmux new-session -d -s "$SESSION" "bash $SCRIPT_DIR/run_bot.sh"
echo "Restarted tmux session $SESSION"

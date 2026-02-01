#!/usr/bin/env bash
# Stop the tmux-managed bot session
set -euo pipefail
SESSION="discord-bot"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux kill-session -t "$SESSION"
  echo "Stopped tmux session: $SESSION"
else
  echo "tmux session $SESSION not running"
fi

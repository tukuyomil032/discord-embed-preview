#!/usr/bin/env bash
# Start tmux-managed bot session (simple name)
set -euo pipefail
SESSION="discord-bot"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."
cd "$PROJECT_ROOT" || exit 1

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session $SESSION already running"
  exit 0
fi

# Start detached session that runs the run_bot.sh script
tmux new-session -d -s "$SESSION" "bash $SCRIPT_DIR/run_bot.sh"

echo "Started tmux session: $SESSION"

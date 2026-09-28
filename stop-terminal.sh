#!/bin/bash
# Aeon Nimbus Terminal — stop all services
for p in 8000 8001 8002 8600 6900 8787 5173; do
  PIDS=$(lsof -ti tcp:$p 2>/dev/null)
  [ -n "$PIDS" ] && echo "$PIDS" | xargs kill -9 2>/dev/null && echo "stopped :$p"
done
echo "🌑 Aeon Nimbus Terminal stopped."

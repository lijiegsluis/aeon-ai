#!/bin/bash
# Aeon Nimbus Terminal — full-stack launcher
#   :5173 frontend        :8787 report worker      :8000 Aeon analytics+fusion
#   :6900 OpenBB API      :8001 TradingAgents      :8002 FinRobot app
#   :8600 Deep Research REST API
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
V="$DIR/vendor"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
export SSL_CERT_FILE=$("$V/venv-openbb/bin/python" -c "import certifi; print(certifi.where())")
export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE"

echo "🌌 Aeon Nimbus Terminal — full stack"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for p in 8000 8001 8002 8600 6900 8787 5173; do
  lsof -ti tcp:$p | xargs kill -9 2>/dev/null || true
done

echo "[1/6] Aeon analytics+fusion :8000"
"$DIR/analytics/.venv/bin/python" -m uvicorn main:app \
  --host 127.0.0.1 --port 8000 --app-dir "$DIR/analytics" >/tmp/aeon-analytics.log 2>&1 &

echo "[2/6] OpenBB Platform API   :6900"
"$V/venv-openbb/bin/openbb-api" --host 127.0.0.1 --port 6900 >/tmp/openbb-api.log 2>&1 &

echo "[3/6] TradingAgents         :8001"
"$V/venv-tradingagents/bin/python" -m uvicorn ta_service:app \
  --host 127.0.0.1 --port 8001 --app-dir "$V" >/tmp/ta-service.log 2>&1 &

echo "[4/6] FinRobot equity app   :8002"
(cd "$V/FinRobot" && "$V/venv-finrobot/bin/python" -m uvicorn \
  finrobot_equity.web_app.main:app --host 127.0.0.1 --port 8002) >/tmp/finrobot-app.log 2>&1 &

echo "[5/6] Deep Research API     :8600"
(cd "$V/financial-research-analyst-agent" && "$V/venv-fra/bin/python" -m uvicorn \
  src.api.routes:app --host 127.0.0.1 --port 8600) >/tmp/fra-api.log 2>&1 &

echo "[6/6] Report worker + UI    :8787 / :5173"
node "$DIR/cli/bin/aeon-ai.js" &
CLI_PID=$!

# Wait for each service — OpenBB is the slow one (~30-60s)
wait_for() {  # name port path timeout_seconds
  local i=0
  until curl -sf -m 3 "http://127.0.0.1:$2$3" >/dev/null 2>&1; do
    i=$((i+3)); [ $i -ge "$4" ] && { echo "   ⚠️  $1 :$2 not up after ${4}s — tail /tmp logs"; return; }
    sleep 3
  done
  echo "   ✅ $1 :$2"
}
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
wait_for Aeon-analytics 8000 /health 30
wait_for TradingAgents 8001 /health 30
wait_for DeepReports 8002 / 45
wait_for DeepResearch 8600 /health 45
wait_for Frontend 5173 / 45
wait_for OpenBB 6900 "/api/v1/equity/search?query=a&provider=sec" 90

FR_PASS=$(grep -m1 'admin password' /tmp/finrobot-app.log 2>/dev/null | sed 's/.*: //')
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 http://localhost:5173"
echo "   Tabs: Overview · Fusion · Research · Markets · Agent Desk"
echo "         FinRobot · Analyst · Quant Lab · Personas · Fincept"
[ -n "$FR_PASS" ] && echo "   FinRobot login: admin / $FR_PASS"
echo "   Fincept desktop: open ~/Applications/FinceptTerminal.app"
echo "   Stop: Ctrl+C here, or ~/aeon-ai/stop-terminal.sh"
command -v open >/dev/null && open http://localhost:5173

trap 'for p in 8000 8001 8002 8600 6900 8787 5173; do lsof -ti tcp:$p | xargs kill -9 2>/dev/null; done; exit 0' INT TERM
wait $CLI_PID

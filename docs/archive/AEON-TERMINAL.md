# 🌌 Aeon Nimbus Terminal

A fully local financial workstation that fuses five major open-source finance
projects and an original analytics layer into one instrument. Your keys, your
machine, your data — nothing leaves localhost except provider API calls.

## Launch / stop

```bash
~/aeon-ai/start-terminal.sh    # starts all 7 services, opens the browser
~/aeon-ai/stop-terminal.sh     # stops everything
```

## The instrument

One **global ticker** (nav search, press `/` to focus) drives every engine.
Recent tickers appear as chips on the Overview.

| Tab           | Engine                 | What it does                                                                                                                     |
| ------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| 🌌 Overview   | fused                  | Live quote + 6-month chart + 52W range + quant snapshot + investor lenses, one screen                                            |
| 🜁 Fusion      | original               | **Valuation Ensemble** (5 philosophies vote, disagreement index) · **Council of Agents** (all paradigms deliberate, chair rules) |
| 🧠 Research   | Aeon worker            | 55-dimension report + PDF (~10 s, Finnhub/Gemini/Groq/Cohere keys)                                                               |
| 📡 Markets    | OpenBB Platform        | Live watchlist; cross-source merged quotes; full catalog at :6900/docs                                                           |
| ⚔️ Agent Desk | TradingAgents          | Real LangGraph: 4 analysts → bull/bear debate → trader → risk (3–10 min, needs LLM key; Gemini/OpenAI/Anthropic selectable)      |
| 🤖 FinRobot   | FinRobot               | Their native equity-research web app (login: admin + password from launcher output)                                              |
| 🔬 Analyst    | research-analyst-agent | Their native 11-agent Streamlit app (RAG over SEC filings)                                                                       |
| 🧮 Quant Lab  | Aeon analytics         | Monte Carlo (10K GBM), 3-scenario DCF, Markowitz optimizer                                                                       |
| 🏛️ Personas   | Aeon analytics         | Buffett/Graham/Lynch/Munger/Marks lenses (free quick-take + live AI)                                                             |
| 🖥️ Fincept    | FinceptTerminal        | Desktop companion: `open ~/Applications/FinceptTerminal.app`                                                                     |

## Services & ports

| Port | Service                    | Source                                    |
| ---- | -------------------------- | ----------------------------------------- |
| 5173 | React frontend             | `frontend/`                               |
| 8787 | Report worker              | `worker/`                                 |
| 8000 | Aeon analytics + fusion    | `analytics/main.py`                       |
| 6900 | OpenBB Platform REST API   | `vendor/venv-openbb`                      |
| 8001 | TradingAgents wrapper      | `vendor/ta_service.py`                    |
| 8002 | FinRobot web app           | `vendor/FinRobot`                         |
| 8501 | Research analyst Streamlit | `vendor/financial-research-analyst-agent` |

Logs: `/tmp/aeon-analytics.log`, `/tmp/openbb-api.log`, `/tmp/ta-service.log`,
`/tmp/finrobot-app.log`, `/tmp/fra-app.log`.

## Keys

- **Research tab**: managed in-app via Manage Keys (encrypted, BYOK)
- **Agent Desk / Fusion / Personas**: key field in each tab, stored in browser
  localStorage only, sent per-request to local services
- **Gemini free tier** allows ~20 requests/day/model — enough for a couple of
  councils, not for a TradingAgents run (50–200 calls). Use a paid key or
  switch provider in Agent Desk.

## Architecture notes

- Each vendored project keeps its **own Python venv** in `vendor/` — their
  dependency trees conflict (FinRobot needs Python <3.12, runs on a uv-managed
  3.11; the rest on 3.13).
- OpenBB startup requires `SSL_CERT_FILE` pointing at certifi's bundle
  (handled by the launcher).
- The Fusion layer treats the projects' overlapping features as ensembles:
  redundant data fetchers → cross-source verification; four DCF variants →
  a five-model valuation vote; four agent paradigms → a council with vote
  tally, agreement score, and synthesized ruling.

## Credits

Built on the shoulders of: [OpenBB](https://github.com/OpenBB-finance/OpenBB),
[TradingAgents](https://github.com/TauricResearch/TradingAgents),
[FinRobot](https://github.com/AI4Finance-Foundation/FinRobot),
[financial-research-analyst-agent](https://github.com/gsaini/financial-research-analyst-agent),
[FinceptTerminal](https://github.com/Fincept-Corporation/FinceptTerminal),
and the original Nipun AI report engine. Not financial advice.

# The Aeon ecosystem — what's actually built

This is the current, code-verified picture of the Aeon product family, replacing
the older docs in [`docs/archive/`](docs/archive/). All four layers the landing
page describes are real and live; one of them — Aeon Platform — lives in a
separate directory/codebase outside this repo, which earlier drafts of this
doc missed (they only searched `~/aeon-ai`). Treat this file, not the marketing
site's copy, as the source of truth for what's real — update it here first when
that changes.

## The four layers (from the landing page's own framing)

| Layer      | Product                                                 | What it does                                                                                                                                                                                                                                                                                                         | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Where                                                                                                                                                                    | Dev ports                                                                                                 |
| ---------- | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| Foundation | **Aeon Analysis**                                       | Deep single-ticker research: Fusion valuation ensemble, CAPM DCF, Council of Agents, grounded persona commentary, Houston research-ops (brief/gates/notes). "Know WHAT to buy."                                                                                                                                      | **Live**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | `analytics/` + `frontend/`                                                                                                                                               | backend :8000, frontend :5173                                                                             |
| Event      | **Aeon Intelligence**                                   | Event/catalyst countdown dashboard — "Buy the rumor, sell the news" timing matrix. "Know WHEN to trade."                                                                                                                                                                                                             | **Live, real data.** `calendar_sync.py` seeds real, sourced 2026 dates for FOMC/NFP/CPI/PPI/ECB/BOJ; events with no publicly fixed schedule this far out (individual earnings, OPEC+, G7, debt ceiling) keep an honestly-labeled "— estimated date" placeholder rather than a false-precision guess. A background startup sync also pulls real RSS financial news, CNN Fear & Greed, VIX, and SEC Form 4 insider trades into the news feed, each tagged with its real source (never `'demo'`). No ticker filter until this redesign, no auth.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | `intelligence/`                                                                                                                                                          | backend :8003, frontend :5175                                                                             |
| Research   | **Aeon Platform**                                       | Filings-to-published-research pipeline: a sourced Data Studio (search a company → auto-research it from filings/public sources → review → recompute → export), Bull/Base/Bear DCF, formula-driven Excel model generator, coverage-universe scoring. "Turn the thesis into a full research report."                   | **Live.** Confirmed running (`uvicorn aeon_nimbus.api:app`, port 5174) with a substantial, actively-maintained FastAPI codebase and its own test suite. The marketing site's `status: 'live'` in `aeonnimbus-landing/src/products.ts` is accurate — an earlier version of this doc wrongly called it vaporware because it only searched this repo.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | **Not in this repo.** Separate codebase at `~/AeonNimbus/AeonNimbus_Platform/Platform_Source_Code`, its own git history (if any), own `.venv`/`.env`/Dockerfile.         | backend + frontend :5174 (single FastAPI process, dashboard and Data Studio both served from `/`)         |
| Execution  | **Aeon Terminal**, publicly branded **Nimbus Terminal** | A Qt-based native desktop trading terminal (order flow, live watchlists, multi-tab workspace), not a browser app. Internally built on the vendored Fincept Terminal codebase — that name is never shown to users; all public-facing surfaces (landing page, docs, the app's own `Info.plist`) say "Nimbus Terminal." | **Live and launchable.** Installed at `~/Applications/Nimbus Terminal.app` (renamed from the earlier in-progress rebuild `AeonNimbusTerminal.app`), `CFBundleName`/`CFBundleDisplayName` set to "Nimbus Terminal", registered with Launch Services under a custom URL scheme (`CFBundleURLTypes` → `nimbusterminal:`). The landing page's "Launch Aeon Terminal" link points at `nimbusterminal://launch`, so clicking it opens the installed app directly — same mechanism Slack/Zoom/Spotify use for "open the desktop app from a web link." Works only for visitors who already have Nimbus Terminal installed locally (honest for this machine's own demo/dev environment; a public visitor without it installed needs a download step first — not yet built). The untouched vendor copy remains parked at `~/Applications/FinceptTerminal-original.app.bak` (never renamed — left as the original reference copy) and the in-house `terminal/frontend/` scaffold (a genuinely-WIP hand-built React shell, no Fincept branding anywhere) stays parked too. | `vendor/FinceptTerminal/` (+ `.dmg` installer alongside it); installed rebrand at `~/Applications/Nimbus Terminal.app`; in-house scaffold parked at `terminal/frontend/` | native desktop app — no dev port; launched via the `nimbusterminal://` custom URL scheme, not `localhost` |

Separately, **Nipun AI** (root `cli/` + `worker/`) is a real, independently
shipped `npx aeon-ai` single-ticker report CLI running on Cloudflare Workers
(BYOK). It is architecturally disconnected from the four layers above — no
shared code, no shared data — and isn't part of this redesign.

## How the pieces actually connect today

- Aeon Analysis links out to Aeon Intelligence per-ticker (Overview "⏱ Timing",
  Rumor/News, Houston gates) — a plain navigation link to
  `$VITE_INTELLIGENCE_URL/?ticker=...`, not shared data or a shared backend.
  Intelligence opens that ticker's **Ticker Lens** (`GET /api/ticker/{symbol}`):
  the timing read from its nearest dated catalyst, the D-X event list,
  news/Telegram mentions, 90-day open-market insider trades, live signals and
  AI calls.
- That's it by design: Intelligence's calendar and news feed are populated
  from real sources (sourced 2026 macro calendars, real RSS/SEC/CNN/VIX
  fetchers) but are still Intelligence's own separate database, not fused
  into Aeon Analysis's signals — importing another product's event feed into
  Analysis's otherwise-real signals would blur which product is asserting
  what (see `frontend/src/dataProvenance.ts`). A link that's clearly labeled
  as opening a separate product's own view is the honest version of that
  integration.
- Aeon Analysis's own "Alpha Digest" (new in this redesign) synthesizes its
  own real signals — Fusion, DCF, Council of Agents, personas, Houston gates —
  into one per-ticker view. It does **not** replace Aeon Platform's research
  pipeline (Data Studio, Excel model export, published buy/sell/hold calls
  across a coverage universe) — the two are complementary, not overlapping:
  Alpha Digest is "everything this app already knows about one ticker, on one
  screen"; Aeon Platform is a separate, heavier research-production workflow.
  There is currently no nav link between Aeon Analysis and Aeon Platform (unlike
  the Intelligence link below) since Platform lives outside this repo — worth
  adding the same lightweight `http://localhost:5174` link pattern if desired.

## Naming history (for future readers)

Three different things have been called "Terminal" in this repo at various
points: (1) a launcher tab inside Aeon Analysis for the third-party Fincept
terminal — removed; (2) Aeon Analysis's own earlier internal branding
("Aeon Nimbus Terminal") — renamed to "Aeon Nimbus Analysis" to match its
actual header/footer branding; (3) the in-house `terminal/frontend/` scaffold,
which briefly held the "Aeon Terminal" / Execution-Layer slot in the ecosystem
while it was being built out. That slot has since been resolved: the
Execution Layer now points at a locally-installed, rebranded copy of the
vendored Fincept Terminal (`vendor/FinceptTerminal/`) — publicly called
**Nimbus Terminal** everywhere a user sees it (landing page, app name, `Info.plist`).
"Fincept Terminal" is an internal-only fact about what the app is built on,
never surfaced to users. The in-house scaffold is parked, not deleted, and is
no longer tracked as a live product. If you find a doc or comment still saying
"Terminal" and meaning Aeon Analysis, it's stale — see `docs/archive/`.

## Configuration and ports

| Service                    | Default port | Override                                                         |
| -------------------------- | ------------ | ---------------------------------------------------------------- |
| Aeon Analysis frontend     | 5173         | —                                                                |
| Aeon Analysis analytics    | 8000         | `PORT` / `AEON_ANALYTICS_PORT`; frontend `VITE_ANALYTICS_URL`    |
| Research report worker     | 8787         | frontend `VITE_WORKER_URL`                                       |
| Aeon Intelligence API      | 8003         | `PORT` / `AEON_INTEL_PORT`; Intelligence frontend `VITE_API_URL` |
| Aeon Intelligence frontend | 5175         | Analysis frontend `VITE_INTELLIGENCE_URL`                        |
| Aeon Platform              | 5174         | Analysis frontend `VITE_PLATFORM_URL`                            |
| OpenBB / TradingAgents     | 6900 / 8001  | `VITE_OPENBB_URL` / `VITE_TRADING_AGENTS_URL`                    |
| FinRobot / Deep Research   | 8002 / 8600  | `VITE_FINROBOT_URL` / `VITE_DEEP_RESEARCH_URL`                   |

Intelligence moved from 8001 to 8003 because 8001 is TradingAgents in the
Analysis terminal stack, and each launcher kills whatever holds its ports.

**Market data.** Analytics reads prices through `analytics/market_data.py`:
yfinance first, then Yahoo's chart API (no cookie/crumb, which is what cloud
hosts usually get blocked on), then Stooq. Fundamentals (DCF inputs, analyst
targets) still need yfinance; everything price-based keeps working without it.
`GET /health` reports which source answered last.

**Honest data.** Intelligence never substitutes invented data for a failed
source: news, insider trades, crypto and sentiment are real or absent (the last
real batch is kept across failed refreshes), and the Data Sources tab says why.

**Checks.** CI runs the worker/frontend unit tests, both backends' pytest
suites (`analytics/tests`, `intelligence/backend/tests`) and the Intelligence
frontend build. `.github/workflows/live-smoke.yml` calls every real upstream
from a GitHub runner weekly (and on backend PRs) and prints what each returned.

# Aeon Nimbus Intelligence - Architecture Design

## Product Positioning

**Aeon Nimbus Terminal** (Port 5173)

- Financial analysis workstation
- Compare, analyze, backtest
- On-demand research
- Desktop app feel

**Aeon Nimbus Intelligence** (Port 5175) - NEW

- Market event monitoring dashboard
- Real-time news aggregation
- D-X countdown system
- Always-on monitoring

## Data Sources - Comprehensive Coverage

### 1. Telegram Channels (Real-time)

- @Tradeul_Breaking_News ✓ (configured)
- @DeItaone (market-moving news)
- @FirstSquawk (economic data)
- @unusual_whales (options flow)
- @fxhedgers (global macro)
- @zerohedge (alternative perspective)

### 2. Economic Calendar (Scheduled Events)

**Macro Data Releases:**

- CPI (Consumer Price Index) - Monthly
- NFP (Non-Farm Payrolls) - Monthly
- GDP (Gross Domestic Product) - Quarterly
- PPI (Producer Price Index) - Monthly
- Retail Sales - Monthly
- Jobless Claims - Weekly
- PMI (Manufacturing/Services) - Monthly

**Central Bank Events:**

- FOMC Meetings (8 per year)
- ECB Meetings (8 per year)
- BOJ Meetings (8 per year)
- BOE Meetings (8 per year)

**Government Events:**

- G7/G20 Summits
- Presidential visits
- State of the Union
- Debt ceiling deadlines
- Election dates

### 3. Corporate Events (S&P 500)

- Earnings dates (all 500 companies)
- Product launches
- Investor days
- M&A announcements
- Dividend dates
- Stock splits

### 4. Geopolitical Events

- UN Security Council meetings
- NATO summits
- OPEC+ meetings
- Trade negotiations
- Sanctions announcements
- Peace talks

### 5. Commodity Events

- USDA crop reports
- EIA inventory reports
- OPEC production decisions
- Gold Council updates

## User Interface Design

### Main Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  🌐 AEON NIMBUS INTELLIGENCE                    [Settings]  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  📊 ACTIVE COUNTDOWNS (Next 30 Days)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  D-1   🔴  CPI Release           Tomorrow 8:30 AM     │  │
│  │  D-2   🟡  Apple Earnings        Oct 28, After Close │  │
│  │  D-7   🟢  FOMC Meeting          Nov 2, 2:00 PM      │  │
│  │  D-14  🔵  China GDP Report      Nov 9, 10:00 PM     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  🔴 DANGER ZONE (D-0 to D-2)     🟡 EUFORIA (D-3 to D-9)   │
│  🟢 ACCUMULATION (D-10 to D-20)  🔵 PRE-RUMOR (D-20+)      │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  📰 LIVE NEWS FEED                                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  2m ago  @Tradeul_Breaking_News                       │  │
│  │  "Fed official signals potential pause in rate cuts"  │  │
│  │  → SPY, QQQ, TLT                           [Analyze]  │  │
│  │                                                         │  │
│  │  15m ago  @DeItaone                                    │  │
│  │  "TSLA deliveries beat consensus by 12%"              │  │
│  │  → TSLA, RIVN, F                          [Analyze]  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  📅 CALENDAR VIEW    [Day] [Week] [Month]                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Mon Oct 26    TSLA Earnings (D-2)                    │  │
│  │  Tue Oct 27    • No events                            │  │
│  │  Wed Oct 28    AAPL Earnings (D-0)                    │  │
│  │  Thu Oct 29    GDP Release (D-0), CPI Flash           │  │
│  │  Fri Oct 30    NFP Report (D-0)                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Event Detail View

```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard                                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  📊 Federal Reserve FOMC Meeting                             │
│  November 2, 2026 at 2:00 PM ET                             │
│                                                               │
│  ⏱️  COUNTDOWN: D-7                                          │
│  [████████████████░░░░] 70% - ACCUMULATION PHASE            │
│                                                               │
│  🎯 AFFECTED ASSETS (Confidence Score)                       │
│  • SPY (95%) - S&P 500 Index                                │
│  • QQQ (90%) - Nasdaq 100                                   │
│  • TLT (95%) - 20+ Year Treasury ETF                        │
│  • GLD (85%) - Gold ETF                                     │
│  • UUP (80%) - US Dollar Index                              │
│                                                               │
│  📈 MARKET SENTIMENT: +25 (Mildly Bullish)                  │
│  Expectation: 25bps rate cut (85% probability)              │
│                                                               │
│  🧠 AI REASONING                                             │
│  "Currently in accumulation phase (D-7). Institutional      │
│  positioning likely underway. Market has priced in 25bps    │
│  cut but Powell's forward guidance will be key driver.      │
│  Historical pattern: SPY +1.2% avg from D-7 to D-1,         │
│  then -0.8% on announcement day (sell the news)."           │
│                                                               │
│  📊 HISTORICAL PATTERN                                       │
│  Last 5 FOMC meetings:                                      │
│  • D-7 to D-1: Avg +1.2% (4/5 times positive)              │
│  • D-0: Avg -0.8% (3/5 times negative)                     │
│  • D+1 to D+5: Avg +0.5% (3/5 times positive)              │
│                                                               │
│  💡 RECOMMENDED ACTION                                       │
│  🟢 BUY - Strong accumulation phase                         │
│  Entry window: Now through D-3                              │
│  Exit target: D-1 (before announcement)                     │
│  Risk level: Medium (guidance-dependent)                    │
│                                                               │
│  📰 RELATED NEWS (Last 7 Days)                              │
│  • Fed official signals data-dependent approach              │
│  • Inflation trending down but services sticky              │
│  • Employment remains strong above trend                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Technical Architecture

### Backend Service (Port 8001)

```python
# New dedicated service: intelligence_service.py
FastAPI(
    title="Aeon Nimbus Intelligence API",
    port=8001
)

Endpoints:
/api/events/live          # Real-time feed
/api/events/calendar      # All scheduled events
/api/events/{id}          # Event details + analysis
/api/sources/telegram     # Telegram feed status
/api/sources/calendar     # Economic calendar sync
/api/alerts/configure     # User alert rules
```

### Frontend (Port 5175)

```
intelligence-app/
├── src/
│   ├── components/
│   │   ├── CountdownGrid.tsx      # D-X countdown cards
│   │   ├── LiveFeed.tsx           # Real-time news stream
│   │   ├── CalendarView.tsx       # Month/week/day view
│   │   ├── EventDetail.tsx        # Deep dive on one event
│   │   ├── PhaseIndicator.tsx     # Color-coded phase bars
│   │   └── SentimentGauge.tsx     # Visual sentiment score
│   ├── pages/
│   │   ├── Dashboard.tsx          # Main view
│   │   ├── Calendar.tsx           # Calendar-focused
│   │   └── Analytics.tsx          # Historical patterns
│   └── services/
│       ├── telegram.ts            # WebSocket for live feed
│       ├── calendar.ts            # Event sync
│       └── analysis.ts            # Sentiment API calls
```

### Data Pipeline

```
[Telegram API] ──→ [Event Extractor] ──→ [Database]
                          ↓
                   [Sentiment Analyzer]
                          ↓
                   [Asset Mapper]
                          ↓
                   [Pattern Matcher]

[Economic Calendar APIs] ──→ [Calendar Sync] ──→ [Database]
[RSS Feeds]            ──→ [Feed Aggregator] ──→ [Database]
[Twitter/X API]        ──→ [Social Monitor]  ──→ [Database]
```

## Data Sources Implementation Priority

### Phase 1 (Week 1) - Foundation

1. ✅ Telegram @Tradeul_Breaking_News (done)
2. Economic calendar sync (Trading Economics API)
3. S&P 500 earnings dates (Yahoo Finance)

### Phase 2 (Week 2) - Expansion

4. Additional Telegram channels (5 more)
5. FOMC schedule (Federal Reserve)
6. Major geopolitical events (UN, G7)

### Phase 3 (Week 3) - Intelligence

7. Historical pattern matching
8. Sentiment correlation
9. Smart alert rules

### Phase 4 (Week 4) - Polish

10. Mobile app
11. Export/sharing
12. Portfolio integration

## Shall I proceed with building Aeon Nimbus Intelligence as a separate application?

Next steps:

1. Create new project structure at /Users/lijie/aeon-ai/intelligence/
2. Build dedicated FastAPI service (port 8001)
3. Create React dashboard (port 5175)
4. Integrate all data sources
5. Deploy alongside Terminal

This gives you:

- Terminal at localhost:5173 (analysis workstation)
- Intelligence at localhost:5175 (event monitoring)
- Platform at localhost:5174 (research reports)

Three distinct products in the Aeon Nimbus ecosystem.

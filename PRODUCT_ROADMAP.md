# Aeon Nimbus Terminal - Product Roadmap

## Current State Assessment

### ✅ What's Working

- Analytics API running on port 8000
- Terminal frontend on port 5173
- Telegram monitor authenticated and connected
- Database initialized with 1 event
- All 5 new tabs integrated (Compare, Alerts, History, Watchlist, Rumor/News)

### ⚠️ Critical Gaps Identified

1. **No actual data flowing** - 0 analyses, 0 alerts despite system running
2. **Telegram monitor silent** - Connected but no events captured yet
3. **User journey unclear** - What should user do first?
4. **No visual feedback** - User doesn't know if Telegram is working
5. **Missing integration** - Features work independently, not as ecosystem

---

## Phase 1: IMMEDIATE FIXES (Make It Actually Work)

### 1.1 Real-Time System Status Dashboard

**Problem:** User can't tell if Telegram is working or receiving events
**Solution:** Live status widget showing:

```
🟢 Telegram: Connected | Last event: 2 minutes ago
🟢 Analytics: Healthy | Response time: 45ms
🟢 Database: 47 events stored | 12 analyzed
⚡ Live Feed: Watching @Tradeul_Breaking_News
```

### 1.2 Sample Data on First Launch

**Problem:** Empty state is confusing
**Solution:** Pre-populate with 10 historical events:

- Apple earnings (D-3)
- Fed meeting (D-7)
- NVIDIA product launch (D-14)
- Tesla delivery numbers (D-21)
  Shows user what to expect

### 1.3 Welcome Flow with Quick Win

**Problem:** User lands on empty Terminal, doesn't know what to do
**Solution:**

1. Show onboarding wizard
2. Offer "Try a demo analysis" button
3. Auto-run AAPL analysis to show all features
4. Then guide to Compare, Rumor/News tabs

### 1.4 Telegram Event Validation

**Problem:** Monitor connected but no events flowing
**Solution:**

- Add test mode that simulates events
- Verify channel name is correct
- Add webhook to manually inject events
- Log all incoming messages to debug

---

## Phase 2: DATA SOURCES EXPANSION

### 2.1 Additional News Sources

**Twitter/X Integration:**

- @DeItaone (market news)
- @FirstSquawk (breaking economic data)
- @unusual_whales (options flow)
- @fxhedgers (global macro)

**RSS Feeds:**

- Bloomberg market news
- Reuters business wire
- SEC Edgar filings (8-K)
- Federal Reserve statements

**API Sources:**

- News API (newsapi.org) - 100 sources
- Alpha Vantage news sentiment
- Finnhub news feed
- Benzinga news API

### 2.2 Economic Calendar Integration

**Problem:** Missing scheduled events
**Solution:** Auto-import from:

- Trading Economics API
- Forex Factory
- Investing.com calendar
- Federal Reserve calendar

Pre-populate events 30 days ahead with:

- CPI, NFP, GDP releases
- Earnings dates (all S&P 500)
- Fed meetings
- G7 summits

### 2.3 Social Sentiment Aggregator

**Reddit sentiment:**

- r/wallstreetbets
- r/investing
- r/stocks

**StockTwits API:**

- Real-time retail sentiment
- Volume + sentiment score per ticker

**Options Flow:**

- Unusual Whales API
- Large trade alerts
- Dark pool prints

---

## Phase 3: INTELLIGENCE LAYER

### 3.1 Smart Event Correlation

**Connect the dots:**

```
Event: "TSLA earnings D-2"
Related events:
  - EV subsidy vote (D-5)
  - China factory output (D-10)
  - Competitor NIO earnings (D-15)
Correlation score: 0.87 (High)
```

### 3.2 Pattern Recognition

**Learn from history:**

- "Last 5 Fed meetings → SPY -2.3% avg on announcement"
- "AAPL earnings beat → typically +4.2% in 3 days"
- "CPI above expectations → TLT -1.8% same day"

### 3.3 Predictive Scoring

**ML model that scores:**

- Probability event moves market (0-100%)
- Expected magnitude (± $X or ±X%)
- Affected tickers ranked by impact
- Recommended entry/exit windows

### 3.4 Smart Alerts

**Beyond simple price alerts:**

- "3 negative macro events converging on SPY (D-5 to D-2)"
- "Sentiment shifted from +40 to -20 in 48h for TSLA"
- "Unusual volume + negative news = potential breakdown"

---

## Phase 4: USER EXPERIENCE POLISH

### 4.1 Unified Command Center

**Problem:** Features scattered across tabs
**Solution:** Single dashboard showing:

- Active rumor/news events (top 5)
- Watchlist live tickers
- Triggered alerts
- Recent analyses
- Live news feed
  All in one glance

### 4.2 Natural Language Interface

**Type:** "What's the sentiment on tech stocks this week?"
**Get:** Aggregated sentiment across AAPL, MSFT, GOOGL, NVDA, META with reasoning

**Type:** "Compare AAPL vs MSFT for next earnings"
**Get:** Side-by-side with D-X countdowns and historical patterns

### 4.3 Mobile Companion App

**Push notifications to phone:**

- Triggered alerts
- Breaking news matched to watchlist
- Daily market sentiment summary
- D-1 countdown warnings

### 4.4 Export & Sharing

**Generate reports:**

- PDF: "Weekly Market Sentiment Report"
- Twitter: Auto-post analysis with charts
- Discord webhook: Alert team channel
- Email: Daily digest to inbox

---

## Phase 5: ADVANCED FEATURES

### 5.1 Portfolio Integration

**Connect brokerage:**

- Import positions from Interactive Brokers, Robinhood, etc.
- Auto-match events to holdings
- "You hold AAPL - earnings in D-3 (DANGER ZONE)"
- Risk score based on upcoming events

### 5.2 Backtesting Engine

**Test strategies:**

- "Buy all stocks D-10 before earnings, sell D-1"
- "Short on negative macro events D-0"
- "Buy the dip when sentiment hits -80"
  Show P&L, win rate, Sharpe ratio

### 5.3 Multi-Asset Support

**Beyond stocks:**

- Crypto (BTC, ETH events)
- Forex (USD/EUR macro drivers)
- Commodities (Gold, Oil supply events)
- Bonds (Yield curve inversions)

### 5.4 Collaborative Features

**Team mode:**

- Shared watchlists
- Comment on events
- Vote on sentiment (crowdsource)
- Leaderboard of best predictions

---

## Phase 6: PRODUCTIZATION

### 6.1 Three Tiers

**Free:**

- 5 watchlist tickers
- 10 alerts
- 7-day event history
- Basic sentiment

**Pro ($29/mo):**

- Unlimited everything
- All data sources
- Mobile app
- API access
- Priority support

**Institutional ($499/mo):**

- Multi-user teams
- Custom data sources
- Backtesting engine
- White-label option
- Dedicated account manager

### 6.2 Landing Page Improvements

**Current:** Basic description
**Needed:**

- Video demo (30 seconds)
- Live sentiment ticker
- Social proof ("Used by 10,000+ traders")
- ROI calculator
- 14-day free trial

### 6.3 Onboarding Optimization

**Reduce time to value:**

1. Sign up → 30 seconds
2. Connect Telegram → 1 minute
3. First analysis → 2 minutes
4. See first event alert → Immediate

**Goal:** 5 minutes to "wow moment"

### 6.4 Analytics & Metrics

**Track:**

- Daily active users
- Events per day
- Alerts triggered
- Analyses run
- Conversion funnel
- Churn rate
- Feature usage

---

## Implementation Priority

### Week 1 (Critical Path)

1. ✅ System status dashboard
2. ✅ Sample data seeding
3. ✅ Telegram event validation
4. ✅ Unified command center tab

### Week 2 (Data Sources)

5. ⬜ Twitter integration
6. ⬜ Economic calendar import
7. ⬜ News API integration
8. ⬜ RSS feed aggregator

### Week 3 (Intelligence)

9. ⬜ Event correlation engine
10. ⬜ Pattern recognition
11. ⬜ Smart alerts

### Week 4 (Polish)

12. ⬜ Natural language interface
13. ⬜ Export & sharing
14. ⬜ Mobile push notifications

---

## Success Metrics

**Technical:**

- 99.9% uptime
- <100ms API response time
- Events captured within 30 seconds of posting
- 95%+ sentiment accuracy

**Business:**

- 1,000 daily active users (Month 1)
- 10,000 DAU (Month 3)
- $50K MRR (Month 6)
- 80% user retention

**User:**

- 5-minute onboarding
- 10+ events analyzed per user per day
- 50+ alerts triggered per day
- 4.5+ star rating

---

## Next Steps

Ready to implement Week 1 critical path:

1. System status dashboard widget
2. Sample data seeding script
3. Telegram event debugger
4. Unified command center tab

Shall I proceed?

"""
Calendar Sync - Seeds economic calendar with major events
Includes data from multiple sources: Fed, BLS, ECB, BOJ

Where a source publishes a real fixed schedule (FOMC, CPI/NFP/PPI, ECB, BOJ),
the dates below are hardcoded from that published 2026 calendar, not
guessed — see the source comment above each block. These need a yearly
refresh (re-pull each schedule once the source publishes next year's dates).

Events with no publicly fixed schedule this far out (OPEC+, G7, debt-ceiling
deadlines, GDP advance estimate, retail sales) are still date-estimated via a
heuristic offset from today, and are labeled "(estimated date)" in their title
so the UI's D-day countdown isn't read as more precise than it actually is.
Individual company earnings dates attempt a real fetch (real_data.get_earnings_date,
Yahoo Finance calendarEvents) first and only fall back to the same kind of
heuristic-offset placeholder, honestly labeled, when that fetch fails.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path

import real_data


def seed_calendar():
    """Seed calendar with major economic events"""

    db_path = Path(os.environ.get("AEON_INTEL_DB_PATH", str(Path.home() / ".aeon" / "intelligence.db")))
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    # Clear existing events
    c.execute('DELETE FROM events')

    now = datetime.now()
    events = []

    # FOMC Meetings — real 2026 schedule (federalreserve.gov/monetarypolicy/fomccalendars.htm).
    # Decision announced on the second day of each two-day meeting, 2:00pm ET.
    fomc_dates = [
        datetime(2026, 1, 28, 14, 0),
        datetime(2026, 3, 18, 14, 0),
        datetime(2026, 4, 29, 14, 0),
        datetime(2026, 6, 17, 14, 0),
        datetime(2026, 7, 29, 14, 0),
        datetime(2026, 9, 16, 14, 0),
        datetime(2026, 10, 28, 14, 0),
        datetime(2026, 12, 9, 14, 0),
    ]
    for date in fomc_dates:
        events.append({
            'title': 'FOMC Meeting Decision',
            'description': 'Federal Reserve announces interest rate decision and monetary policy outlook',
            'date': date.isoformat(),
            'event_type': 'macro',
            'affected_tickers': 'SPY,QQQ,IWM,DIA,TLT,GLD,DXY',
            'impact_score': 9.5
        })

    # NFP (Employment Situation) — real 2026 schedule (bls.gov/schedule/2026/home.htm), 8:30am ET.
    nfp_dates = [
        datetime(2026, 1, 9), datetime(2026, 2, 11), datetime(2026, 3, 6),
        datetime(2026, 4, 3), datetime(2026, 5, 8), datetime(2026, 6, 5),
        datetime(2026, 7, 2), datetime(2026, 8, 7), datetime(2026, 9, 4),
        datetime(2026, 10, 2), datetime(2026, 11, 6), datetime(2026, 12, 4),
    ]
    for date in nfp_dates:
        events.append({
            'title': 'Non-Farm Payrolls (NFP)',
            'description': 'Monthly employment report - key labor market indicator',
            'date': date.replace(hour=8, minute=30).isoformat(),
            'event_type': 'macro',
            'affected_tickers': 'SPY,QQQ,DXY,GLD',
            'impact_score': 9.0
        })

    # CPI — real 2026 schedule (bls.gov/schedule/2026/home.htm), 8:30am ET.
    cpi_dates = [
        datetime(2026, 1, 13), datetime(2026, 2, 13), datetime(2026, 3, 11),
        datetime(2026, 4, 10), datetime(2026, 5, 12), datetime(2026, 6, 10),
        datetime(2026, 7, 14), datetime(2026, 8, 12), datetime(2026, 9, 11),
        datetime(2026, 10, 14), datetime(2026, 11, 10), datetime(2026, 12, 10),
    ]
    for date in cpi_dates:
        events.append({
            'title': 'Consumer Price Index (CPI)',
            'description': 'Monthly inflation data - crucial for Fed policy',
            'date': date.replace(hour=8, minute=30).isoformat(),
            'event_type': 'macro',
            'affected_tickers': 'SPY,QQQ,TLT,GLD,DXY',
            'impact_score': 9.0
        })

    # PPI — real 2026 schedule (bls.gov/schedule/2026/home.htm), 8:30am ET.
    ppi_dates = [
        datetime(2026, 1, 14), datetime(2026, 1, 30), datetime(2026, 2, 27),
        datetime(2026, 3, 18), datetime(2026, 4, 14), datetime(2026, 5, 13),
        datetime(2026, 6, 11), datetime(2026, 7, 15), datetime(2026, 8, 13),
        datetime(2026, 9, 10), datetime(2026, 10, 15), datetime(2026, 11, 13),
        datetime(2026, 12, 15),
    ]
    for date in ppi_dates:
        events.append({
            'title': 'Producer Price Index (PPI)',
            'description': 'Wholesale inflation indicator',
            'date': date.replace(hour=8, minute=30).isoformat(),
            'event_type': 'macro',
            'affected_tickers': 'SPY,QQQ,DXY',
            'impact_score': 7.0
        })

    # ECB Governing Council — real remaining-2026 schedule (ecb.europa.eu press calendar).
    # Announced on the second day, 13:45 CET press conference.
    for date in [datetime(2026, 10, 29, 13, 45), datetime(2026, 12, 17, 13, 45)]:
        events.append({
            'title': 'ECB Interest Rate Decision',
            'description': 'European Central Bank monetary policy announcement',
            'date': date.isoformat(),
            'event_type': 'macro',
            'affected_tickers': 'EURUSD,DXY,SPY',
            'impact_score': 7.5
        })

    # Bank of Japan — real remaining-2026 schedule (boj.or.jp meeting calendar).
    # Decision typically announced on the second day, afternoon JST (~22:00 prior-day ET).
    for date in [datetime(2026, 10, 30, 22, 0), datetime(2026, 12, 18, 22, 0)]:
        events.append({
            'title': 'Bank of Japan Policy Meeting',
            'description': 'BOJ interest rate and yield curve control decision',
            'date': date.isoformat(),
            'event_type': 'macro',
            'affected_tickers': 'USDJPY,DXY,EWJ',
            'impact_score': 7.0
        })

    # ── Events below have no publicly fixed schedule this far out — dates are
    # a best-effort heuristic offset from today, not sourced from a real
    # calendar. Titles say "(estimated date)" so the countdown isn't mistaken
    # for a confirmed one. ──────────────────────────────────────────────────

    # GDP (Quarterly advance estimate) — BEA doesn't publish next-quarter dates
    # this far ahead; ~30 days out is a rough placeholder.
    gdp_date = now + timedelta(days=30)
    events.append({
        'title': 'GDP Report (Advance) — estimated date',
        'description': 'Quarterly economic growth data. Exact BEA release date not yet confirmed; shown date is an estimate.',
        'date': gdp_date.replace(hour=8, minute=30).isoformat(),
        'event_type': 'macro',
        'affected_tickers': 'SPY,QQQ,DXY',
        'impact_score': 8.5
    })

    # Retail Sales (Monthly) — Census Bureau's exact day varies each month;
    # mid-month is a rough placeholder, not the confirmed release date.
    for month_offset in [0, 1, 2]:
        retail_date = (now.replace(day=1) + timedelta(days=32 * month_offset)).replace(day=15)
        events.append({
            'title': 'Retail Sales — estimated date',
            'description': 'Monthly consumer spending data. Exact Census Bureau release date not yet confirmed; shown date is an estimate.',
            'date': retail_date.replace(hour=8, minute=30).isoformat(),
            'event_type': 'macro',
            'affected_tickers': 'SPY,XRT,AMZN,WMT',
            'impact_score': 7.5
        })

    # Major Tech Earnings — try a real per-ticker earnings date first (Yahoo
    # Finance calendarEvents); only fall back to the offset-guess placeholder,
    # clearly labeled "(estimated date)", when the real fetch fails.
    earnings_date = now + timedelta(days=21)
    tech_earnings = [
        ('AAPL', 'Apple Q4 Earnings', 'iPhone sales, Services revenue, China growth'),
        ('MSFT', 'Microsoft Q4 Earnings', 'Azure cloud growth, AI investments'),
        ('NVDA', 'NVIDIA Q4 Earnings', 'AI chip demand, datacenter revenue'),
        ('TSLA', 'Tesla Q4 Earnings', 'Vehicle deliveries, FSD progress, margins'),
        ('GOOGL', 'Alphabet Q4 Earnings', 'Search revenue, YouTube ads, Cloud growth'),
        ('META', 'Meta Q4 Earnings', 'Ad revenue, AI spending, Reality Labs'),
        ('AMZN', 'Amazon Q4 Earnings', 'AWS growth, retail margins, Prime growth'),
    ]
    for i, (ticker, title, desc) in enumerate(tech_earnings):
        real_date_iso = real_data.get_earnings_date(ticker)
        if real_date_iso:
            events.append({
                'title': title,
                'description': desc,
                'date': real_date_iso,
                'event_type': 'earnings',
                'affected_tickers': ticker,
                'impact_score': 8.5 if ticker in ['AAPL', 'NVDA', 'TSLA'] else 8.0
            })
        else:
            events.append({
                'title': f'{title} — estimated date',
                'description': f'{desc}. Exact reporting date not yet confirmed by the company; shown date is a placeholder.',
                'date': (earnings_date + timedelta(days=i)).replace(hour=16, minute=0).isoformat(),
                'event_type': 'earnings',
                'affected_tickers': ticker,
                'impact_score': 8.5 if ticker in ['AAPL', 'NVDA', 'TSLA'] else 8.0
            })

    # Oil & Energy — EIA publishes weekly, always Wednesday 10:30am ET; the
    # weekday/time is real, we just walk forward week by week from today.
    for week in range(0, 12, 1):
        eia_date = now + timedelta(weeks=week)
        while eia_date.weekday() != 2:  # 2 = Wednesday
            eia_date += timedelta(days=1)

        events.append({
            'title': 'EIA Crude Oil Inventories',
            'description': 'Weekly petroleum status report',
            'date': eia_date.replace(hour=10, minute=30).isoformat(),
            'event_type': 'commodity',
            'affected_tickers': 'USO,XLE,CVX,XOM',
            'impact_score': 6.5
        })

    # OPEC+ Meeting — scheduled irregularly by the group itself, no public
    # calendar to source this far ahead.
    opec_date = now + timedelta(days=45)
    events.append({
        'title': 'OPEC+ Production Meeting — estimated date',
        'description': 'Oil production quota decision. OPEC+ has not announced a confirmed date this far ahead; shown date is a placeholder.',
        'date': opec_date.replace(hour=12, minute=0).isoformat(),
        'event_type': 'commodity',
        'affected_tickers': 'USO,XLE,CVX,XOM,BNO',
        'impact_score': 8.0
    })

    # Geopolitical — G7 summit dates rotate by host country and aren't fixed
    # this far ahead in a single public source we pull from.
    g7_date = now + timedelta(days=60)
    events.append({
        'title': 'G7 Summit — estimated date',
        'description': 'Major economic powers meeting - trade, sanctions, policy coordination. Exact date not yet confirmed; shown date is a placeholder.',
        'date': g7_date.replace(hour=9, minute=0).isoformat(),
        'event_type': 'geopolitical',
        'affected_tickers': 'SPY,DXY,GLD',
        'impact_score': 7.0
    })

    # US Political — depends on Treasury's "X-date" projections, which move
    # with tax receipts; no fixed date to source ahead of time.
    debt_date = now + timedelta(days=75)
    events.append({
        'title': 'US Debt Ceiling Deadline — estimated date',
        'description': 'Congress must raise debt limit to avoid default. Exact Treasury X-date not yet confirmed; shown date is a placeholder.',
        'date': debt_date.replace(hour=12, minute=0).isoformat(),
        'event_type': 'political',
        'affected_tickers': 'SPY,TLT,GLD,DXY',
        'impact_score': 8.5
    })

    # Insert all events
    for event in events:
        c.execute('''
            INSERT INTO events (title, description, date, event_type, affected_tickers, impact_score)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            event['title'],
            event['description'],
            event['date'],
            event['event_type'],
            event['affected_tickers'],
            event['impact_score']
        ))

    conn.commit()
    conn.close()

    print(f"✅ Seeded {len(events)} events into calendar")
    return len(events)


if __name__ == "__main__":
    count = seed_calendar()
    print(f"Calendar sync complete: {count} events loaded")

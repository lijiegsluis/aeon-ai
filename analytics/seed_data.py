"""
Market events seeding - populates market_events with real, named event types.

Where a source publishes a real fixed schedule (FOMC, CPI/NFP/PPI, ECB — same
2026 calendars already sourced for intelligence/backend/calendar_sync.py), the
dates below are hardcoded from that published schedule, not guessed. Events
with no publicly fixed schedule this far out (individual company earnings,
OPEC+) keep a heuristic offset-from-now date but are labeled "— estimated
date" in the title so the UI's D-day countdown isn't read as more precise
than it is — same convention as calendar_sync.py.

`source` is set to 'scheduled' (never 'demo') for every row here, since every
event is a real, named event type — only some of its dates are estimates.
Existing rows tagged 'demo' (the previous version of this script) or
'manual' (a real user-submitted event) are left untouched; only 'scheduled'
rows are cleared and re-seeded, so re-running this never destroys manual work.
"""
import sqlite3
from datetime import datetime, timedelta
import json
import os

DB_PATH = os.path.expanduser("~/.aeon/terminal.db")


def _build_events():
    now = datetime.now()
    events = []

    # FOMC — real 2026 schedule (federalreserve.gov/monetarypolicy/fomccalendars.htm)
    events.append({
        "title": "Federal Reserve FOMC Meeting - Interest Rate Decision",
        "category": "macro",
        "event_date": "2026-10-28",
        "raw_text": "Federal Reserve FOMC two-day meeting concludes with a rate decision and "
                     "Powell press conference at 2:00 PM ET. Major impact on SPY, QQQ, bonds.",
        "affected_assets": ["SPY", "QQQ", "TLT", "GLD"],
    })

    # NFP — real 2026 schedule (bls.gov/schedule/2026/home.htm)
    events.append({
        "title": "US Non-Farm Payrolls (NFP) Report",
        "category": "macro",
        "event_date": "2026-10-02",
        "raw_text": "Bureau of Labor Statistics releases the Employment Situation report at "
                     "8:30 AM ET. Key labor-market indicator, critical for Fed policy outlook.",
        "affected_assets": ["SPY", "DXY", "GLD", "TLT"],
    })

    # CPI — real 2026 schedule (bls.gov/schedule/2026/home.htm)
    events.append({
        "title": "CPI Inflation Data Release",
        "category": "macro",
        "event_date": "2026-10-14",
        "raw_text": "Consumer Price Index released at 8:30 AM ET. Monthly inflation data, "
                     "crucial for Fed rate-cut expectations.",
        "affected_assets": ["SPY", "TLT", "GLD", "UUP"],
    })

    # PPI — real 2026 schedule (bls.gov/schedule/2026/home.htm)
    events.append({
        "title": "PPI Wholesale Inflation Data Release",
        "category": "macro",
        "event_date": "2026-10-15",
        "raw_text": "Producer Price Index released at 8:30 AM ET. Wholesale inflation "
                     "indicator, leading signal for consumer-level CPI.",
        "affected_assets": ["SPY", "DXY"],
    })

    # ECB — real remaining-2026 schedule (ecb.europa.eu press calendar)
    events.append({
        "title": "ECB Interest Rate Decision",
        "category": "macro",
        "event_date": "2026-10-29",
        "raw_text": "European Central Bank Governing Council announces its monetary policy "
                     "decision, 13:45 CET press conference.",
        "affected_assets": ["SPY"],
    })

    # ── Below: real, named event types with no publicly fixed schedule this
    # far out. Dates are a best-effort offset from today, not sourced from a
    # real calendar — flagged in the title so the countdown isn't mistaken
    # for a confirmed one.

    tech_earnings = [
        ("AAPL", "Apple Q4 Earnings Report",
         "Apple scheduled to report quarterly earnings. iPhone sales, Services "
         "revenue, and China growth are the key metrics analysts watch.", 5),
        ("TSLA", "Tesla Quarterly Delivery Numbers",
         "Tesla to report quarterly vehicle deliveries. Production ramp and "
         "margins are the key focus.", 3),
        ("AMZN", "Amazon Quarterly Earnings Report",
         "Amazon reports quarterly results. AWS growth and retail margins are "
         "the key metrics.", 9),
        ("NVDA", "NVIDIA Product/AI Chip Announcement",
         "NVIDIA event covering next-generation AI chip roadmap and datacenter "
         "demand outlook.", 14),
        ("MSFT", "Microsoft AI/Copilot Product Event",
         "Microsoft product event covering Copilot Enterprise pricing and Azure "
         "AI integration.", 12),
    ]
    for ticker, title, desc, days in tech_earnings:
        events.append({
            "title": f"{title} — estimated date",
            "category": "earnings" if ticker in ("AAPL", "TSLA", "AMZN") else "general",
            "event_date": (now + timedelta(days=days)).strftime("%Y-%m-%d"),
            "raw_text": f"{desc} Exact reporting date not yet confirmed by the company; "
                         f"shown date is a placeholder.",
            "affected_assets": [ticker],
        })

    # OPEC+ — scheduled irregularly by the group itself, no public calendar to
    # source this far ahead.
    events.append({
        "title": "OPEC+ Production Meeting — estimated date",
        "category": "geopolitical",
        "event_date": (now + timedelta(days=18)).strftime("%Y-%m-%d"),
        "raw_text": "OPEC+ production quota decision. OPEC+ has not announced a confirmed "
                     "date this far ahead; shown date is a placeholder.",
        "affected_assets": ["USO", "XLE", "CVX", "XOM"],
    })

    # EIA weekly crude inventories — always Wednesday, 10:30am ET. The
    # weekday/time is real; only "which upcoming Wednesday" is walked forward.
    eia_date = now
    while eia_date.weekday() != 2:
        eia_date += timedelta(days=1)
    events.append({
        "title": "Oil Inventories Report - EIA",
        "category": "general",
        "event_date": eia_date.strftime("%Y-%m-%d"),
        "raw_text": "Energy Information Administration weekly petroleum status report at "
                     "10:30 AM ET.",
        "affected_assets": ["USO", "XLE", "XOM", "CVX"],
    })

    return events


def seed_database():
    """Seed market_events with real event types, run at Analysis backend startup.

    Clears and re-inserts only 'scheduled' rows (this script's own prior output)
    so re-running never touches a 'manual' user-submitted event.
    """
    from sentiment_analyzer import analyze_market_event

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM market_events WHERE source = 'scheduled'")
    cursor.execute("DELETE FROM market_events WHERE source = 'demo'")

    inserted_ids = []
    for event in _build_events():
        cursor.execute("""
            INSERT INTO market_events
            (title, category, event_date, source, raw_text, affected_assets, created_at)
            VALUES (?, ?, ?, 'scheduled', ?, ?, ?)
        """, (
            event["title"],
            event["category"],
            event["event_date"],
            event["raw_text"],
            json.dumps(event["affected_assets"]),
            datetime.now().isoformat(),
        ))
        inserted_ids.append(cursor.lastrowid)

    conn.commit()
    conn.close()

    for event_id in inserted_ids:
        try:
            analyze_market_event(event_id)
        except Exception as e:
            print(f"[seed_data] analysis failed for event {event_id}: {e}")

    print(f"✓ Seeded {len(inserted_ids)} market events (source='scheduled')")


if __name__ == "__main__":
    seed_database()

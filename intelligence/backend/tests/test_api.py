"""API behaviour with every network source stubbed out."""
import pytest
from fastapi.testclient import TestClient

import calendar_sync
import intelligence_service as svc
import real_data


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """Every upstream fails, as it would with no network."""
    for name in ("get_real_news", "get_recent_form4_trades"):
        monkeypatch.setattr(real_data, name, lambda *a, **k: [])
    for name in ("get_crypto_prices", "get_fear_greed", "get_reddit_sentiment", "get_vix",
                 "get_current_price", "get_earnings_date"):
        monkeypatch.setattr(real_data, name, lambda *a, **k: None)
    monkeypatch.setattr(real_data, "get_fomc_schedule", lambda: {})
    import alpha_data
    monkeypatch.setattr(alpha_data, "earnings_between", lambda *a, **k: [])
    monkeypatch.setattr(alpha_data, "next_earnings", lambda t: None)
    monkeypatch.setattr(real_data, "get_bls_schedule", lambda: {})


@pytest.fixture()
def client():
    # No `with` block: the startup hooks (network sync threads) stay off.
    return TestClient(svc.app)


def test_no_fabricated_data_when_every_source_fails(monkeypatch):
    monkeypatch.setattr(svc, "NEWS", [])
    monkeypatch.setattr(svc, "CRYPTO", [])
    monkeypatch.setattr(svc, "SENTIMENT", [])
    monkeypatch.setattr(svc, "INSIDER_TRADES", [])
    assert svc.generate_news() == []
    assert svc.generate_crypto() == []
    assert svc.generate_sentiment() == []
    trades, fresh = svc.generate_insider_trades()
    assert trades == [] and fresh is False


def test_failed_refresh_keeps_last_real_batch(monkeypatch):
    real = [{"id": 1, "title": "Real headline", "source": "MarketWatch"}]
    monkeypatch.setattr(svc, "NEWS", real)
    assert svc.generate_news() is real


def test_manual_events_survive_calendar_resync(client):
    r = client.post("/api/events", json={"title": "Investor day", "event_type": "earnings",
                                          "date": "2099-01-15", "affected_tickers": ["msft"]})
    assert r.status_code == 200
    calendar_sync.seed_calendar()
    with svc.get_db() as conn:
        row = conn.execute("SELECT affected_tickers, source FROM events WHERE title = 'Investor day'").fetchone()
    assert row["source"] == "manual" and row["affected_tickers"] == "MSFT"


def test_event_date_is_validated(client):
    r = client.post("/api/events", json={"title": "x", "event_type": "macro", "date": "next tuesday"})
    assert r.status_code == 422


def test_only_manual_events_can_be_deleted(client):
    calendar_sync.seed_calendar()
    with svc.get_db() as conn:
        seeded_id = conn.execute("SELECT id FROM events WHERE source = 'calendar' LIMIT 1").fetchone()["id"]
    assert client.delete(f"/api/events/{seeded_id}").status_code == 409
    new_id = client.post("/api/events", json={"title": "Temp", "event_type": "macro", "date": "2099-02-01"}).json()["id"]
    assert client.delete(f"/api/events/{new_id}").status_code == 200
    assert client.delete(f"/api/events/{new_id}").status_code == 404


def test_calendar_times_have_no_stray_seconds():
    calendar_sync.seed_calendar()
    with svc.get_db() as conn:
        dates = [r["date"] for r in conn.execute("SELECT date FROM events WHERE source = 'calendar'")]
    assert dates and all(len(d) == 19 and d.endswith(":00") for d in dates)


def test_alert_rules_respect_category_and_ticker_filters(client):
    client.post("/api/events", json={"title": "NVDA product day", "event_type": "general",
                                      "date": _days_from_now(5), "affected_tickers": ["NVDA"]})
    client.post("/api/events", json={"title": "AAPL earnings (test)", "event_type": "earnings",
                                      "date": _days_from_now(6), "affected_tickers": ["AAPL"]})
    rule = client.post("/api/alerts", json={"event_category": "earnings", "min_days_before": 0,
                                            "max_days_before": 10, "assets_filter": ["aapl"]}).json()["id"]
    msgs = [t["event"]["title"] for t in client.get("/api/alerts/triggered").json()["triggered"] if t["rule_id"] == rule]
    assert msgs == ["AAPL earnings (test)"]
    assert any(r["id"] == rule for r in client.get("/api/alerts").json()["rules"])
    assert client.delete(f"/api/alerts/{rule}").status_code == 200
    assert all(r["id"] != rule for r in client.get("/api/alerts").json()["rules"])


def test_ticker_lens(client):
    client.post("/api/events", json={"title": "COIN earnings (test)", "event_type": "earnings",
                                      "date": _days_from_now(12), "affected_tickers": ["COIN"]})
    d = client.get("/api/ticker/coin").json()
    assert d["ticker"] == "COIN"
    assert d["timing"]["phase"] == "accumulation"
    assert [e["title"] for e in d["events"]] == ["COIN earnings (test)"]
    assert client.get("/api/ticker/bad$ticker").status_code == 400


def test_thirteen_f_deadline_is_a_real_quarter_deadline():
    note = svc.generate_smart_money_notifications()["future_expected"][0]
    assert note["timestamp"][5:10] in {"02-14", "05-15", "08-14", "11-14"}


def _days_from_now(n):
    from datetime import datetime, timedelta
    return (datetime.now() + timedelta(days=n)).strftime("%Y-%m-%d")

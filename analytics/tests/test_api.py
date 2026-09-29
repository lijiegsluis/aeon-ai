from datetime import date, timedelta


def test_quote_and_dividend_yield_is_a_fraction(client):
    q = client.get("/market/quote/AAPL").json()
    assert q["price"] == 200.0 and q["dividendYield"] == 0.0046


def test_quote_works_from_chart_only_data(client):
    q = client.get("/market/quote/CHART").json()
    assert q["price"] == 50.0 and q["source"] == "yahoo-chart"


def test_dcf_refuses_negative_fcf_and_missing_fundamentals(client):
    assert client.get("/quant/dcf/BURN").status_code == 422
    assert client.get("/quant/dcf/CHART").status_code == 503
    d = client.get("/quant/dcf/AAPL").json()
    assert d["scenarios"]["bear"]["fairValue"] < d["scenarios"]["base"]["fairValue"] < d["scenarios"]["bull"]["fairValue"]


def test_montecarlo_and_markowitz(client):
    mc = client.get("/quant/montecarlo/AAPL?sims=2000").json()
    assert 0 <= mc["probUp"] <= 100 and mc["percentiles"]["p5"] < mc["percentiles"]["p95"]
    mk = client.get("/quant/markowitz?tickers=AAPL,MSFT,NVDA").json()
    assert abs(sum(mk["optimal"]["weights"].values()) - 100) < 0.5
    assert mk["optimal"]["riskFree"] == 4.2


def test_fusion_ensemble_labels_real_growth(client):
    e = client.get("/fusion/valuation/AAPL").json()
    assert "dcf" in e["models"] and "8.0% growth fading" in e["models"]["dcf"]["philosophy"]


def test_price_cross_check_uses_an_independent_source(client, monkeypatch):
    import main
    monkeypatch.setattr(main, "nasdaq_quote", lambda t: 200.4)
    q = client.get("/fusion/quote/AAPL").json()
    assert q["sources"] == {"yfinance-direct": 200.0, "nasdaq": 200.4} and q["verified"] is True


def test_thesis_gate_rejects_path_traversal(client):
    body = {"ticker": "../../etc/x", "edge": "e", "catalyst": "c", "entry": "1", "target": "2",
            "stop": "0.5", "size": "4%", "kill": "k"}
    assert client.post("/houston/gates", json=body).status_code == 400
    body["ticker"] = "aapl"
    assert client.post("/houston/gates", json=body).json()["file"].startswith("AAPL-")


def test_houston_run_builds_native_brief(client):
    r = client.post("/houston/run").json()
    assert r["native"] and r["brief"].startswith("# Aeon Morning Brief")


def test_alerts_validate_and_fire_once(client):
    bad = client.post("/api/alerts", json={"ticker": "AAPL", "condition_type": "moon", "threshold": 1, "user_id": 1})
    assert bad.status_code == 422
    aid = client.post("/api/alerts", json={"ticker": "aapl", "condition_type": "price_above",
                                            "threshold": 150, "user_id": 1}).json()["id"]
    first = client.post("/api/alerts/check").json()
    assert [t["id"] for t in first["triggered"]] == [aid]
    assert client.post("/api/alerts/check").json()["count"] == 0
    assert client.get("/api/alerts/triggered").json()["alerts"][0]["id"] == aid


def test_watchlists_validate_delete_and_analyze(client):
    assert client.post("/api/watchlists", json={"name": "x", "tickers": ["$$$"], "user_id": 1}).status_code == 422
    wid = client.post("/api/watchlists", json={"name": " Core ", "tickers": ["aapl", "AAPL", "burn"], "user_id": 1}).json()["id"]
    wl = [w for w in client.get("/api/watchlists?user_id=1").json()["watchlists"] if w["id"] == wid][0]
    assert wl["tickers"] == ["AAPL", "BURN"] and wl["name"] == "Core"
    res = client.post(f"/api/watchlists/{wid}/analyze").json()["results"]
    assert {r["ticker"]: r["status"] for r in res} == {"AAPL": "success", "BURN": "success"}
    assert client.delete(f"/api/watchlists/{wid}").status_code == 200
    assert client.delete(f"/api/watchlists/{wid}").status_code == 404


def test_analysis_history_delete(client):
    aid = client.post("/api/analyses/save", json={"ticker": "AAPL", "result": {"ticker": "AAPL"}}).json()["id"]
    assert client.delete(f"/api/analyses/{aid}").status_code == 200
    assert client.get(f"/api/analyses/{aid}").status_code == 404


def test_market_events_hide_past_and_can_be_deleted(client):
    past = (date.today() - timedelta(days=10)).isoformat()
    soon = (date.today() + timedelta(days=5)).isoformat()
    pid = client.post("/api/market-events", json={"title": "Old", "category": "macro", "event_date": past}).json()["id"]
    sid = client.post("/api/market-events", json={"title": "Soon", "category": "macro", "event_date": soon}).json()["id"]
    ids = [e["id"] for e in client.get("/api/market-events").json()["events"]]
    assert sid in ids and pid not in ids
    assert pid in [e["id"] for e in client.get("/api/market-events?include_past=true").json()["events"]]
    assert client.delete(f"/api/market-events/{pid}").status_code == 200


def test_sentiment_keywords_match_whole_words():
    from sentiment_analyzer import SentimentAnalyzer
    a = SentimentAnalyzer()
    tickers = {x["ticker"] for x in a._scan_affected_assets("Every event whether macro or prime minister level")}
    assert not tickers & {"TSLA", "ETH-USD", "AAPL", "AMZN"}
    assert "TSLA" in {x["ticker"] for x in a._scan_affected_assets("New EV tax credit announced")}


def test_compare_and_research_snapshot(client):
    c = client.get("/market/compare?tickers=AAPL,SPY&period=1y").json()
    assert c["series"][0]["AAPL"] == 100.0 and set(c["stats"]) == {"AAPL", "SPY"}
    s = client.get("/research/snapshot/AAPL").json()
    assert s["performance"]["beta"] is not None and s["technicals"]["ma200"] is not None
    assert s["analysts"]["targetMean"] == 230.0
    assert client.get("/research/snapshot/bad$$").status_code == 400


def test_risk_free_rate_handles_tenfold_quote(monkeypatch):
    import main
    import market_data as md
    from conftest import fake_history
    md.clear_cache()
    monkeypatch.setattr(md, "history", lambda tk, p="1y", i="1d": fake_history(tk, p) * (10 if tk == "^TNX" else 1))
    assert round(main.risk_free_rate(), 4) == 0.042

import pandas as pd

import market_data as md
from conftest import fake_history


def _real_md():
    """The autouse fixture stubs md.history/md.info; reload for the real ones."""
    import importlib
    real = importlib.reload(md)
    real.clear_cache()
    return real


def test_history_falls_back_when_yfinance_fails(monkeypatch):
    real = _real_md()
    monkeypatch.setattr(real, "_yf_history", lambda *a: (_ for _ in ()).throw(RuntimeError("crumb")))
    monkeypatch.setattr(real, "_chart_history", lambda tk, p, i: fake_history(tk, p))
    df = real.history("AAPL", "1y")
    assert len(df) == 252 and real.LAST_SOURCE["history"] == "yahoo-chart"


def test_history_reaches_stooq_when_yahoo_is_down(monkeypatch):
    real = _real_md()
    monkeypatch.setattr(real, "_yf_history", lambda *a: pd.DataFrame())
    monkeypatch.setattr(real, "_chart_history", lambda *a: pd.DataFrame())
    monkeypatch.setattr(real, "_stooq_history", lambda tk, p, i: fake_history(tk, p))
    assert not real.history("MSFT", "6mo").empty and real.LAST_SOURCE["history"] == "stooq"


def test_info_rebuilds_quote_from_chart(monkeypatch):
    real = _real_md()
    monkeypatch.setattr(real.yf, "Ticker", lambda tk: (_ for _ in ()).throw(RuntimeError("blocked")))
    monkeypatch.setattr(real, "_chart", lambda tk, p, i: {
        "meta": {"regularMarketPrice": 101.0, "shortName": "X"},
        "indicators": {"quote": [{"close": [98.0, 99.0, 100.0, 101.0]}]}})
    i = real.info("XYZ")
    assert i["regularMarketPrice"] == 101.0 and round(i["regularMarketChangePercent"], 3) == 1.0
    assert i["fiftyTwoWeekLow"] == 98.0 and not real.has_fundamentals(i)

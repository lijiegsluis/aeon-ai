import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_TMP = tempfile.mkdtemp(prefix="aeon-analytics-test-")
os.environ["AEON_ANALYTICS_DB_PATH"] = str(Path(_TMP) / "terminal.db")
os.environ["HOME"] = _TMP  # keeps Houston's ~/AeonNimbus paths inside the sandbox
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import market_data as md  # noqa: E402


def fake_history(tk, period="1y", interval="1d"):
    days = {"5d": 5, "6mo": 126, "1y": 252, "2y": 504}.get(period, 252)
    idx = pd.bdate_range(end=pd.Timestamp("2026-09-25"), periods=days, tz="UTC")
    rng = np.random.default_rng(abs(hash(tk)) % 2**32)
    drift = 0.0008 if tk != "SPY" else 0.0004
    close = 100 * np.exp(np.cumsum(drift + 0.012 * rng.standard_normal(days)))
    if tk == "^TNX":
        close = np.full(days, 4.2)
    return pd.DataFrame({"Open": close, "High": close * 1.01, "Low": close * 0.99, "Close": close,
                         "Volume": np.full(days, 1_000_000.0)}, index=idx)


FAKE_INFO = {
    "AAPL": {"currentPrice": 200.0, "shortName": "Apple Inc.", "regularMarketChange": 2.0,
             "regularMarketChangePercent": 1.0, "marketCap": 3e12, "trailingPE": 30.0, "trailingEps": 6.5,
             "bookValue": 4.0, "beta": 1.2, "sharesOutstanding": 15e9, "freeCashflow": 100e9,
             "earningsGrowth": 0.08, "totalDebt": 1e11, "dividendYield": 0.44,
             "trailingAnnualDividendYield": 0.0046, "targetMeanPrice": 230.0, "sector": "Technology"},
    "BURN": {"currentPrice": 10.0, "shortName": "Cash Burner", "sharesOutstanding": 1e8,
             "freeCashflow": -5e8, "beta": 1.5},
    "CHART": {"regularMarketPrice": 50.0, "shortName": "Chart Only", "_source": "yahoo-chart"},
}


@pytest.fixture(autouse=True)
def offline_market(monkeypatch):
    md.clear_cache()
    monkeypatch.setattr(md, "history", fake_history)
    monkeypatch.setattr(md, "info", lambda tk: dict(FAKE_INFO.get(tk, {})))
    monkeypatch.setattr(md, "joint_closes",
                        lambda syms, period="2y": pd.DataFrame({s: fake_history(s, period)["Close"] for s in syms}))
    import main
    monkeypatch.setattr(main, "stooq_quote", lambda t: None)
    yield


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app)  # no `with`: skips the network-seeding startup hook

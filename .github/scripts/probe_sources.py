"""One-off probe of candidate keyless data sources for the alpha engine."""
import json
from datetime import date, timedelta

from curl_cffi import requests as br


def show(label, url, params=None, n=700, headers=None):
    try:
        r = br.get(url, params=params, impersonate="chrome", timeout=20, headers=headers)
        print(f"\n=== {label} HTTP {r.status_code} len={len(r.text)}")
        print(r.text[:n])
        return r
    except Exception as e:
        print(f"\n=== {label} FAILED {type(e).__name__}: {e}")


past = date.today() - timedelta(days=28)
while past.weekday() > 3:
    past -= timedelta(days=1)
fut = date.today() + timedelta(days=21)
while fut.weekday() > 3:
    fut += timedelta(days=1)
show("nasdaq calendar past", "https://api.nasdaq.com/api/calendar/earnings", {"date": past.isoformat()}, 1500)
show("nasdaq calendar future", "https://api.nasdaq.com/api/calendar/earnings", {"date": fut.isoformat()}, 1200)
show("nasdaq surprise AAPL", "https://api.nasdaq.com/api/company/AAPL/earnings-surprise", None, 1500)
show("nasdaq earnings-date AAPL", "https://api.nasdaq.com/api/analyst/AAPL/earnings-date", None, 800)
r = show("cnn graphdata", "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
         None, 300, {"Referer": "https://www.cnn.com/markets/fear-and-greed"})
if r is not None and r.status_code == 200:
    d = r.json()
    print("keys:", list(d))
    h = (d.get("fear_and_greed_historical") or {}).get("data") or []
    print("historical points:", len(h), h[:2], h[-1:] if h else None)
r = show("yahoo chart with earnings events", "https://query2.finance.yahoo.com/v8/finance/chart/AAPL",
         {"range": "2y", "interval": "1d", "events": "earnings,div,split"}, 200)
if r is not None and r.status_code == 200:
    ev = r.json()["chart"]["result"][0].get("events") or {}
    print("event kinds:", list(ev), "earnings:", list((ev.get("earnings") or {}).values())[:3])
show("sec form4 atom 100", "https://www.sec.gov/cgi-bin/browse-edgar",
     {"action": "getcurrent", "type": "4", "company": "", "dateb": "", "owner": "include", "count": "100", "output": "atom"},
     300, {"User-Agent": "AeonIntelligence research contact@aeonnimbus.com"})
show("sec daily form index", f"https://www.sec.gov/Archives/edgar/daily-index/{past.year}/QTR{(past.month-1)//3+1}/",
     None, 400, {"User-Agent": "AeonIntelligence research contact@aeonnimbus.com"})
show("openinsider cluster buys", "http://openinsider.com/latest-cluster-buys", None, 300)

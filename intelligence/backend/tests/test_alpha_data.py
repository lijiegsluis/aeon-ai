import alpha_data


def test_number_parsing():
    assert alpha_data._num("$357,892,653,000") == 357892653000.0
    assert alpha_data._num("($0.04)") == -0.04
    assert alpha_data._num("-16.13") == -16.13
    assert alpha_data._num("N/A") is None and alpha_data._num("") is None and alpha_data._num(None) is None


OI_HTML = """<table class="tinytable"><thead><tr>
<th>X</th><th>Filing&nbsp;Date</th><th>Trade&nbsp;Date</th><th>Ticker</th><th>Company Name</th><th>Industry</th>
<th>Ins</th><th>Trade&nbsp;Type</th><th>Price</th><th>Qty</th><th>Owned</th><th>ΔOwn</th><th>Value</th>
<th>1d</th><th>1w</th><th>1m</th><th>6m</th></tr></thead><tbody>
<tr><td>M</td><td>2026-09-25 17:02:11</td><td>2026-09-23</td><td>ABCD</td><td>Abcd Inc</td><td>Banks</td>
<td>3</td><td>P - Purchase</td><td>$12.40</td><td>+40,000</td><td>1,200,000</td><td>+3%</td><td>+$496,000</td>
<td></td><td></td><td></td><td></td></tr>
<tr><td></td><td>bad</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td>
<td></td><td></td><td></td><td></td></tr>
</tbody></table>"""


def test_openinsider_parse():
    rows = alpha_data._parse_openinsider(OI_HTML)
    assert rows == [{
        "ticker": "ABCD", "company": "Abcd Inc", "industry": "Banks", "filing_date": "2026-09-25",
        "trade_date": "2026-09-23", "insiders": 3, "trade_type": "P - Purchase", "price": 12.4,
        "qty": 40000.0, "owned_change_pct": 3.0, "value": 496000.0,
    }]


def test_calendar_normalisation(monkeypatch):
    class Resp:
        def json(self):
            return {"data": {"rows": [
                {"symbol": "DELL", "name": "Dell", "time": "time-after-hours", "marketCap": "$357,892,653,000",
                 "epsForecast": "$4.72", "eps": "$6.76", "surprise": "43.22", "noOfEsts": "5",
                 "fiscalQuarterEnding": "Jul/2026"},
                {"symbol": "", "name": "blank"},
            ]}}
    monkeypatch.setattr(alpha_data.real_data, "_get", lambda *a, **k: Resp())
    from datetime import date
    rows = alpha_data._fetch_calendar(date(2026, 9, 1))
    assert rows == [{"symbol": "DELL", "name": "Dell", "date": "2026-09-01", "time": "after",
                     "market_cap": 357892653000.0, "eps_forecast": 4.72, "eps_actual": 6.76,
                     "surprise_pct": 43.22, "num_estimates": 5.0, "fiscal_quarter": "Jul/2026"}]

"""Parsers and classifiers in real_data - pure functions, no network."""
from datetime import datetime

import real_data


def _form4(*txns):
    rows = "".join(
        f"""<nonDerivativeTransaction>
              <transactionDate><value>{d}</value></transactionDate>
              <transactionCoding><transactionCode>{code}</transactionCode></transactionCoding>
              <transactionAmounts>
                <transactionShares><value>{shares}</value></transactionShares>
                <transactionPricePerShare><value>{price}</value></transactionPricePerShare>
                <transactionAcquiredDisposedCode><value>{ad}</value></transactionAcquiredDisposedCode>
              </transactionAmounts>
            </nonDerivativeTransaction>"""
        for code, ad, shares, price, d in txns
    )
    return f"""<ownershipDocument>
      <issuer><issuerCik>0000320193</issuerCik><issuerName>Apple Inc.</issuerName><issuerTradingSymbol>AAPL</issuerTradingSymbol></issuer>
      <reportingOwner><reportingOwnerId><rptOwnerName>Doe Jane</rptOwnerName></reportingOwnerId>
        <reportingOwnerRelationship><isOfficer>true</isOfficer><officerTitle>CFO</officerTitle></reportingOwnerRelationship></reportingOwner>
      <nonDerivativeTable>{rows}</nonDerivativeTable></ownershipDocument>"""


def test_form4_counts_open_market_purchase_as_buy():
    t = real_data._parse_form4_xml(_form4(("P", "A", 1000, 150.0, "2026-09-01")))
    assert t["is_buy"] and t["shares"] == 1000 and t["total_value"] == 150_000


def test_form4_ignores_option_exercise_grant_and_tax_withholding():
    # An option exercise (M), a grant (A) and tax withholding (F) are not conviction trades.
    xml = _form4(("M", "A", 5000, 20.0, "2026-09-01"), ("A", "A", 800, 0, "2026-09-01"),
                 ("F", "D", 300, 150.0, "2026-09-01"))
    assert real_data._parse_form4_xml(xml) is None


def test_form4_sale_after_exercise_is_a_sale_only():
    xml = _form4(("M", "A", 5000, 20.0, "2026-09-02"), ("S", "D", 5000, 190.0, "2026-09-02"))
    t = real_data._parse_form4_xml(xml)
    assert t["is_buy"] is False and t["total_value"] == 950_000


def test_untagged_headline_is_not_pinned_on_spy():
    assert real_data._extract_tickers("Oil prices climb as supply tightens", real_data.WATCHLIST) == ""
    assert real_data._extract_tickers("NVDA and AMD rally", real_data.WATCHLIST) == "NVDA,AMD"


def test_fomc_parser_handles_cross_month_and_sep_asterisks():
    html = ("<h4>2027 FOMC Meetings</h4><strong>January</strong> 26-27 <p>Notation vote January 26</p> "
            "<strong>March</strong> 16-17* "
            "<strong>April/May</strong> 27-28 <strong>June</strong> 15-16* <strong>July</strong> 27-28 "
            "<strong>October/November</strong> 31-1 <strong>December</strong> 7-8*")
    dates = real_data.parse_fomc_calendar(html)[2027]
    assert [d.strftime("%m-%d") for d in dates] == ["01-27", "03-17", "04-28", "06-16", "07-28", "11-01", "12-08"]
    assert all(d.hour == 14 for d in dates)


def test_fomc_parser_rejects_garbage():
    assert real_data.parse_fomc_calendar("2027 FOMC Meetings nothing here") == {}


def test_bls_ics_parser_unfolds_lines_and_reads_times():
    ics = ("BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nDTSTART;TZID=US-Eastern:20261106T083000\r\n"
           "SUMMARY:Employment Situation for Octo\r\n ber 2026\r\nEND:VEVENT\r\n"
           "BEGIN:VEVENT\r\nDTSTART;TZID=US-Eastern:20261110T083000\r\nSUMMARY:Consumer Price Index for October 2026\r\nEND:VEVENT\r\n"
           "BEGIN:VEVENT\r\nDTSTART;TZID=US-Eastern:20261112T100000\r\nSUMMARY:Job Openings and Labor Turnover Survey\r\nEND:VEVENT\r\nEND:VCALENDAR")
    out = real_data.parse_bls_ics(ics)
    assert out["nfp"] == [datetime(2026, 11, 6, 8, 30)]
    assert out["cpi"] == [datetime(2026, 11, 10, 8, 30)]
    assert "ppi" not in out


def test_kraken_fallback_parses_legacy_pair_names(monkeypatch):
    class Resp:
        def json(self):
            return {"error": [], "result": {
                "XXBTZUSD": {"c": ["65000.0", "0.1"], "o": "64000.0", "v": ["10", "100"]},
                "XETHZUSD": {"c": ["3000.0", "1"], "o": "3100.0", "v": ["50", "500"]},
            }}
    monkeypatch.setattr(real_data, "_get", lambda *a, **k: Resp())
    out = {c["symbol"]: c for c in real_data._kraken_prices()}
    assert out["BTC"]["price"] == 65000.0 and out["BTC"]["change_24h"] == 1.56
    assert out["ETH"]["change_24h"] == -3.23 and out["BTC"]["source"] == "Kraken" and "SOL" not in out

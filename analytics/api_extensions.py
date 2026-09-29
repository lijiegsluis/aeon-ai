"""
API endpoints for persistence, collaboration, and advanced features
"""
import math
import re
from typing import List, Optional
from pydantic import BaseModel, field_validator
from datetime import datetime, timedelta
import secrets
import json
from fastapi import HTTPException, FastAPI
import requests as http
from database import save_analysis, get_analysis_history, save_watchlist, get_watchlists, create_alert, get_active_alerts


_TICKER = re.compile(r"^[A-Z0-9.\-^]{1,10}$")
CONDITIONS = {"price_above", "price_below", "pe_above", "pe_below"}


def _clean_ticker(t: str) -> str:
    t = (t or "").strip().upper()
    if not _TICKER.match(t):
        raise ValueError(f"invalid ticker: {t!r}")
    return t


def register_api_extensions(app: FastAPI, quote_func):
    """Register all API extension endpoints to the FastAPI app"""

    # ─── Request/Response Models ─────────────────────────────────────────

    class SaveAnalysisRequest(BaseModel):
        ticker: str
        result: dict
        user_id: Optional[int] = None


    class WatchlistRequest(BaseModel):
        name: str
        tickers: List[str]
        user_id: int

        @field_validator("tickers")
        @classmethod
        def _tickers(cls, v):
            out = list(dict.fromkeys(_clean_ticker(t) for t in v if t and t.strip()))
            if not out:
                raise ValueError("at least one ticker is required")
            return out[:50]

        @field_validator("name")
        @classmethod
        def _name(cls, v):
            if not v.strip():
                raise ValueError("name is required")
            return v.strip()[:80]


    class AlertRequest(BaseModel):
        ticker: str
        condition_type: str  # "price_above", "price_below", "pe_above", "pe_below"
        threshold: float
        user_id: int

        @field_validator("ticker")
        @classmethod
        def _ticker(cls, v):
            return _clean_ticker(v)

        @field_validator("condition_type")
        @classmethod
        def _cond(cls, v):
            if v not in CONDITIONS:
                raise ValueError(f"condition_type must be one of {sorted(CONDITIONS)}")
            return v

        @field_validator("threshold")
        @classmethod
        def _threshold(cls, v):
            if not math.isfinite(v) or v <= 0:
                raise ValueError("threshold must be a positive number")
            return v


    class ComparisonRequest(BaseModel):
        tickers: List[str]  # Up to 5 tickers

        @field_validator("tickers")
        @classmethod
        def _tickers(cls, v):
            return list(dict.fromkeys(_clean_ticker(t) for t in v if t and t.strip()))


    class ShareAnalysisRequest(BaseModel):
        analysis_id: int
        expires_in_days: Optional[int] = 7

    # ─── Persistence Endpoints ───────────────────────────────────────────

    @app.post("/api/analyses/save")
    def api_save_analysis(req: SaveAnalysisRequest):
        """Save analysis to database for history/replay"""
        analysis_id = save_analysis(req.user_id, req.ticker, req.result)
        return {"id": analysis_id, "saved_at": datetime.utcnow().isoformat()}


    @app.get("/api/analyses/history")
    def api_get_history(user_id: Optional[int] = None, ticker: Optional[str] = None, limit: int = 50):
        """Get analysis history for user/ticker"""
        history = get_analysis_history(user_id, ticker, limit)
        return {"history": history, "count": len(history)}


    @app.get("/api/analyses/{analysis_id}")
    def api_get_analysis(analysis_id: int):
        """Retrieve specific analysis by ID for replay"""
        from database import get_db
        with get_db() as conn:
            row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
            if not row:
                raise HTTPException(404, "Analysis not found")
            return {**dict(row), "result": json.loads(row["result_json"])}


    @app.delete("/api/analyses/{analysis_id}")
    def api_delete_analysis(analysis_id: int):
        from database import get_db
        with get_db() as conn:
            conn.execute("DELETE FROM shared_analyses WHERE analysis_id = ?", (analysis_id,))
            cur = conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
        if not cur.rowcount:
            raise HTTPException(404, "Analysis not found")
        return {"status": "deleted"}


    # ─── Watchlist Endpoints ─────────────────────────────────────────────

    @app.post("/api/watchlists")
    def api_create_watchlist(req: WatchlistRequest):
        """Create watchlist"""
        watchlist_id = save_watchlist(req.user_id, req.name, req.tickers)
        return {"id": watchlist_id}


    @app.get("/api/watchlists")
    def api_get_watchlists(user_id: int):
        """Get all watchlists for user"""
        watchlists = get_watchlists(user_id)
        return {"watchlists": watchlists}


    @app.delete("/api/watchlists/{watchlist_id}")
    def api_delete_watchlist(watchlist_id: int):
        from database import get_db
        with get_db() as conn:
            cur = conn.execute("DELETE FROM watchlists WHERE id = ?", (watchlist_id,))
        if not cur.rowcount:
            raise HTTPException(404, "Watchlist not found")
        return {"status": "deleted"}


    # Plain `def` so FastAPI runs it in a worker thread — the per-ticker quotes are
    # blocking network calls that would otherwise stall every other request.
    @app.post("/api/watchlists/{watchlist_id}/analyze")
    def api_analyze_watchlist(watchlist_id: int):
        """Bulk analyze all tickers in watchlist"""
        from database import get_db
        with get_db() as conn:
            row = conn.execute("SELECT tickers_json FROM watchlists WHERE id = ?", (watchlist_id,)).fetchone()
            if not row:
                raise HTTPException(404, "Watchlist not found")
            tickers = json.loads(row["tickers_json"])

        results = []
        for ticker in tickers:
            try:
                # Run quick quote + basic metrics
                quote_data = quote_func(ticker)
                results.append({"ticker": ticker, "status": "success", "data": quote_data})
            except Exception as e:
                detail = getattr(e, "detail", None) or str(e) or type(e).__name__
                results.append({"ticker": ticker, "status": "error", "error": detail})

        return {"watchlist_id": watchlist_id, "results": results, "total": len(tickers)}


    # ─── Alert Endpoints ─────────────────────────────────────────────────

    @app.post("/api/alerts")
    def api_create_alert(req: AlertRequest):
        """Create price/metric alert"""
        alert_id = create_alert(req.user_id, req.ticker, req.condition_type, req.threshold)
        return {"id": alert_id}


    @app.get("/api/alerts")
    def api_get_alerts(ticker: Optional[str] = None):
        """Get active alerts"""
        alerts = get_active_alerts(ticker)
        return {"alerts": alerts}


    @app.post("/api/alerts/{alert_id}/deactivate")
    def api_deactivate_alert(alert_id: int):
        """Deactivate alert"""
        from database import get_db
        with get_db() as conn:
            conn.execute("UPDATE alerts SET is_active = 0 WHERE id = ?", (alert_id,))
        return {"status": "deactivated"}


    @app.get("/api/alerts/triggered")
    def api_triggered_alerts(limit: int = 20):
        """Recently fired alerts (each alert fires once, then switches off)."""
        from database import get_db
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM alerts WHERE triggered_at IS NOT NULL ORDER BY triggered_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return {"alerts": [dict(r) for r in rows]}


    @app.post("/api/alerts/check")
    def api_check_alerts():
        """Check all active alerts; each one that fires is returned once and then
        switched off, so a price sitting past its threshold doesn't re-notify
        every minute."""
        from database import get_db
        alerts = get_active_alerts()
        triggered = []

        for alert in alerts:
            try:
                quote_data = quote_func(alert["ticker"])
                current_price = quote_data.get("price")

                if not current_price:
                    continue

                condition = alert["condition_type"]
                threshold = alert["threshold"]

                if condition == "price_above" and current_price > threshold:
                    triggered.append({**alert, "current_value": current_price})
                elif condition == "price_below" and current_price < threshold:
                    triggered.append({**alert, "current_value": current_price})
                elif condition == "pe_above" and quote_data.get("pe") and quote_data["pe"] > threshold:
                    triggered.append({**alert, "current_value": quote_data["pe"]})
                elif condition == "pe_below" and quote_data.get("pe") and quote_data["pe"] < threshold:
                    triggered.append({**alert, "current_value": quote_data["pe"]})
            except Exception:
                continue

        if triggered:
            now = datetime.utcnow().isoformat(timespec="seconds")
            with get_db() as conn:
                for t in triggered:
                    conn.execute("UPDATE alerts SET is_active = 0, triggered_at = ?, triggered_value = ? WHERE id = ?",
                                 (now, t["current_value"], t["id"]))
        return {"triggered": triggered, "count": len(triggered)}


    # ─── Comparison Endpoints ────────────────────────────────────────────

    @app.post("/api/compare")
    def api_compare_tickers(req: ComparisonRequest):
        """Side-by-side comparison of up to 5 tickers"""
        if len(req.tickers) > 5:
            raise HTTPException(400, "Maximum 5 tickers allowed")

        results = {}
        for ticker in req.tickers:
            try:
                results[ticker] = quote_func(ticker)
            except Exception as e:
                results[ticker] = {"error": getattr(e, "detail", None) or str(e) or type(e).__name__}

        return {"comparison": results, "tickers": req.tickers}


    # ─── Sharing/Collaboration ───────────────────────────────────────────

    @app.post("/api/analyses/{analysis_id}/share")
    def api_share_analysis(analysis_id: int, req: ShareAnalysisRequest):
        """Generate shareable link for analysis"""
        from database import get_db

        share_token = secrets.token_urlsafe(32)
        expires_at = (datetime.utcnow() + timedelta(days=req.expires_in_days)).isoformat()

        with get_db() as conn:
            # Verify analysis exists
            row = conn.execute("SELECT id FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
            if not row:
                raise HTTPException(404, "Analysis not found")

            conn.execute(
                "INSERT INTO shared_analyses (analysis_id, share_token, expires_at) VALUES (?, ?, ?)",
                (analysis_id, share_token, expires_at)
            )

        return {
            "share_token": share_token,
            "share_url": f"http://localhost:5173/shared/{share_token}",
            "expires_at": expires_at
        }


    @app.get("/api/shared/{share_token}")
    def api_get_shared_analysis(share_token: str):
        """Retrieve shared analysis by token"""
        from database import get_db

        with get_db() as conn:
            row = conn.execute("""
                SELECT a.*, sa.expires_at
                FROM shared_analyses sa
                JOIN analyses a ON sa.analysis_id = a.id
                WHERE sa.share_token = ?
            """, (share_token,)).fetchone()

            if not row:
                raise HTTPException(404, "Shared analysis not found")

            if row["expires_at"] and datetime.fromisoformat(row["expires_at"]) < datetime.utcnow():
                raise HTTPException(410, "Share link expired")

            return {**dict(row), "result": json.loads(row["result_json"])}


    # ─── Export Endpoints ────────────────────────────────────────────────

    @app.get("/api/export/analysis/{analysis_id}")
    def api_export_analysis(analysis_id: int, format: str = "json"):
        """Export analysis in various formats"""
        from database import get_db

        with get_db() as conn:
            row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
            if not row:
                raise HTTPException(404, "Analysis not found")

        result = json.loads(row["result_json"])

        if format == "json":
            return result
        elif format == "csv":
            # Convert to CSV (simplified)
            import io
            import csv
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Metric", "Value"])
            # Flatten result dict
            for key, value in result.items():
                if isinstance(value, (str, int, float)):
                    writer.writerow([key, value])
            return {"csv": output.getvalue()}
        else:
            raise HTTPException(400, "Unsupported format")


    # ─── Platform Integration ────────────────────────────────────────────

    @app.post("/api/integration/export-to-platform")
    def api_export_to_platform(analysis_id: int, platform_url: str = "http://localhost:5174"):
        """Export Terminal analysis to Research Platform"""
        from database import get_db

        with get_db() as conn:
            row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
            if not row:
                raise HTTPException(404, "Analysis not found")

        result = json.loads(row["result_json"])

        # Send to Platform API
        try:
            response = http.post(
                f"{platform_url}/api/import-from-terminal",
                json={"ticker": row["ticker"], "data": result},
                timeout=10
            )
            response.raise_for_status()
            return {"status": "exported", "platform_project_id": response.json().get("project_id")}
        except Exception as e:
            raise HTTPException(500, f"Export failed: {str(e)}")

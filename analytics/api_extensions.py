"""
API endpoints for persistence, collaboration, and advanced features
"""
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import secrets
import json
from fastapi import HTTPException, FastAPI
import requests as http
from database import save_analysis, get_analysis_history, save_watchlist, get_watchlists, create_alert, get_active_alerts


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


    class AlertRequest(BaseModel):
        ticker: str
        condition_type: str  # "price_above", "price_below", "pe_above", "pe_below"
        threshold: float
        user_id: int


    class ComparisonRequest(BaseModel):
        tickers: List[str]  # Up to 5 tickers


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


    @app.post("/api/watchlists/{watchlist_id}/analyze")
    async def api_analyze_watchlist(watchlist_id: int):
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
                results.append({"ticker": ticker, "status": "error", "error": str(e)})

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


    @app.post("/api/alerts/check")
    def api_check_alerts():
        """Check all active alerts and return triggered ones"""
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
                results[ticker] = {"error": str(e)}

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

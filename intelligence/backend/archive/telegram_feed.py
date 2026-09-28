"""
Aeon Intelligence - Real Telegram Breaking News Feed

Connects (read-only listener, never sends messages) to the user's real
@Tradeul_Breaking_News Telegram channel using their existing, already-
authorized Telethon session (copied from the Aeon Nimbus Terminal analytics
project so the two apps don't fight over the same session file). Messages
are turned into news-item-shaped dicts so they flow into the same NEWS list,
/api/news endpoints, AI grounding context, and history_db persistence that
real RSS news already uses - just with a "Telegram:" source label so they
stay distinguishable in the UI.

Fails soft everywhere: if credentials are missing, the session has expired,
or Telethon/network errors occur, this module logs and simply contributes no
messages - it must never crash the API.
"""

import configparser
import re
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from real_data import WATCHLIST, _classify_sentiment, _extract_tickers

_CONFIG_PATH = Path("/Users/lijie/aeon-ai/analytics/telegram_config.ini")
_SESSION_PATH = Path(__file__).parent / "aeon_intelligence_telegram"

SOURCE_LABEL = "Telegram: Tradeul_Breaking_News"

TELEGRAM_MESSAGES: List[Dict[str, Any]] = []
# This channel posts ~100-150x/day, so a real 30-day window needs a few
# thousand slots, not a few hundred - a low cap here silently truncates the
# "past month" window to just the last few days no matter what _HISTORY_DAYS says.
_MAX_MESSAGES = 8000
_HISTORY_DAYS = 30
_lock = threading.Lock()
_status = {
    "connected": False,
    "authorized": None,
    "last_error": None,
    "started_at": None,
    "history_window_days": _HISTORY_DAYS,
    "backfilled_count": None,
    "message_count": 0,
}


def _prune_locked():
    """Keep only the last _HISTORY_DAYS worth of messages (and cap the count as a safety net)."""
    from datetime import timezone
    cutoff = datetime.now(timezone.utc).timestamp() - _HISTORY_DAYS * 86400
    kept = []
    for item in TELEGRAM_MESSAGES:
        try:
            ts = datetime.fromisoformat(item["published_at"]).timestamp()
        except Exception:
            ts = datetime.now(timezone.utc).timestamp()
        if ts >= cutoff:
            kept.append(item)
    TELEGRAM_MESSAGES[:] = kept[:_MAX_MESSAGES]
    _status["message_count"] = len(TELEGRAM_MESSAGES)


def _load_config() -> Optional[Dict[str, str]]:
    try:
        if not _CONFIG_PATH.exists() or not _SESSION_PATH.with_suffix(".session").exists():
            return None
        cfg = configparser.ConfigParser()
        cfg.read(_CONFIG_PATH)
        section = cfg["telegram"]
        return {
            "api_id": int(section["api_id"]),
            "api_hash": section["api_hash"],
            "channel_username": section["channel_username"],
        }
    except Exception as e:
        print(f"[telegram_feed] config load failed: {e}")
        return None


def _to_news_item(text: str, when: datetime) -> Dict[str, Any]:
    clean = re.sub(r"\s+", " ", text).strip()
    title = clean[:140] if clean else "(empty Telegram message)"
    return {
        "title": title,
        "published_at": when.isoformat(),
        "source": SOURCE_LABEL,
        "sentiment": _classify_sentiment(clean),
        "summary": clean[:280] or title,
        "tickers": _extract_tickers(clean, WATCHLIST),
        "url": "",
        "urgency": "breaking",
    }


def get_recent(limit: int = 20) -> List[Dict[str, Any]]:
    with _lock:
        return list(TELEGRAM_MESSAGES[:limit])


def get_status() -> Dict[str, Any]:
    with _lock:
        return dict(_status)


def _run_client_forever(on_new_message: Optional[Callable[[Dict[str, Any]], None]]):
    import asyncio
    from telethon import TelegramClient, events

    async def _backfill_history(client, channel_username: str):
        """One-time-per-connect real history fetch: pull up to _HISTORY_DAYS of past real
        channel messages so the UI shows an actual month of history, not just what arrives
        after this process happened to start listening."""
        from datetime import timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=_HISTORY_DAYS)
        backfilled: List[Dict[str, Any]] = []
        async for msg in client.iter_messages(channel_username, limit=_MAX_MESSAGES):
            if msg.date < cutoff:
                break
            if not (msg.message or "").strip():
                continue
            backfilled.append(_to_news_item(msg.message, msg.date))
        with _lock:
            TELEGRAM_MESSAGES[:] = backfilled
            _prune_locked()
            _status["backfilled_count"] = len(backfilled)
        print(f"[telegram_feed] backfilled {len(backfilled)} real messages from the last {_HISTORY_DAYS} days")

    cfg = _load_config()
    if cfg is None:
        print("[telegram_feed] no config/session found - skipping live Telegram feed")
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = TelegramClient(str(_SESSION_PATH), cfg["api_id"], cfg["api_hash"])

    async def _main():
        await client.connect()
        authorized = await client.is_user_authorized()
        with _lock:
            _status["authorized"] = authorized
        if not authorized:
            print("[telegram_feed] session is not authorized (expired?) - skipping live feed")
            return

        @client.on(events.NewMessage(chats=cfg["channel_username"]))
        async def handler(event):
            try:
                item = _to_news_item(event.message.message or "", event.date)
                with _lock:
                    TELEGRAM_MESSAGES.insert(0, item)
                    _prune_locked()
                if on_new_message:
                    on_new_message(item)
            except Exception as e:
                print(f"[telegram_feed] failed to process message: {e}")

        try:
            await _backfill_history(client, cfg["channel_username"])
        except Exception as e:
            print(f"[telegram_feed] history backfill failed (continuing live-only): {e}")

        with _lock:
            _status["connected"] = True
            _status["started_at"] = datetime.now().isoformat()
        print(f"[telegram_feed] connected - listening to {cfg['channel_username']}")
        await client.run_until_disconnected()

    try:
        loop.run_until_complete(_main())
    except Exception as e:
        with _lock:
            _status["last_error"] = str(e)
        print(f"[telegram_feed] client error: {e}")
    finally:
        with _lock:
            _status["connected"] = False
        try:
            loop.run_until_complete(client.disconnect())
        except Exception:
            pass


def start_background(on_new_message: Optional[Callable[[Dict[str, Any]], None]] = None):
    """Fire-and-forget background thread. Auto-retries with backoff on disconnect."""

    def _loop_with_retry():
        backoff = 30
        while True:
            try:
                _run_client_forever(on_new_message)
            except Exception as e:
                print(f"[telegram_feed] unexpected error, retrying in {backoff}s: {e}")
            time.sleep(backoff)
            backoff = min(backoff * 2, 600)

    threading.Thread(target=_loop_with_retry, daemon=True).start()

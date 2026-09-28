"""
Aeon Intelligence - AI Engine

Free-tier multi-provider LLM client, ported from the fallback-chain pattern
used in Aeon Nimbus Platform's ai_research.py. Tries Groq first (generous
free RPM), then Gemini, then OpenAI/Anthropic only if the user has set those
keys. Never raises - callers get None on total failure and fall back to
static/demo content.
"""

import json
import os
import re
import time
from typing import Any, Dict, Optional

import requests

# provider -> (env var holding the key, OpenAI-compatible base url, default model)
_OPENAI_COMPATIBLE = {
    "groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1", "openai/gpt-oss-120b"),
    "gemini": ("GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai", "gemini-3.8-flash"),
    "openai": ("OPENAI_API_KEY", "https://api.openai.com/v1", "gpt-4o-mini"),
}

_PROVIDER_ORDER = ["groq", "gemini", "openai"]


def available() -> bool:
    return any(os.environ.get(env_var) for env_var, _, _ in _OPENAI_COMPATIBLE.values())


def _configured_providers():
    for name in _PROVIDER_ORDER:
        env_var, base_url, model = _OPENAI_COMPATIBLE[name]
        key = os.environ.get(env_var)
        if key:
            yield name, key, base_url, os.environ.get(f"AI_MODEL_{name.upper()}", model)


def _loads(raw: str) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    return None


def _call_provider(base_url: str, model: str, key: str, system: str, user: str,
                    max_retries: int = 2) -> Optional[str]:
    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
    }

    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
        except Exception as e:
            print(f"[ai_engine] request to {url} failed: {e}")
            return None

        if resp.status_code == 200:
            try:
                return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"[ai_engine] unexpected response shape from {url}: {e}")
                return None

        if resp.status_code in (429, 503) and attempt < max_retries:
            time.sleep(1.5 * (attempt + 1))
            continue

        print(f"[ai_engine] {url} -> HTTP {resp.status_code}: {resp.text[:200]}")
        return None

    return None


def generate_json(system_prompt: str, user_prompt: str) -> Optional[Dict[str, Any]]:
    """Try each configured free-tier provider in order. Returns parsed JSON dict or None."""
    for name, key, base_url, model in _configured_providers():
        raw = _call_provider(base_url, model, key, system_prompt, user_prompt)
        if raw is None:
            continue
        parsed = _loads(raw)
        if parsed is not None:
            return parsed
        print(f"[ai_engine] {name} returned unparseable JSON, trying next provider")
    return None

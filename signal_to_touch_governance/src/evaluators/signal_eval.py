import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from src.config import DATA_DIR, DIST_DIR, get_setting


SEARCH_TERMS = [
    "ERP migration",
    "SAP S/4HANA migration",
    "supplier portal update",
    "supplier guidelines",
    "routing guide",
    "invoice reconciliation",
    "store operations hiring",
    "logistics delays",
    "workforce planning",
    "retail operations transformation",
    "supply chain transformation",
]


def find_signal(account: dict[str, Any]) -> dict[str, Any]:
    live_signal = _search_exa(account)
    if live_signal:
        _write_cache(account["account_name"], live_signal)
        return live_signal
    return _fallback_signal(account["account_name"])


def _search_exa(account: dict[str, Any]) -> dict[str, Any] | None:
    api_key = get_setting("EXA_API_KEY")
    if not api_key:
        return None

    company = account["public_search_company"]
    query = f"{company} ({' OR '.join(SEARCH_TERMS)})"
    payload = {
        "query": query,
        "numResults": 5,
        "type": "neural",
        "contents": {"text": True, "summary": True},
    }

    request = urllib.request.Request(
        "https://api.exa.ai/search",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None

    results = body.get("results") or []
    if not results:
        return None

    evaluated = [_score_exa_result(result) for result in results]
    evaluated.sort(key=lambda item: item["score"], reverse=True)
    return evaluated[0]


def _score_exa_result(result: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(
        str(result.get(field, ""))
        for field in ("title", "summary", "text", "url")
    ).lower()

    keyword_weights = {
        "sap": 2,
        "s/4hana": 3,
        "erp": 3,
        "supplier": 2,
        "portal": 2,
        "invoice": 2,
        "reconciliation": 2,
        "store operations": 3,
        "logistics": 2,
        "supply chain": 3,
        "transformation": 2,
        "migration": 2,
    }
    raw_score = 2 + sum(weight for keyword, weight in keyword_weights.items() if keyword in text)
    score = max(0, min(10, raw_score))

    return {
        "signal_title": result.get("title") or "External operations signal",
        "signal_url": result.get("url") or "",
        "signal_summary": result.get("summary") or _summarize_text(result.get("text", "")),
        "signal_type": _classify_signal(text),
        "score": score,
        "relevance_reason": "The result references operational change that may map to Duvo's retail and supply chain ICP.",
        "risk_of_noise": "Live search results need CRM and conversation checks before any outbound action.",
        "source": "exa_live",
    }


def _classify_signal(text: str) -> str:
    if "sap" in text or "erp" in text or "migration" in text:
        return "erp_migration"
    if "supplier" in text and "portal" in text:
        return "supplier_portal"
    if "store operations" in text or "hiring" in text:
        return "store_ops_hiring"
    if "logistics" in text or "delay" in text:
        return "logistics_friction"
    if "ai" in text:
        return "generic_ai"
    return "other"


def _summarize_text(text: str) -> str:
    compact = " ".join(str(text).split())
    if len(compact) <= 260:
        return compact
    return compact[:257] + "..."


def _fallback_signal(account_name: str) -> dict[str, Any]:
    fallback_path = DATA_DIR / "exa_fallback_signals.json"
    payload = json.loads(fallback_path.read_text(encoding="utf-8"))
    for signal in payload["signals"]:
        if signal["account_name"] == account_name:
            return signal
    raise ValueError(f"No fallback signal found for {account_name}")


def _write_cache(account_name: str, signal: dict[str, Any]) -> None:
    DIST_DIR.mkdir(exist_ok=True)
    cache_path = DIST_DIR / "exa_cache.json"
    cache: dict[str, Any] = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache = {}
    cache[account_name] = signal
    cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")

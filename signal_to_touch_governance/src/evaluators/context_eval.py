import json
from typing import Any

from src.config import get_setting


def evaluate_context(
    hubspot_account: dict[str, Any],
    gong_context: dict[str, Any],
    signal: dict[str, Any],
) -> dict[str, Any]:
    llm_result = _evaluate_with_openai(hubspot_account, gong_context, signal)
    if llm_result:
        return llm_result
    return _deterministic_context_eval(hubspot_account, gong_context, signal)


def _evaluate_with_openai(
    hubspot_account: dict[str, Any],
    gong_context: dict[str, Any],
    signal: dict[str, Any],
) -> dict[str, Any] | None:
    api_key = get_setting("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    model = get_setting("OPENAI_MODEL", "gpt-4.1-mini")
    client = OpenAI(api_key=api_key)
    prompt = {
        "hubspot_account": hubspot_account,
        "gong_context": gong_context,
        "signal": signal,
        "instructions": "Return strict JSON only. Detect active deal conflict, vendor freeze, open objection, support for outreach, owner handling, key evidence, context summary, and risk level.",
    }

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a GTM governance evaluator. Return only valid JSON with keys: "
                        "has_active_deal_conflict, has_vendor_freeze, has_open_objection, "
                        "supports_outreach, owner_should_handle, key_evidence, context_summary, risk_level."
                    ),
                },
                {"role": "user", "content": json.dumps(prompt)},
            ],
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        return _normalize_context(parsed)
    except Exception:
        return None


def _deterministic_context_eval(
    hubspot_account: dict[str, Any],
    gong_context: dict[str, Any],
    signal: dict[str, Any],
) -> dict[str, Any]:
    recent_call = gong_context.get("recent_call", {})
    combined_text = " ".join(
        str(value)
        for value in [
            recent_call.get("structured_summary", ""),
            recent_call.get("transcript_excerpt", ""),
            recent_call.get("objection_type", ""),
            recent_call.get("sentiment", ""),
            recent_call.get("next_step", ""),
        ]
    ).lower()

    has_vendor_freeze = "vendor_freeze" in combined_text or "vendor conversations are frozen" in combined_text
    has_pause = "pause" in combined_text or "do not outbound" in combined_text or "do not have anyone else reach out" in combined_text
    active_deal = bool(hubspot_account.get("active_deal"))
    owner_should_handle = active_deal or has_vendor_freeze or has_pause
    has_open_objection = has_pause or recent_call.get("objection_type") not in (None, "", "none")
    supports_outreach = not (has_vendor_freeze or has_pause or active_deal or has_open_objection)

    evidence = []
    if active_deal:
        evidence.append(
            f"HubSpot shows active deal in {hubspot_account.get('deal_stage')} owned by {hubspot_account.get('owner')}."
        )
    if recent_call.get("transcript_excerpt"):
        evidence.append(recent_call["transcript_excerpt"])
    if signal.get("score", 0) >= 6:
        evidence.append(f"External signal is strong with score {signal['score']}/10.")

    if supports_outreach:
        context_summary = (
            "The account has a strong external operations signal, no active HubSpot deal conflict, "
            "and supportive Gong context for a concise, relevant follow-up. Prepare a dry-run draft "
            "for human review."
        )
        risk_level = "low"
    else:
        context_summary = (
            "The account has a strong external operations signal, but Gong or HubSpot context contains "
            "a vendor freeze, open objection, explicit pause, or owner conflict. The owner should handle "
            "follow-up timing."
        )
        risk_level = "high" if has_vendor_freeze or has_pause else "medium"

    return {
        "has_active_deal_conflict": active_deal,
        "has_vendor_freeze": has_vendor_freeze,
        "has_open_objection": has_open_objection,
        "supports_outreach": supports_outreach,
        "owner_should_handle": owner_should_handle,
        "key_evidence": evidence,
        "context_summary": context_summary,
        "risk_level": risk_level,
        "evaluation_source": "deterministic_fallback",
    }


def _normalize_context(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "has_active_deal_conflict": bool(payload.get("has_active_deal_conflict")),
        "has_vendor_freeze": bool(payload.get("has_vendor_freeze")),
        "has_open_objection": bool(payload.get("has_open_objection")),
        "supports_outreach": bool(payload.get("supports_outreach")),
        "owner_should_handle": bool(payload.get("owner_should_handle")),
        "key_evidence": _as_text_list(payload.get("key_evidence")),
        "context_summary": str(payload.get("context_summary") or ""),
        "risk_level": str(payload.get("risk_level") or "medium"),
        "evaluation_source": "openai_live",
    }


def _as_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if item not in (None, "")]
    return [str(value)]

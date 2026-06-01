from typing import Any


def plan_action(
    hubspot_account: dict[str, Any],
    gong_context: dict[str, Any],
    signal: dict[str, Any],
    context: dict[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    conflict = any(
        [
            context["has_vendor_freeze"],
            context["has_open_objection"],
            context["has_active_deal_conflict"],
            context["owner_should_handle"],
        ]
    )

    if conflict:
        return {
            "decision": "BLOCK_OUTBOUND",
            "reasoning": (
                "Strong external signal, but Gong and HubSpot context indicate an active vendor freeze, "
                "open objection, or owner-led deal motion. Do not enroll this account in lemlist."
            ),
            "blocked_actions": ["lemlist_enrollment", "auto_send", "linkedin_message", "call_task"],
            "human_approval_required": True,
            "dry_run": dry_run,
            "hubspot_task_payload": _hubspot_task(hubspot_account, gong_context, signal),
            "lemlist_payload": None,
        }

    if signal.get("score", 0) < 6:
        return {
            "decision": "MONITOR_ONLY",
            "reasoning": "Signal score is below the outbound threshold. Keep monitoring and avoid enrichment spend.",
            "blocked_actions": ["lemlist_enrollment", "auto_send"],
            "human_approval_required": True,
            "dry_run": dry_run,
            "hubspot_task_payload": None,
            "lemlist_payload": None,
        }

    return {
        "decision": "PREPARE_LEMLIST_DRAFT",
        "reasoning": "Strong signal and no detected account or conversation conflict.",
        "blocked_actions": ["auto_send"],
        "human_approval_required": True,
        "dry_run": dry_run,
        "hubspot_task_payload": None,
        "lemlist_payload": None,
    }


def _hubspot_task(
    hubspot_account: dict[str, Any],
    gong_context: dict[str, Any],
    signal: dict[str, Any],
) -> dict[str, Any]:
    recent_call = gong_context.get("recent_call", {})
    return {
        "object_type": "task",
        "account_name": hubspot_account["account_name"],
        "owner": hubspot_account.get("owner"),
        "priority": "high",
        "subject": "Review blocked outbound signal before any follow-up",
        "body": (
            f"External signal found: {signal.get('signal_title')}. "
            f"Outbound blocked because Gong context says: {recent_call.get('next_step')}"
        ),
        "due_date": "2026-10-15",
        "metadata": {
            "decision": "BLOCK_OUTBOUND",
            "signal_url": signal.get("signal_url"),
            "gong_call_date": recent_call.get("date"),
            "objection_type": recent_call.get("objection_type"),
        },
    }

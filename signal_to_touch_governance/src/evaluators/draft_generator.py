from typing import Any


def generate_draft_payload(
    hubspot_account: dict[str, Any],
    signal: dict[str, Any],
    action: dict[str, Any],
) -> dict[str, Any] | None:
    if action["decision"] != "PREPARE_LEMLIST_DRAFT":
        return None

    contact = (hubspot_account.get("contacts") or [{}])[0]
    first_name = contact.get("first_name", "Alex")
    last_name = contact.get("last_name", "Morgan")

    return {
        "campaign_id": "mock_campaign_duvo_ops",
        "lead": {
            "email": contact.get("email", "mock@example.com"),
            "firstName": first_name,
            "lastName": last_name,
            "companyName": hubspot_account["account_name"],
            "customVariables": {
                "signal": signal.get("signal_title"),
                "why_now": signal.get("signal_summary"),
                "duvo_angle": "Reduce operational friction across supplier, store, and back-office workflows.",
            },
        },
        "message": {
            "subject": "Operational workflow question",
            "body": (
                f"Hi {first_name},\n\n"
                "Saw broader operations change around your team and thought this might be relevant. "
                "Duvo helps operations teams reduce manual coordination across supplier, store, and "
                "back-office workflows.\n\n"
                "Worth a short look if this is already on your team's radar?"
            ),
        },
        "dry_run": True,
        "human_approval_required": True,
    }

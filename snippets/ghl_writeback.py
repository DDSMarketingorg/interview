import os

import requests


GHL_BASE_URL = os.environ.get("GHL_BASE_URL", "https://services.leadconnectorhq.com")
GHL_API_KEY = os.environ["GHL_API_KEY"]


def ghl_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Version": "2021-07-28",
        "Content-Type": "application/json",
    }


def write_qualification_note(*, contact_id: str, note: str) -> None:
    response = requests.post(
        f"{GHL_BASE_URL}/contacts/{contact_id}/notes",
        headers=ghl_headers(),
        json={"body": note},
        timeout=15,
    )
    response.raise_for_status()


def update_contact_stage(*, contact_id: str, stage: str, custom_fields: dict[str, str | bool | None]) -> None:
    response = requests.put(
        f"{GHL_BASE_URL}/contacts/{contact_id}",
        headers=ghl_headers(),
        json={
            "tags": [stage],
            "customFields": [
                {"key": key, "field_value": value}
                for key, value in custom_fields.items()
            ],
        },
        timeout=15,
    )
    response.raise_for_status()


def sync_result_to_ghl(contact_id: str, result: dict[str, object]) -> None:
    note = (
        f"Reason: {result.get('reason_for_visit') or 'Unknown'} | "
        f"Pain: {result.get('pain_level') or 'Unknown'} | "
        f"Insurance: {result.get('insurance_provider') or 'None'} | "
        f"Preferred slot: {result.get('preferred_slot') or 'Not provided'}"
    )

    stage = "Urgent follow-up" if result.get("urgent") else "Qualified for scheduling"

    update_contact_stage(
        contact_id=contact_id,
        stage=stage,
        custom_fields={
            "reason_for_visit": result.get("reason_for_visit"),
            "pain_level": result.get("pain_level"),
            "insurance_provider": result.get("insurance_provider"),
            "preferred_slot": result.get("preferred_slot"),
            "urgent": bool(result.get("urgent")),
        },
    )
    write_qualification_note(contact_id=contact_id, note=note)

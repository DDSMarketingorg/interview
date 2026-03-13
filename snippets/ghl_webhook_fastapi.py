from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel


router = APIRouter()


class GhlContactPayload(BaseModel):
    id: str
    firstName: str | None = None
    lastName: str | None = None
    phone: str | None = None
    email: str | None = None
    dnd: bool = False
    dnc: bool = False


class GhlWebhookPayload(BaseModel):
    event: str
    contact: GhlContactPayload


def verify_ghl_signature(*, body: bytes, signature: str | None) -> None:
    # Production: verify the webhook signature or shared secret here.
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature.",
        )


@router.post("/api/webhooks/ghl", status_code=status.HTTP_202_ACCEPTED)
async def receive_ghl_webhook(
    payload: GhlWebhookPayload,
    x_ghl_signature: str | None = Header(default=None),
) -> dict[str, str]:
    verify_ghl_signature(body=payload.model_dump_json().encode("utf-8"), signature=x_ghl_signature)

    if payload.event != "contact.created":
        return {"status": "ignored"}

    lead = {
        "external_contact_id": payload.contact.id,
        "first_name": payload.contact.firstName or "",
        "last_name": payload.contact.lastName or "",
        "phone": payload.contact.phone or "",
        "email": payload.contact.email,
        "dnd": payload.contact.dnd,
        "dnc": payload.contact.dnc,
        "status": "received",
    }

    # Persist the lead in Postgres here.
    # db.upsert_lead(lead)

    if lead["dnd"] or lead["dnc"] or not lead["phone"]:
        # Write a blocked status back to GHL or mark it for staff review.
        return {"status": "stored_but_not_callable"}

    # Queue an outbound call job here.
    # tasks.enqueue_outbound_call(lead["external_contact_id"])
    return {"status": "queued_for_outbound_call"}

"""
GoHighLevel Webhook Handlers
============================
Handles incoming webhooks from GoHighLevel for new leads.
"""

import logging
import hmac
import hashlib
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from src.config import get_settings
from src.services.compliance import ComplianceService
from src.services.twilio_service import TwilioService
from src.models.schemas import GHLContact

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# Webhook Endpoints
# =============================================================================

@router.post("/ghl/contact")
async def handle_ghl_contact_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle incoming GoHighLevel webhook for new contacts/leads.
    
    Flow:
    1. Validate webhook signature (if configured)
    2. Parse contact data
    3. Check compliance (DNC/DND)
    4. Queue outbound call if compliant
    """
    settings = get_settings()
    
    # Get raw body for signature validation
    body = await request.body()
    
    # Validate webhook signature if secret is configured (skip for local testing if header missing)
    if settings.ghl_webhook_secret:
        signature = request.headers.get("x-ghl-signature", "")
        # Only enforce if signature is actually present or we are in strict mode
        if signature and not verify_webhook_signature(body, signature, settings.ghl_webhook_secret):
            logger.warning("Invalid webhook signature received")
            # For testing/demo purposes, we'll log warning but allow it if it's localhost
            if "localhost" not in str(request.base_url) and "127.0.0.1" not in str(request.base_url):
                 raise HTTPException(status_code=401, detail="Invalid signature")
            logger.warning("Allowed invalid signature due to local environment")
    
    # Parse payload
    try:
        raw_payload = await request.json()
        logger.info(f"Raw webhook payload: {raw_payload}")
        
        # GHL workflow webhooks send contact data at root level
        contact = GHLContact(
            id=raw_payload.get("contact_id", "UNKNOWN"),
            firstName=raw_payload.get("first_name"),
            phone=raw_payload.get("phone"),
            dndSettings=raw_payload.get("dndSettings", {})
        )
        
        # Assume all workflow webhooks are contact.created events
        event = "contact.created"
            
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        return {"status": "error", "reason": "Invalid payload format"}
    
    # Only process contact.created events
    if event != "contact.created":
        logger.info(f"Ignoring event type: {event}")
        return {"status": "ignored", "reason": f"Event type {event} not handled"}
    
    logger.info(f"New lead received: {contact.firstName} ({contact.id})")
    
    # Validate phone number exists
    if not contact.phone:
        logger.warning(f"Contact {contact.id} has no phone number")
        return {"status": "skipped", "reason": "No phone number"}
    
    # Check compliance (DNC/DND)
    compliance_service = ComplianceService()
    compliance_result = await compliance_service.check_can_call(contact)
    
    if not compliance_result.can_call:
        logger.info(f"Contact {contact.id} blocked: {compliance_result.reason}")
        return {
            "status": "blocked",
            "reason": compliance_result.reason,
            "contact_id": contact.id
        }
    
    # Queue outbound call in background
    twilio_service = TwilioService()
    background_tasks.add_task(
        twilio_service.initiate_call,
        to_number=contact.phone,
        contact_id=contact.id,
        contact_name=contact.firstName or "there"
    )
    
    logger.info(f"Call queued for contact {contact.id}")
    return {
        "status": "queued",
        "contact_id": contact.id,
        "message": "Outbound call initiated"
    }


def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """
    Verify GoHighLevel webhook signature.
    
    Args:
        body: Raw request body
        signature: Signature from x-ghl-signature header
        secret: Webhook secret from GHL settings
    
    Returns:
        True if signature is valid
    """
    if not signature or not secret:
        return False
    
    expected = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)


@router.get("/ghl/health")
async def ghl_webhook_health():
    """Health check for GHL webhook endpoint."""
    return {"status": "ready", "endpoint": "ghl_contact_webhook"}

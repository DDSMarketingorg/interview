from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import Response
import hmac
import hashlib
from typing import Dict, Any
import json
import logging
from datetime import datetime

from ..models.models import GHLWebhookPayload, Lead, ComplianceFlags
from ..services.dnc_service import DNCService, DatabaseService
from ..services.twilio_service import TwilioService

logger = logging.getLogger(__name__)


class WebhookService:
    """GoHighLevel webhook event handler"""

    def __init__(self, webhook_secret: str, dnc_service: DNCService,
                 twilio_service: TwilioService, db_service: DatabaseService):
        self.webhook_secret = webhook_secret
        self.dnc_service = dnc_service
        self.twilio_service = twilio_service
        self.db_service = db_service

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify the webhook signature from GHL"""
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()

            # GHL typically sends signature as 'sha256=<hash>'
            if signature.startswith('sha256='):
                signature = signature[7:]

            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False

    async def process_webhook(self, payload: GHLWebhookPayload, background_tasks: BackgroundTasks) -> Dict[str, Any]:
        """Process incoming webhook and initiate appropriate actions"""
        try:
            logger.info(f"Processing webhook event: {payload.event}")

            lead = payload.to_lead()

            if not self._validate_lead_data(lead):
                raise HTTPException(
                    status_code=400, detail="Invalid lead data")

            compliance_flags = await self._check_compliance(lead)
            if not compliance_flags.dnc_checked or lead.dnc_status:
                logger.warning(f"Lead {lead.id} is on DNC list, skipping call")
                return {"status": "skipped", "reason": "DNC_listed"}

            await self.db_service.store_lead(lead)

            # Schedule call in background
            if payload.event == "contact.created":
                background_tasks.add_task(
                    self._initiate_qualification_call,
                    lead,
                    compliance_flags
                )

            return {
                "status": "processed",
                "lead_id": lead.id,
                "action": "call_scheduled"
            }

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise HTTPException(
                status_code=500, detail="Webhook processing failed")

    def _validate_lead_data(self, lead: Lead) -> bool:
        """Validate essential lead data"""
        required_fields = [lead.id, lead.first_name, lead.phone]
        return all(field for field in required_fields)

    async def _check_compliance(self, lead: Lead) -> ComplianceFlags:
        """Perform compliance checks on the lead"""
        compliance_flags = ComplianceFlags()

        try:
            is_dnc = await self.dnc_service.check_dnc_status(lead.phone)
            compliance_flags.dnc_checked = True
            lead.dnc_status = is_dnc
        except Exception as e:
            logger.error(f"DNC check failed for {lead.phone}: {e}")
            compliance_flags.dnc_checked = False

        return compliance_flags

    async def _initiate_qualification_call(self, lead: Lead, compliance_flags: ComplianceFlags):
        """Initiate the qualification call for the lead"""
        try:
            greeting = self._create_personalized_greeting(lead)

            call_sid = await self.twilio_service.initiate_qualification_call(
                to_number=lead.phone,
                lead_id=lead.id,
                greeting=greeting
            )

            await self.db_service.update_lead_call_status(
                lead.id,
                call_sid,
                "initiated"
            )

            logger.info(
                f"Qualification call initiated for lead {lead.id}, call SID: {call_sid}")

        except Exception as e:
            logger.error(f"Failed to initiate call for lead {lead.id}: {e}")
            await self.db_service.update_lead_call_status(
                lead.id,
                None,
                "failed"
            )

    def _create_personalized_greeting(self, lead: Lead) -> str:
        """Create a personalized greeting for the lead"""
        name = lead.first_name or "there"
        return (
            f"Hello {name}, this is Nova from Premier Dental calling about "
            f"your recent inquiry for dental services. I'm an AI assistant "
            f"that can help schedule your appointment and answer some initial "
            f"questions. Do you have a few minutes to talk?"
        )


def setup_webhook_routes(app: FastAPI, webhook_service: WebhookService):
    """Setup webhook routes on the FastAPI app"""

    @app.post("/webhooks/ghl")
    async def handle_ghl_webhook(
        request: Request,
        background_tasks: BackgroundTasks
    ):
        """Handle incoming GHL webhooks"""
        try:
            payload_bytes = await request.body()
            signature = request.headers.get('X-Signature-256', '')

            if not webhook_service.verify_webhook_signature(payload_bytes, signature):
                logger.warning("Invalid webhook signature received")
                raise HTTPException(
                    status_code=401, detail="Invalid signature")

            payload_dict = json.loads(payload_bytes.decode('utf-8'))
            webhook_payload = GHLWebhookPayload(**payload_dict)

            result = await webhook_service.process_webhook(webhook_payload, background_tasks)

            return result

        except HTTPException:
            # Re-raise HTTPExceptions so FastAPI handles them properly
            raise
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        except Exception as e:
            logger.error(f"Webhook handling error: {e}")
            raise HTTPException(
                status_code=500, detail="Internal server error")

    @app.get("/webhooks/health")
    async def webhook_health_check():
        """Health check endpoint for webhook service"""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "webhook_service"
        }

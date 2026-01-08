"""
Call Manager Service
====================
Orchestrates the complete call flow from webhook to GHL update.
"""

import logging
from datetime import datetime

from src.models.schemas import GHLContact
from src.services.twilio_service import TwilioService
from src.services.ghl_client import GHLClient, CallData

logger = logging.getLogger(__name__)


class CallManager:
    """
    Orchestrates the complete call lifecycle.
    
    Flow:
    1. Receive lead from webhook
    2. Initiate Twilio call
    3. Manage AI conversation
    4. Update GHL with results
    """
    
    def __init__(self):
        self.twilio_service = TwilioService()
        self.ghl_client = GHLClient()
        self._active_calls: dict[str, dict] = {}  # call_sid -> call state
    
    async def initiate_lead_call(self, contact: GHLContact) -> str | None:
        """
        Initiate an outbound call to a new lead.
        """
        logger.info(f"Initiating call to lead: {contact.firstName} ({contact.id})")
        
        # Initiate Twilio call
        call_sid = await self.twilio_service.initiate_call(
            to_number=contact.phone,
            contact_id=contact.id,
            contact_name=contact.firstName or "there"
        )
        
        if not call_sid:
            logger.error(f"Failed to initiate call to {contact.id}")
            # Log failed attempt to GHL
            await self.ghl_client.add_contact_note(
                contact.id,
                f"⚠️ AI Call Failed - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                "Unable to initiate outbound call. Please follow up manually."
            )
            return None
        
        # Track active call
        self._active_calls[call_sid] = {
            "contact_id": contact.id,
            "contact_name": contact.firstName,
            "started_at": datetime.now(),
            "status": "initiated"
        }
        
        logger.info(f"Call {call_sid} initiated successfully")
        return call_sid
    
    async def handle_call_completed(
        self,
        call_sid: str,
        call_data: CallData
    ) -> bool:
        """
        Handle call completion and update GHL.
        """
        call_state = self._active_calls.get(call_sid)
        if not call_state:
            logger.warning(f"Call {call_sid} not found in active calls")
            return False
        
        contact_id = call_state["contact_id"]
        
        # Update GHL with call results
        success = await self.ghl_client.update_contact_with_call_data(
            contact_id=contact_id,
            call_data=call_data
        )
        
        # Clean up active call tracking
        del self._active_calls[call_sid]
        
        logger.info(f"Call {call_sid} completed, GHL updated: {success}")
        return success
    
    async def handle_escalation(
        self,
        call_sid: str,
        reason: str,
        transfer_number: str = "+15551234567"  # Default dental office number
    ) -> bool:
        """
        Handle emergency escalation during a call.
        """
        call_state = self._active_calls.get(call_sid)
        if not call_state:
            logger.warning(f"Call {call_sid} not found for escalation")
            return False
        
        # Transfer to human
        
        Returns:
            True if transfer successful
        """
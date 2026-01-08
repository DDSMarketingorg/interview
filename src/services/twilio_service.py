"""
Twilio Voice Service
====================
Manages Twilio outbound calls and voice operations.
"""

import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from src.config import get_settings

logger = logging.getLogger(__name__)


class TwilioService:
    """
    Twilio voice service for outbound call management.
    """
    
    def __init__(self):
        settings = get_settings()
        self.client = Client(
            settings.twilio_account_sid,
            settings.twilio_auth_token
        )
        self.from_number = settings.twilio_phone_number
        self.base_url = settings.app_base_url
    
    async def initiate_call(
        self,
        to_number: str,
        contact_id: str,
        contact_name: str = "there"
    ) -> str | None:
        """
        Initiate an outbound call to a lead.
        """
        try:
            # Build callback URL with contact context
            answer_url = (
                f"{self.base_url}/api/voice/answer"
                f"?contact_id={contact_id}"
                f"&contact_name={contact_name}"
            )
            
            status_url = f"{self.base_url}/api/voice/status"
            
            call = self.client.calls.create(
                to=to_number,
                from_=self.from_number,
                url=answer_url,
                status_callback=status_url,
                status_callback_event=["initiated", "ringing", "answered", "completed"],
                status_callback_method="POST",
                machine_detection="Enable",  # Detect voicemail
                machine_detection_timeout=5
            )
            
            logger.info(f"Call initiated to {to_number}, SID: {call.sid}")
            return call.sid
            
        except TwilioRestException as e:
            logger.error(f"Twilio error initiating call to {to_number}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error initiating call: {e}")
            return None
    
    async def transfer_to_human(self, call_sid: str, transfer_number: str) -> bool:
        """
        Transfer an active call to a human operator.
        """
        try:
            # Update call with transfer TwiML
            twiml = f"""
                <Response>
                    <Say voice="Polly.Joanna">
                        Please hold while I connect you with our dental staff.
                    </Say>
                    <Dial>{transfer_number}</Dial>
                </Response>
            """
            
            self.client.calls(call_sid).update(twiml=twiml)
            logger.info(f"Call {call_sid} transferring to {transfer_number}")
            return True
            
        except TwilioRestException as e:
            logger.error(f"Failed to transfer call {call_sid}: {e}")
            return False
    
    async def end_call(self, call_sid: str) -> bool:
        """
        End an active call.
        """
        try:
            self.client.calls(call_sid).update(status="completed")
            logger.info(f"Call {call_sid} ended")
            return True
        except Exception as e:
            logger.error(f"Failed to end call {call_sid}: {e}")
            return False
    
    async def get_call_status(self, call_sid: str) -> dict:
        """
        Get current status of a call.
        """
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                "sid": call.sid,
                "status": call.status,
                "duration": call.duration,
                "direction": call.direction,
                "answered_by": call.answered_by
            }
        except Exception as e:
            logger.error(f"Failed to get call status for {call_sid}: {e}")
            return {"error": str(e)}

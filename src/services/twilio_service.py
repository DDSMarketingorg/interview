from ..models.models import CallSession, CallStatus
import aiohttp
import asyncio
from datetime import datetime
import logging
from typing import Optional, Dict, Any
import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Pause

logger = logging.getLogger(__name__)


class TwilioService:
    """Twilio voice API integration for outbound calling"""

    def __init__(self, account_sid: str, auth_token: str, phone_number: str, webhook_base_url: str):
        self.client = Client(account_sid, auth_token)
        self.phone_number = phone_number
        self.webhook_base_url = webhook_base_url

    async def initiate_qualification_call(self, to_number: str, lead_id: str, greeting: str) -> str:
        """Initiate an outbound qualification call"""
        try:
            twiml_url = f"{self.webhook_base_url}/voice/start/{lead_id}"

            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=twiml_url,
                method='POST',
                status_callback=f"{self.webhook_base_url}/voice/status/{lead_id}",
                status_callback_event=['initiated',
                                       'ringing', 'answered', 'completed'],
                status_callback_method='POST',
                record=True,  # Record for quality and compliance
                timeout=30,   # Ring timeout
                machine_detection='Enable',  # Detect answering machines
                machine_detection_timeout=10
            )

            logger.info(f"Call initiated for lead {lead_id}: {call.sid}")
            return call.sid

        except Exception as e:
            logger.error(f"Failed to initiate call for lead {lead_id}: {e}")
            raise

    def create_initial_twiml(self, lead_id: str, greeting: str) -> str:
        """Create initial TwiML for call start"""
        response = VoiceResponse()

        # Initial greeting and consent
        response.say(greeting, voice='alice', language='en-US')
        response.pause(length=1)

        # Gather consent for conversation
        gather = Gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            action=f"/voice/consent/{lead_id}",
            method='POST'
        )
        gather.say(
            "To proceed with this call, please say 'yes' to confirm you'd like to "
            "discuss your dental needs, or say 'no' if you'd prefer not to continue.",
            voice='alice'
        )
        response.append(gather)

        # Fallback if no response
        response.say("I didn't hear a response. Goodbye!", voice='alice')
        response.hangup()

        return str(response)

    def create_conversation_twiml(self, lead_id: str, prompt: str, gather_action: str = "process") -> str:
        """Create TwiML for ongoing conversation"""
        response = VoiceResponse()

        # Say the AI-generated response
        response.say(prompt, voice='alice', language='en-US')

        # Gather user response with modern TwiML patterns
        gather = Gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            action=f"/voice/{gather_action}/{lead_id}",
            method='POST',
            speech_model='phone_call'  # Optimized for phone calls
        )

    def create_escalation_twiml(self, lead_id: str, reason: str = "high_priority") -> str:
        """Create TwiML for emergency escalation"""
        response = VoiceResponse()

        if reason == "emergency":
            response.say(
                "I understand this sounds urgent. Let me connect you immediately "
                "with one of our dental professionals who can help you right away.",
                voice='alice'
            )
        else:
            response.say(
                "Let me connect you with one of our team members who can "
                "better assist you with your dental needs.",
                voice='alice'
            )

        # Transfer to human
        response.dial(
            os.getenv('ESCALATION_PHONE', '+1234567890'),
            timeout=30,
            action=f"/voice/escalation-complete/{lead_id}",
            method='POST'
        )

        return str(response)

    def create_completion_twiml(self, lead_id: str, appointment_scheduled: bool = False) -> str:
        """Create TwiML for call completion"""
        response = VoiceResponse()

        if appointment_scheduled:
            response.say(
                "Perfect! I've scheduled your appointment and you'll receive a "
                "confirmation shortly. Thank you for choosing Premier Dental, "
                "and we look forward to seeing you soon!",
                voice='alice'
            )
        else:
            response.say(
                "Thank you for your time today. One of our team members will "
                "follow up with you soon regarding your dental needs. "
                "Have a great day!",
                voice='alice'
            )

        response.hangup()
        return str(response)

    async def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """Get current status of a Twilio call"""
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                "sid": call.sid,
                "status": call.status,
                "direction": call.direction,
                "duration": call.duration,
                "price": call.price,
                "answered_by": call.answered_by
            }
        except Exception as e:
            logger.error(f"Error fetching call status for {call_sid}: {e}")
            return {}

    async def end_call(self, call_sid: str) -> bool:
        """Programmatically end a call"""
        try:
            call = self.client.calls(call_sid).update(status='completed')
            logger.info(f"Call {call_sid} ended successfully")
            return True
        except Exception as e:
            logger.error(f"Error ending call {call_sid}: {e}")
            return False

    def handle_machine_detection(self, lead_id: str, answered_by: str) -> str:
        """Handle calls answered by machines"""
        response = VoiceResponse()

        if answered_by == 'machine_start':
            # Leave a brief message
            response.pause(length=2)  # Wait for beep
            response.say(
                f"Hello, this is Nova from Premier Dental. We received your "
                f"inquiry about dental services. Please call us back at your "
                f"convenience to schedule your appointment. Thank you!",
                voice='alice'
            )

        response.hangup()
        return str(response)

    def setup_voice_routes(self, app, ai_service, db_service):
        """Setup voice webhook routes"""

        @app.post("/voice/start/{lead_id}")
        async def handle_call_start(lead_id: str, request):
            """Handle call initiation"""
            form = await request.form()
            answered_by = form.get('AnsweredBy')

            if answered_by in ['machine_start', 'machine_end_beep', 'machine_end_silence']:
                return Response(
                    self.handle_machine_detection(lead_id, answered_by),
                    media_type="application/xml"
                )

            session = CallSession(
                session_id=f"session_{lead_id}_{datetime.utcnow().timestamp()}",
                lead_id=lead_id,
                twilio_call_sid=form.get('CallSid'),
                status=CallStatus.IN_PROGRESS
            )

            await db_service.create_call_session(session)

            lead = await db_service.get_lead(lead_id)
            greeting = f"Hello {lead.first_name}, this is Nova from Premier Dental..."

            return Response(
                self.create_initial_twiml(lead_id, greeting),
                media_type="application/xml"
            )

        @app.post("/voice/consent/{lead_id}")
        async def handle_consent(lead_id: str, request):
            """Handle consent response"""
            form = await request.form()
            speech_result = form.get('SpeechResult', '').lower()

            if 'yes' in speech_result or 'okay' in speech_result:
                # Proceed with qualification
                prompt = await ai_service.generate_first_question(lead_id)
                return Response(
                    self.create_conversation_twiml(lead_id, prompt),
                    media_type="application/xml"
                )
            else:
                # End call politely
                response = VoiceResponse()
                response.say("No problem. Have a great day!", voice='alice')
                response.hangup()
                return Response(str(response), media_type="application/xml")

        @app.post("/voice/process/{lead_id}")
        async def handle_conversation(lead_id: str, request):
            """Handle ongoing conversation"""
            form = await request.form()
            speech_result = form.get('SpeechResult', '')
            call_sid = form.get('CallSid')
            ai_response = await ai_service.process_conversation_turn(
                lead_id, speech_result, call_sid
            )

            if ai_response.get('escalate'):
                return Response(
                    self.create_escalation_twiml(
                        lead_id, ai_response.get('escalation_reason')),
                    media_type="application/xml"
                )
            elif ai_response.get('complete'):
                return Response(
                    self.create_completion_twiml(
                        lead_id,
                        ai_response.get('appointment_scheduled', False)
                    ),
                    media_type="application/xml"
                )
            else:
                return Response(
                    self.create_conversation_twiml(
                        lead_id, ai_response['response']),
                    media_type="application/xml"
                )

        @app.post("/voice/status/{lead_id}")
        async def handle_call_status(lead_id: str, request):
            """Handle call status updates"""
            form = await request.form()
            call_status = form.get('CallStatus')
            call_sid = form.get('CallSid')

            await db_service.update_call_session_status(call_sid, call_status)

            logger.info(f"Call status update for {lead_id}: {call_status}")
            return {"status": "received"}

        return app

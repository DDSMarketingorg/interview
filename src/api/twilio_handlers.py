"""
Twilio Voice Webhook Handlers
=============================
Handles Twilio voice callbacks for call flow management.
"""

import logging
from fastapi import APIRouter, Request, Response, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse, Gather, Connect, Stream

from src.config import get_settings
from src.ai.agent import get_agent
from src.services.ghl_client import GHLClient

logger = logging.getLogger(__name__)
router = APIRouter()

# Voice configuration constants
DENTAL_HINTS = "tooth pain, appointment, insurance, sun life, delta dental, one, two, three, four, five, six, seven, eight, nine, ten, yes, no, cleaning, checkup, emergency, hurt, swelling"
VOICE_NAME = "Google.en-US-Neural2-F"
LANGUAGE = "en-US"
SPEECH_MODEL = "phone_call"



# =============================================================================
# Voice Endpoints
# =============================================================================

@router.post("/answer")
async def handle_call_answer(request: Request):
    """
    Initial TwiML response when call is answered.
    """
    settings = get_settings()
    contact_id = request.query_params.get("contact_id", "")
    contact_name = request.query_params.get("contact_name", "there")
    
    response = VoiceResponse()
    
    # 1. Greeting
    greeting = (
        f"Hello {contact_name}, this is Nova from Nova Dentistry "
        "calling about your appointment request. How can I help you today?"
    )
    
    # Use Gather to collect speech input
    gather = Gather(
        input="speech",
        action=f"{settings.app_base_url}/api/voice/process?contact_id={contact_id}&contact_name={contact_name}",
        method="POST",
        language=LANGUAGE,
        speechTimeout="auto",
        speechModel=SPEECH_MODEL,
        hints=DENTAL_HINTS
    )
    gather.say(greeting, voice=VOICE_NAME)
    response.append(gather)
    
    # If no input, prompt again
    response.redirect(f"{settings.app_base_url}/api/voice/no-input?contact_id={contact_id}&contact_name={contact_name}")
    
    return Response(content=str(response), media_type="application/xml")


@router.post("/process")
async def process_speech(
    request: Request,
    SpeechResult: str = Form(default=""),
    Confidence: float = Form(default=0.0),
    CallSid: str = Form(default="")
):
    """
    Process speech input from caller and generate AI response.
    """
    settings = get_settings()
    contact_id = request.query_params.get("contact_id", "")
    contact_name = request.query_params.get("contact_name", "")
    
    logger.info(f"Speech received: '{SpeechResult}' (confidence: {Confidence})")
    
    if not SpeechResult:
        return await handle_no_input(request)
    
    # Process with AI agent
    agent = get_agent()
    ai_response = await agent.process_input(
        user_input=SpeechResult,
        contact_id=contact_id,
        call_sid=CallSid,
        contact_name=contact_name
    )
    
    response = VoiceResponse()
    
    # Check if conversation should end
    if ai_response.should_end_call:
        response.say(ai_response.message, voice="Google.en-US-Neural2-F")
        response.say("Thank you for calling Nova Dentistry. Goodbye!", voice="Google.en-US-Neural2-F")
        response.hangup()
        
        # Update GHL with collected data
        if ai_response.collected_data:
            ghl_client = GHLClient()
            await ghl_client.update_contact_with_call_data(
                contact_id=contact_id,
                call_data=ai_response.collected_data
            )
        return Response(content=str(response), media_type="application/xml")
    
    # Check transfer
    if ai_response.needs_transfer:
        response.say(
            "I understand this is urgent. Let me connect you with our staff right away.",
            voice="Google.en-US-Neural2-F"
        )
        response.dial("+1555DENTIST")
        return Response(content=str(response), media_type="application/xml")
    
    # Continue conversation
    gather = Gather(
        input="speech",
        action=f"{settings.app_base_url}/api/voice/process?contact_id={contact_id}&contact_name={contact_name}",
        method="POST",
        language=LANGUAGE,
        speechTimeout="auto",
        speechModel=SPEECH_MODEL,
        hints=DENTAL_HINTS
    )
    gather.say(ai_response.message, voice=VOICE_NAME)
    response.append(gather)
    
    # Fallback if no input
    response.redirect(f"{settings.app_base_url}/api/voice/no-input?contact_id={contact_id}&contact_name={contact_name}")
    
    return Response(content=str(response), media_type="application/xml")


# Deprecated/Unused legacy process endpoint (keeping for reference or removing? Plan calls to refactor completely)
# We can just remove the old process_speech since handle_recording replaces it.



@router.post("/no-input")
async def handle_no_input(request: Request):
    """Handle case when no speech input is detected."""
    settings = get_settings()
    contact_id = request.query_params.get("contact_id", "")
    contact_name = request.query_params.get("contact_name", "")
    
    response = VoiceResponse()
    
    gather = Gather(
        input="speech",
        action=f"{settings.app_base_url}/api/voice/process?contact_id={contact_id}&contact_name={contact_name}",
        method="POST",
        language=LANGUAGE,
        speechTimeout="auto",
        speechModel=SPEECH_MODEL,
        hints=DENTAL_HINTS
    )
    gather.say(
        "I'm sorry, I didn't catch that. How can I help you with your dental appointment?",
        voice=VOICE_NAME
    )
    response.append(gather)
    
    # After 3 attempts, end call gracefully
    response.say(
        "I'm having trouble hearing you. Please call our office directly at 555-DENTIST. Goodbye!",
        voice="Google.en-US-Neural2-F"
    )
    response.hangup()
    
    return Response(content=str(response), media_type="application/xml")


@router.post("/status")
async def handle_call_status(
    CallSid: str = Form(default=""),
    CallStatus: str = Form(default=""),
    CallDuration: int = Form(default=0)
):
    """
    Handle Twilio call status callbacks.
    Log call completion and metrics.
    """
    logger.info(f"Call {CallSid} status: {CallStatus}, duration: {CallDuration}s")
    
    # Store call metrics (could save to database here)
    return {"status": "logged", "call_sid": CallSid, "call_status": CallStatus}

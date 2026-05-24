import os
import json
import base64
import asyncio
from fastapi import FastAPI, BackgroundTasks, WebSocket
from fastapi.websockets import WebSocketDisconnect
import websockets
from twilio.rest import Client
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
DOMAIN = os.getenv("DOMAIN")
PORT = os.getenv("PORT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="AI Voice Assistant")
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

active_calls: dict[str, dict] = {}

class GHLContact(BaseModel):
    id: str
    firstName: str
    phone: str
    email: str
    practiceName: str

class GHLContactRequest(BaseModel):
    event: str
    contact: GHLContact

class GHLContactResponse(BaseModel):
    contact_status: str
    contact_id: str

def make_twilio_call(contact: GHLContact):
    practice_name = contact.practiceName
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Connect>
            <Stream url="wss://{DOMAIN}/media-stream" />
        </Connect>
    </Response>"""

    call = twilio_client.calls.create(
        to=contact.phone,
        from_=TWILIO_PHONE_NUMBER,
        twiml=twiml,
    )

    active_calls[call.sid] = contact

    print(f"Call initiated: {call.sid} -> {contact.firstName} at {contact.phone}")

@app.post("/ghl/contact")
async def handle_ghl_contact(request: GHLContactRequest, background_tasks: BackgroundTasks) -> GHLContactResponse:
    print("handle_ghl_contact")
    if request.event != "contact.created":
        return GHLContactResponse(contact_status="ignored", contact_id=request.contact.id)

    # ignore contacts with empty or whitespace data
    # we need a phone number to call and a practice to book the appointment for
    if not request.contact.firstName.strip() or \
       not request.contact.phone.strip() or \
       not request.contact.practiceName.strip():
        return GHLContactResponse(contact_status="invalid", contact_id=request.contact.id)

    # enqueue twilio call so reach out to contact
    background_tasks.add_task(make_twilio_call, request.contact)

    return GHLContactResponse(contact_status="contacting", contact_id=request.contact.id)

@app.websocket('/media-stream')
async def handle_twilio_openai_stream(twilio_ws: WebSocket):
    print("handle_twilio_openai_stream")
    await twilio_ws.accept()

    temperature = 0.8
    async with websockets.connect(
        f"wss://api.openai.com/v1/realtime?model=gpt-realtime&temperature={temperature}",
        additional_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
    ) as openai_ws:
        stream_sid = None
        contact = None

        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid, contact
            try:
                async for message in twilio_ws.iter_text():
                    data = json.loads(message)

                    if data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        call_sid = data['start'].get('callSid')
                        if call_sid and call_sid in active_calls:
                            contact = active_calls[call_sid]
                            await initialize_openai_realtime_session(openai_ws, contact)
                            await send_initial_openai_conversation_item(openai_ws, contact)
                    elif data['event'] == 'media' and openai_ws.state.name == 'OPEN':
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.state.name == 'OPEN':
                    await openai_ws.close()
            finally:
                if call_sid:
                    active_calls.pop(call_sid, None)

        async def receive_from_openai():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid, contact
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)

                    if response['type'] == 'response.output_audio.delta' and response.get('delta'):
                        try:
                            audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": audio_payload
                                }
                            }
                            await twilio_ws.send_json(audio_delta)
                        except Exception as e:
                            print(f"Error processing audio data: {e}")
                    elif response['type'] == 'response.function_call_arguments.done':
                        call_id = response['call_id']
                        name = response['name']
                        try:
                            arguments = json.loads(response['arguments'])
                        except json.JSONDecodeError:
                            arguments = {}
                        result = handle_tool_call(name, arguments, contact)
                        await openai_ws.send(json.dumps({
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": call_id,
                                "output": json.dumps(result)
                            }
                        }))
                        await openai_ws.send(json.dumps({"type": "response.create"}))
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")
                
        await asyncio.gather(receive_from_twilio(), receive_from_openai())

def handle_tool_call(name: str, arguments: dict, contact: GHLContact) -> dict:
    match name:
        case "qualify_lead":
            pain = arguments.get("pain_level", "N/A")
            insurance = arguments.get("insurance_provider") or "none"
            reason = arguments.get("reason_for_visit", "N/A")
            preferred = arguments.get("preferred_day_time", "N/A")

            print(f"[QUALIFY] Contact {contact.id} ({contact.firstName} {contact.phone}): "
                  f"pain={pain}/10 insurance={insurance} reason='{reason}' preferred='{preferred}'")

            if isinstance(pain, (int, float)) and int(pain) >= 8:
                return {"escalate": True, "message": "High pain level detected. The office will prioritize this case."}

            return {"status": "recorded", "message": "Your details have been noted. Let me check available appointments."}

        case "schedule_appointment":
            date_time = arguments.get("date_time", "TBD")
            print(f"[SCHEDULE] Contact {contact.id} ({contact.firstName}): appointment={date_time}")
            return {"status": "booked", "confirmation": f"Appointment set for {date_time}. A confirmation will be sent to {contact.email}."}

        case "escalate_emergency":
            emergency = arguments.get("emergency_type", "not specified")
            print(f"!!! [911] Contact {contact.id} ({contact.firstName} {contact.phone}) "
                  f"LIFE-THREATENING EMERGENCY: {emergency}")
            return {"status": "911", "message": "Stop. This is a medical emergency. Hang up and call 911 immediately. Do not wait."}

        case "escalate_to_human":
            reason = arguments.get("reason", "not specified")
            print(f"[ESCALATE] Contact {contact.id} ({contact.firstName} {contact.phone}) "
                  f"needs human callback. Reason: {reason}")
            return {"status": "escalated", "message": "Someone from the office will call you back right away to help."}

        case "opt_out":
            print(f"[DNC] Contact {contact.id} ({contact.firstName} {contact.phone}) requested no further contact")
            return {"status": "opted_out", "message": "Noted. You will not be contacted again."}

        case _:
            print(f"[UNKNOWN_TOOL] {name} args={arguments}")
            return {"status": "unknown_tool", "name": name}

async def initialize_openai_realtime_session(openai_ws, contact: GHLContact):
    system_message = f"""You are a professional AI scheduling assistant calling on behalf of {contact.practiceName}, a dental office. You're speaking with someone who recently submitted a request for a dental appointment. Your job is to qualify the lead and help book a visit.

    Identity & disclosure:
    - You are an AI assistant. Make that clear in your greeting, and again if asked.

    Your goals, in order:
    1. Confirm you're speaking with the right person.
    2. Briefly reference that they requested an appointment.
    3. Collect: reason for the visit, pain level on a 1-to-10 scale, whether they have dental insurance (and the provider if so), and a preferred day/time.
    4. Offer to book an appointment and confirm the details back to them.

    Using tools:
    - Use your tools to record the caller's details and to check or book appointment times. Call the qualification tool once you have the information rather than only talking about it.

    Safety & escalation (important):
    - You are NOT a medical professional. Never diagnose, never give clinical or treatment advice, never recommend medication.
    - There are two escalation paths. Use the right one:
      1. escalate_emergency: Life-threatening emergencies ONLY — uncontrolled bleeding, physical trauma to the face/mouth, airway obstruction, signs of stroke or heart attack. Tell the caller to hang up and call 911 immediately. Do not wait for a callback.
      2. escalate_to_human: Dental urgency (pain 8-10, swelling with fever, signs of serious infection) OR the caller asks to speak to a person OR the caller is unable to complete the booking process. Calmly let them know someone from the office will reach out to them right away.
    - qualify_lead may return an escalate flag for high pain — read that result and escalate if indicated.

    Conversation style (this is a live phone call):
    - Keep replies short and natural. Ask one question at a time. Never read lists or formatting aloud.
    - Be warm, efficient, and respectful of their time.
    - Collect only what's needed to schedule. Do not ask for full medical history, SSN, or payment details.
    - If it's a bad time, offer to reschedule the call. If they ask not to be called again, acknowledge it, stop, and don't push. If they're not interested, thank them and end politely.
    - If you can't handle something, offer to have a human from the office follow up.
    """

    session_update = {
        "type": "session.update",
        "session": {
            "type": "realtime",
            "model": "gpt-realtime",
            "output_modalities": ["audio"],
            "audio": {
                "input": {
                    "format": {"type": "audio/pcmu"},
                    "turn_detection": {"type": "server_vad"}
                },
                "output": {
                    "format": {"type": "audio/pcmu"},
                    "voice": "alloy"
                }
            },
            "instructions": system_message,
            "tools": [
                {
                    "type": "function",
                    "name": "qualify_lead",
                    "description": "Record the caller's qualification details once collected — pain level, insurance provider, reason for visit, and preferred day/time. Call this as soon as you have the information rather than only talking about it.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pain_level": {"type": "integer", "minimum": 1, "maximum": 10, "description": "Self-reported pain on a 1-10 scale"},
                            "insurance_provider": {"type": "string", "description": "Dental insurance provider name, or 'none' if no insurance"},
                            "reason_for_visit": {"type": "string", "description": "Chief complaint or reason for the dental visit"},
                            "preferred_day_time": {"type": "string", "description": "Preferred appointment day and time, e.g. 'Monday afternoon'"}
                        },
                        "required": ["pain_level", "reason_for_visit"]
                    }
                },
                {
                    "type": "function",
                    "name": "schedule_appointment",
                    "description": "Book an appointment for the caller at the given date and time. Only call after qualification is complete and the caller has agreed to book.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date_time": {"type": "string", "description": "Confirmed date and time, e.g. '2025-06-15 14:00'"}
                        },
                        "required": ["date_time"]
                    }
                },
                {
                    "type": "function",
                    "name": "escalate_emergency",
                    "description": "Caller has a life-threatening emergency — uncontrolled bleeding, trauma, cannot breathe, stroke/heart attack signs. Tell them to call 911 immediately.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "emergency_type": {"type": "string", "description": "Brief description of the life-threatening emergency"}
                        },
                        "required": ["emergency_type"]
                    }
                },
                {
                    "type": "function",
                    "name": "escalate_to_human",
                    "description": "Escalate to the dental office for human callback. Use for dental urgency (pain 8+, swelling with fever, infection signs), caller requests a person, or caller cannot complete booking.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {"type": "string", "description": "Why this needs human follow-up"}
                        },
                        "required": ["reason"]
                    }
                },
                {
                    "type": "function",
                    "name": "opt_out",
                    "description": "Caller asked not to be contacted again. Record and stop the conversation politely.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ],
        }
    }

    await openai_ws.send(json.dumps(session_update))

async def send_initial_openai_conversation_item(openai_ws, contact: GHLContact):
    """Send initial conversation so AI talks first."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                    f"The call has just connected. Open the conversation: greet {contact.firstName} warmly, "
                    f"introduce yourself as an automated AI scheduling assistant calling on behalf of "
                    f"{contact.practiceName} about the dental appointment request they recently submitted, and "
                    f"confirm you're speaking with {contact.firstName}. Keep it to one or two short, friendly "
                    f"sentences, then stop and wait for their reply."
                )
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))
    

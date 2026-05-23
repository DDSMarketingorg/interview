import os
import json
import asyncio
from fastapi import FastAPI, BackgroundTasks, WebSocket
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

class GHLContact(BaseModel):
    id: str
    firstName: str
    phone: str
    email: str

class GHLContactRequest(BaseModel):
    event: str
    contact: GHLContact

class GHLContactResponse(BaseModel):
    contact_status: str
    contact_id: str

def make_twilio_call():
    print("making call...")

@app.post("/ghl/contact")
async def handle_ghl_contact(request: GHLContactRequest, background_tasks: BackgroundTasks) -> GHLContactResponse:
    print("handle_ghl_contact")
    if request.event != "contact.created":
        return GHLContactResponse(contact_status="ignored", contact_id=request.contact.id)

    # enqueue twilio call so reach out to contact
    background_tasks.add_task(make_twilio_call)

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
        await initialize_openai_realtime_session(openai_ws)
        await send_initial_openai_conversation_item(openai_ws)

        



async def initialize_openai_realtime_session(openai_ws):
    system_message = (
        "You are a helpful AI assistant who loves to chat about "
        "anything the user is interested in and is prepared to offer them facts. "
        "You have a penchant for dad jokes, owl jokes, and rickrolling – subtly. "
        "Always stay positive, but work in a joke when appropriate."
    )

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
        }
    }

    await openai_ws.send(json.dumps(session_update))

async def send_initial_openai_conversation_item(openai_ws):
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
                        "Greet the user with 'Hello there! I am an AI voice assistant powered by "
                        "Twilio and the OpenAI Realtime API. You can ask me for facts, jokes, or "
                        "anything you can imagine. How can I help you?'"
                    )
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))
    

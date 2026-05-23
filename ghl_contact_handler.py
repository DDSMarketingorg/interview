import os
from fastapi import FastAPI, BackgroundTasks, WebSocket
from twilio.rest import Client
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
DOMAIN = os.getenv("DOMAIN")
PORT = os.getenv("PORT")

app = FastAPI(title="AI Voice Assistant")
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

class Contact(BaseModel):
    id: str
    firstName: str
    phone: str
    email: str

class GHLContactRequest(BaseModel):
    event: str
    contact: Contact

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

    while True:
        msg = await twilio_ws.receive_text()
        print("message: ", msg)
        await twilio_ws.send_text("Hello")

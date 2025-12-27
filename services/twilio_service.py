from uuid import uuid4
from twilio.rest import Client
from config import Config
import os


account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)


def activate_voice_agent(lead):
    session_id = str(uuid4())
    # simulate dialogue
    # dialogue_result = run_ai_dialogue(lead)
    # store_result(session_id, dialogue_result)

    return session_id


# def make_call(to_phone: str, lead_id: str) -> str:
#     try:
#         call = client.calls.create(
#             to=to_phone,
#             from_=os.environ["TWILIO_PHONE_NUMBER"],
#             url=f"https://059f854ab101f7.lhr.life/voice/answer/{lead_id}",
#             status_callback="https://059f854ab101f7.lhr.life/voice/status",
#             status_callback_event=["initiated", "completed"],
#             method="POST"
#         )
#         print("Call created:", call.sid)
#         return call.sid
#     except Exception as e:
#         print("Error creating call:", e)
#         return ""


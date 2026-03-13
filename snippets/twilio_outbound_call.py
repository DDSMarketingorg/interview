import os

from twilio.rest import Client


TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = os.environ["TWILIO_PHONE_NUMBER"]
PUBLIC_API_BASE_URL = os.environ["PUBLIC_API_BASE_URL"]


client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def start_outbound_call(*, lead_id: str, to_number: str) -> str:
    call = client.calls.create(
        to=to_number,
        from_=TWILIO_PHONE_NUMBER,
        url=f"{PUBLIC_API_BASE_URL}/api/twilio/calls/{lead_id}/twiml",
        status_callback=f"{PUBLIC_API_BASE_URL}/api/twilio/calls/{lead_id}/status",
        status_callback_event=["initiated", "ringing", "answered", "completed"],
        method="POST",
    )
    return call.sid


if __name__ == "__main__":
    sid = start_outbound_call(lead_id="CNT_xxx", to_number="+14165551234")
    print(f"Outbound call started: {sid}")

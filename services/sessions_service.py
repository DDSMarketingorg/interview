from typing import Literal


ConversationState = Literal[
    "INIT",
    "COLLECTING_INFO",
    "AWAITING_SLOT",
    "AWAITING_CONFIRMATION",
    "BOOKED",
    "ESCALATED"
]

sessions = {}
def get_session(sid):
    if sid not in sessions:
        sessions[sid] = {
            "state": "INIT",
            "data": {
                "chief_complaint": None,
                "pain_level": None,
                "insurance_provider": None,
                "preferred_slot": None,
                "escalation_required": False
            }
        }
    return sessions[sid]


CONFIRM_WORDS = [
    "yes", "yes please", "ok", "okay",
    "sure", "go ahead", "confirm", "please do"
]

def is_confirmation(text: str) -> bool:
    text = text.lower().strip()
    return any(word in text for word in CONFIRM_WORDS)

def merge_session_data(session_data, new_data):
    for k, v in new_data.items():
        if v is not None:
            # ⛔ اجازه overwrite بیمه بعد از ست شدن نده
            if k == "insurance_provider" and session_data.get(k):
                continue
            session_data[k] = v



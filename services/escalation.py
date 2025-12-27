def check_escalation(data):
    if data.get("escalation_required"):
        return True, data.get("escalation_reason", "unspecified")
    return False, None

def build_human_reply(data: dict) -> str:
    if data.get("escalation_required"):
        return (
            "Thanks for explaining. This sounds urgent. "
            "I'm going to transfer you to a human receptionist right now."
        )

    # 1️⃣ Insurance FIRST — single responsibility
    if not data.get("insurance_provider"):
        return "Got it. Do you have dental insurance?"

    # 2️⃣ Slot SECOND
    if not data.get("preferred_slot"):
        return (
            "Thanks. I can help you schedule an appointment. "
            "Do you have a preferred day and time?"
        )

    # 3️⃣ Confirmation
    return (
        f"I can reserve an appointment for you on {data['preferred_slot']}. "
        "Should I go ahead and book it?"
    )


def next_agent_reply(session: dict) -> str:
    data = session["data"]

    # 1️⃣ Escalation
    if data.get("escalation_required"):
        session["state"] = "ESCALATED"
        return (
            "This sounds urgent. I am transferring you to a human receptionist."
        )

    # 2️⃣ Insurance missing
    if not data.get("insurance_provider"):
        session["state"] = "COLLECTING_INFO"
        return "Do you have dental insurance?"

    # 3️⃣ Slot missing (مهم‌ترین اصلاح)
    if not data.get("preferred_slot"):
        session["state"] = "AWAITING_SLOT"
        return "What day and time works best for you?"

    # 4️⃣ Slot exists → confirmation (حتی اگر بیمه نداشته باشه)
    session["state"] = "AWAITING_CONFIRMATION"
    return (
        f"I can reserve an appointment for you on {data['preferred_slot']}. "
        "Should I go ahead and book it?"
    )



import re

KNOWN_INSURANCES = [
    "delta dental",
    "blue cross",
    "aetna",
    "cigna",
    "metlife",
]

NO_INSURANCE_PATTERNS = [
    "no insurance",
    "i don't have insurance",
    "i do not have insurance",
    "without insurance",
    "not insured",
]


def extract_insurance_fallback(text: str) -> str | None:
    text_lower = text.lower()

    # 🚫 Explicit NO insurance
    for phrase in NO_INSURANCE_PATTERNS:
        if phrase in text_lower:
            return "NO_INSURANCE"

    # ✅ Known insurances
    for insurance in KNOWN_INSURANCES:
        if insurance in text_lower:
            return insurance.title()

    return None




import re
from datetime import datetime, timedelta

def extract_preferred_slot(text: str) -> str | None:
    text = text.lower()

    # مثال ساده: saturday at 3
    match = re.search(r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday).*?(\d{1,2})(?:[:.](\d{2}))?", text)
    if not match:
        return None

    day_name = match.group(1)
    hour = int(match.group(2))
    minute = int(match.group(3) or 0)

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    today = datetime.now()
    target_weekday = weekdays[day_name]
    days_ahead = (target_weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7

    target_date = today + timedelta(days=days_ahead)
    target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

    return target_date.strftime("%Y-%m-%d %H:%M")
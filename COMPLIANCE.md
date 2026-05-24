# Compliance

## Data Collected (PHI)

The AI asks for only four things:
- Reason for visit
- Pain level
- Insurance provider
- Prefered day/time for appointment

The prompt explicitly forbids the AI from asking medical history, SSN, payment info, or "full history" (`ghl_twilio_openai_assistant.py:257`).

The AI also announces it is not a medical professional and cannot give clinical advice (`ghl_twilio_openai_assistant.py:241`).

All collected data is stored as a plain-text note on the GHL contact (`ghl_twilio_openai_assistant.py:393-399`). The note includes the contact's phone and email which come from the GHL record itself, not from the caller.

---

## Do Not Call / Do Not Disturb
 
**Before the call** (`ghl_twilio_openai_assistant.py:80-92`): The system fetches the contact from GHL and checks:
- The `dnd` field (GHL's built-in flag)
- The `ai-opted-out` tag (set by this system during a previous call)

If either is true, the call is skipped and a note is logged.

**During the call** (`ghl_twilio_openai_assistant.py:440-447`): If the caller asks not to be contacted again, the `opt_out` tool sets both `dnd=True` and the `ai-opted-out` tag on their GHL record. A future webhook for the same contact will be blocked by the pre-call check above.

---

## Escalation

AI tool calls will trigger two escalation paths:
- For life-threatening signs the AI tells the caller to hang up and dial 911 and the call ends immediately.
- Pain 8–10, swelling + fever, signs of infection, caller asks for a person, caller can't complete booking | AI tells caller someone from the office will call back.

---

## Encryption

Data in transit is encrypted by the platforms used (HTTPS to GHL, WSS to Twilio/OpenAI). Data at rest (GHL notes) depends on GHL's own encryption. This system does not implement its own encryption.
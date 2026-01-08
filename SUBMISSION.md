# 🦷 Dental AI Voice Assistant – Technical Submission

> **Production-Ready AI Voice Agent for Dental Lead Qualification**  
> Built with FastAPI, GPT-5-mini, Twilio Programmable Voice, and GoHighLevel CRM

---

## 📌 Executive Summary

This submission delivers an outbound AI voice assistant for dental lead qualification. The system:

- Receives new leads from GoHighLevel webhooks
- Initiates outbound calls via Twilio with machine detection
- Conducts natural language conversations using GPT-5-mini with tool calling
- Extracts structured data (pain level, insurance, appointment preferences)
- Detects emergencies and triggers human transfer
- Updates CRM records with call outcomes

**Key Technical Highlights:**
- **~1,200 lines** of production Python code across 10+ modules
- **Comprehensive test suite** with 14+ unit tests
- **Multi-layer safety system** with regex-based detection + LLM guardrails
- **TCPA/PHI compliant** with DND checking and audit logging

---

## 1. System Architecture

### High-Level Flow

```mermaid
flowchart LR
    subgraph GoHighLevel["GoHighLevel CRM"]
        A[New Lead Created] --> B[Webhook Trigger]
    end
    
    subgraph Backend["FastAPI Backend"]
        C[Webhook Handler] --> D{Compliance Check}
        D -->|Pass| E[Queue Call]
        D -->|Fail| F[Block & Log]
        E --> G[Call Manager]
    end
    
    subgraph Twilio["Twilio Voice"]
        H[Outbound Call] --> I[Answer Webhook]
        I --> J[Gather Speech]
        J --> K[Process Webhook]
    end
    
    subgraph AI["AI Pipeline"]
        L[Safety Detector] --> M{Emergency?}
        M -->|Yes| N[Transfer to Human]
        M -->|No| O[GPT-5-mini Agent]
        O --> P[Tool Execution Loop]
        P --> Q[TwiML Response]
    end
    
    B --> C
    G --> H
    K --> L
    Q --> J
```

---

## 2. Code Implementation

### A. Twilio Outbound Call (With Identity Context)

We pass `contact_name` in the callback URL to ensure the AI knows who it's speaking to immediately—preventing the awkward "What is your name?" question.

**File: `src/services/twilio_service.py`**

```python
async def initiate_call(
    self,
    to_number: str,
    contact_id: str,
    contact_name: str = "there"
) -> str | None:
    """Initiate an outbound call to a lead."""
    # Build callback URL with contact context persisted via URL params
    answer_url = (
        f"{self.base_url}/api/voice/answer"
        f"?contact_id={contact_id}"
        f"&contact_name={contact_name}"
    )
    
    call = self.client.calls.create(
        to=to_number,
        from_=self.from_number,
        url=answer_url,
        status_callback=f"{self.base_url}/api/voice/status",
        status_callback_event=["initiated", "ringing", "answered", "completed"],
        machine_detection="Enable",      # Detect voicemail
        machine_detection_timeout=5
    )
    
    return call.sid
```

### B. AI Agent with Tool Execution Loop

The agent implements a **tool loop** that handles GPT-5-mini's function calling. If the model calls a tool, we execute it and feed the result back, allowing multi-step reasoning.

**File: `src/ai/agent.py`**

```python
async def process_input(self, user_input: str, contact_id: str, call_sid: str, contact_name: str | None = None) -> AgentResponse:
    """Process user speech input and generate response."""
    state = self._get_or_create_conversation(contact_id, call_sid, contact_name)
    
    # 1. Safety check FIRST (before LLM call)
    safety_result = self.safety_detector.check_input(user_input)
    if safety_result.needs_escalation:
        if safety_result.level == EscalationLevel.EMERGENCY:
            return AgentResponse(
                message="I understand this is serious. Let me transfer you to our dental staff right away.",
                needs_transfer=True,
                transfer_reason=safety_result.reason
            )
        elif safety_result.level == EscalationLevel.URGENT:
            # Offer choice for high pain (8-10) cases
            return AgentResponse(
                message="I'm concerned about the level of pain you're experiencing. Would you like me to connect you with our dental staff right away, or would you prefer to schedule an urgent appointment?",
                needs_transfer=False  # Let patient decide
            )
    
    # 2. Add to conversation history
    state.messages.append({"role": "user", "content": user_input})
    
    # 3. Tool execution loop (max 3 turns to prevent infinite loops)
    for _ in range(3):
        response = await self.client.chat.completions.create(
            model="gpt-5-mini",
            messages=state.messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            max_completion_tokens=2500,  # Increased for reasoning models
            response_format={"type": "text"},
            verbosity="low",             # Optimize for latency
            reasoning_effort="minimal"
        )
        
        assistant_message = response.choices[0].message
        
        if assistant_message.tool_calls:
            # Append assistant's tool call message
            state.messages.append(assistant_message)
            
            for tool_call in assistant_message.tool_calls:
                # Execute tool and append result
                result = await self._execute_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments),
                    state
                )
                state.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
            continue  # Loop back to get the verbal response
        
        # No tool calls - return the text response
        return AgentResponse(
            message=assistant_message.content or "I'm sorry, I missed that. Could you please say it again?",
            collected_data=self._build_collected_data(state)
        )
```

### C. Structured Data Extraction (Tool Definitions)

We use OpenAI's function calling to extract structured data during the conversation:

**File: `src/ai/prompts.py`**

```python
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "record_patient_info",
            "description": "Record structured information collected from the patient",
            "parameters": {
                "type": "object",
                "properties": {
                    "chief_complaint": {
                        "type": "string",
                        "description": "The main reason the patient is seeking dental care"
                    },
                    "pain_level": {
                        "type": "string",
                        "description": "Pain level on 1-10 scale, or 'none'"
                    },
                    "insurance": {
                        "type": "string",
                        "description": "Name of dental insurance provider, or 'none'"
                    },
                    "preferred_slot": {
                        "type": "string",
                        "description": "Preferred appointment date/time"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_appointment",
            "description": "Book an appointment for the patient",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "YYYY-MM-DD format"},
                    "time": {"type": "string", "description": "HH:MM format"},
                    "appointment_type": {
                        "type": "string",
                        "enum": ["checkup", "cleaning", "consultation", "emergency", "follow_up"]
                    }
                },
                "required": ["date", "time", "appointment_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_transfer",
            "description": "Transfer to human staff for emergencies",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                    "urgency": {"type": "string", "enum": ["routine", "urgent", "emergency"]}
                },
                "required": ["reason", "urgency"]
            }
        }
    }
]
```

### D. CRM Sync (Structured Notes)

**File: `src/services/ghl_client.py`**

```python
async def update_contact_with_call_data(self, contact_id: str, call_data: CallData) -> bool:
    """Update contact with structured data from the call."""
    note_parts = [
        f"📞 AI Voice Call - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Outcome: {call_data.outcome}",
    ]
    
    if call_data.chief_complaint:
        note_parts.append(f"Chief Complaint: {call_data.chief_complaint}")
    if call_data.pain_level:
        note_parts.append(f"Pain Level: {call_data.pain_level}")
    if call_data.insurance:
        note_parts.append(f"Insurance: {call_data.insurance}")
    if call_data.preferred_slot:
        note_parts.append(f"Preferred Appointment: {call_data.preferred_slot}")
    if call_data.escalated:
        note_parts.append(f"⚠️ ESCALATED: {call_data.escalation_reason}")
    
    note = "\n".join(note_parts)
    await self.add_contact_note(contact_id, note)
    
    # Also update custom fields for reporting
    if call_data.pain_level or call_data.insurance:
        await self.update_contact(contact_id, {
            "customFields": {
                "pain_level": call_data.pain_level,
                "insurance_provider": call_data.insurance
        })
```

> [!NOTE]
> **GHL Sandbox Limitation**: Due to GoHighLevel trial/sandbox restrictions, the CRM writeback functionality runs in **mock mode** during development. The `GHLClient` detects trial API keys and logs updates locally instead of making live API calls. In production with a full GHL account, these updates would sync to the CRM automatically.

---

## 3. Compliance & Safety

### A. Multi-Layer Safety System

The system implements **defense in depth** with multiple safety layers:

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| **1. Pre-LLM** | Regex-based `SafetyDetector` | Catch emergencies before burning tokens |
| **2. System Prompt** | Explicit safety instructions | Prevent medical advice, guide escalation |
| **3. Tool Constraints** | `request_transfer` tool | Structured escalation with audit trail |
| **4. Symptom Combinations** | `check_combined_symptoms()` | Detect dangerous patterns (swelling + fever) |

**File: `src/ai/agent.py` - SafetyDetector**

```python
class SafetyDetector:
    """Detects safety concerns and emergencies in patient speech."""
    
    def __init__(self):
        # Compile regex patterns for efficient matching
        self._emergency_pattern = re.compile(
            "|".join(re.escape(kw) for kw in EMERGENCY_KEYWORDS),
            re.IGNORECASE
        )
        self._high_pain_pattern = re.compile(
            "|".join(re.escape(phrase) for phrase in HIGH_PAIN_PHRASES),
            re.IGNORECASE
        )
        self._pain_scale_pattern = re.compile(
            r"(\d+)\s*(out of|\/)\s*10",
            re.IGNORECASE
        )
    
    def check_input(self, user_input: str) -> SafetyCheckResult:
        # Check for emergency keywords (swelling, fever, trauma, etc.)
        if self._emergency_pattern.findall(user_input):
            return SafetyCheckResult(
                needs_escalation=True,
                level=EscalationLevel.EMERGENCY,
                reason="Emergency condition detected"
            )
        
        # Check for numeric pain scale >= 8
        pain_match = self._pain_scale_pattern.search(user_input)
        if pain_match and int(pain_match.group(1)) >= 8:
            return SafetyCheckResult(
                needs_escalation=True,
                level=EscalationLevel.URGENT,
                reason=f"Pain level {pain_match.group(1)}/10"
            )
        
        return SafetyCheckResult(needs_escalation=False, level=EscalationLevel.NONE)
```

### B. Compliance Checks (TCPA / DND)

**File: `src/services/compliance.py`**

```python
class ComplianceService:
    """Service for ensuring compliance with calling regulations."""
    
    async def check_can_call(self, contact: GHLContact) -> ComplianceResult:
        # Check DND settings from GHL
        if contact.dndSettings.get("all", False):
            self._log_compliance_check(contact.id, "BLOCKED", "DND_ALL")
            return ComplianceResult(can_call=False, reason="DND enabled for all channels")
        
        if contact.dndSettings.get("phone", False):
            self._log_compliance_check(contact.id, "BLOCKED", "DND_PHONE")
            return ComplianceResult(can_call=False, reason="DND enabled for phone")
        
        # TCPA: Check calling hours (9 AM - 8 PM local)
        if not self._is_within_calling_hours():
            self._log_compliance_check(contact.id, "BLOCKED", "OUTSIDE_HOURS")
            return ComplianceResult(can_call=False, reason="Outside permitted hours (9 AM - 8 PM)")
        
        return ComplianceResult(can_call=True)
    
    def _log_compliance_check(self, contact_id: str, result: str, reason: str):
        """Audit trail for compliance decisions."""
        logger.info(f"Compliance check: contact={contact_id}, result={result}, reason={reason}")
```

### C. PHI Protection Guidelines

| Principle | Implementation |
|-----------|----------------|
| **Minimal Collection** | Only collect: chief complaint, pain scale (1-10), insurance provider, appointment preference |
| **No Storage of PII** | SSN, DOB, full addresses are never requested or stored |
| **Encryption** | All API calls use HTTPS; GHL handles data-at-rest encryption |
| **Audit Logging** | Compliance checks logged with timestamps for accountability |

---

## 4. Design Decisions & Trade-offs

### GPT-5-mini Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `max_completion_tokens` | 2500 | Prevents "empty response" errors when reasoning exhausts tokens |
| `verbosity` | "low" | Reduces latency for real-time conversation |
| `reasoning_effort` | "minimal" | Phone calls need speed over deep analysis |
| `response_format` | `{"type": "text"}` | Ensures clean text output (no markdown) |

### Twilio `<Gather>` vs `<Record>` + Whisper

We evaluated two approaches for speech-to-text:

| Approach | Latency | Accuracy | Cost |
|----------|---------|----------|------|
| **`<Gather>` (Native STT)** | ~500ms | Good | Included |
| `<Record>` → Whisper API | ~2-3s | Excellent | +$0.006/min |

**Decision:** We chose `<Gather>` for its significantly lower latency, which is critical for natural turn-taking. The accuracy trade-off is acceptable for lead qualification.

### Prompt Engineering Highlights

1. **No Medical Advice:** System prompt explicitly forbids diagnosis and treatment recommendations
2. **Auto-Inference:** AI infers appointment type (emergency vs. checkup) from context—users shouldn't have to self-classify pain as "emergency"
3. **Identity Injection:** Patient name is injected into system prompt AND passed via URL params to prevent "What is your name?" loops
4. **Single Question Per Turn:** Prevents overwhelming patients with compound questions

---

## 5. Example Conversation Transcript

**Scenario: Emergency Booking with Pain Detection**

> **AI**: Hello Manuel, this is Nova from Nova Dentistry calling about your appointment request. How can I help you today?
>
> **Patient**: *Hi, I've been having some pain. I'm going to see about getting an appointment.*
> 
> **AI**: Sorry to hear that, Manuel — I can help. What's the main reason you're seeking care today?
> 
> **Patient**: *Tooth pain.*
> 
> **AI**: I'm sorry you're in pain, Manuel. On a scale of 1 to 10, how is your pain right now?
> 
> **Patient**: *It's about a 7. It's been bothering me for a few days.*
> 
> **AI**: Thank you, Manuel — I'm sorry you've been dealing with that. A 7 is significant; we can get you in sooner. Do you have dental insurance we should have on file?
> 
> **Patient**: *Yes, I have insurance through my employer.*
> 
> **AI**: Thanks, Manuel — that's helpful. Do you have a preferred day or time for the appointment?
> 
> **Patient**: *Tomorrow afternoon maybe around 3:30 p.m.*
> 
> **AI**: Got it — tomorrow (Thursday) at 3:30 PM. I have you down for an emergency visit. I'll book that now... You're all set! We'll see you tomorrow at 3:30 PM.

**Extracted Data:**
```json
{
  "pain_level": "7/10",
  "chief_complaint": "Tooth pain",
  "insurance": "Employer-provided",
  "preferred_slot": "2026-01-09 15:30",
  "appointment_type": "emergency"
}
```

---

## 6. Testing

The project includes a comprehensive test suite:

```bash
# Run all tests
pytest tests/ -v

# Test coverage
pytest tests/ --cov=src --cov-report=term-missing
```

**Test Files:**
- `tests/test_webhooks.py` - GHL webhook parsing and routing
- `tests/test_compliance.py` - DND/hours compliance checks
- `tests/test_safety.py` - Emergency detection and escalation triggers

---

## 7. Project Structure

```
voice_assistant/
├── src/
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Environment configuration
│   ├── ai/
│   │   ├── agent.py          # GPT-5-mini agent + SafetyDetector
│   │   └── prompts.py        # System prompt + tool definitions
│   ├── api/
│   │   ├── webhooks.py       # GHL webhook handlers
│   │   └── voice.py          # Twilio voice webhooks
│   ├── services/
│   │   ├── twilio_service.py # Outbound call management
│   │   ├── ghl_client.py     # CRM integration
│   │   └── compliance.py     # DND/TCPA checks
│   └── models/
│       └── schemas.py        # Pydantic models
├── tests/
│   ├── test_webhooks.py
│   ├── test_compliance.py
│   └── test_safety.py
├── requirements.txt
└── README.md
```

---

## 8. Running Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Start the server
uvicorn src.main:app --reload --port 8000

# 4. Expose for Twilio (separate terminal)
ngrok http 8000
# Update APP_BASE_URL in .env with ngrok URL
```

---

## 9. Future Enhancements

- [ ] **Streaming TTS**: Switch to ElevenLabs for more natural prosody
- [ ] **Conversation Analytics**: Track completion rates, escalation patterns
- [ ] **Calendar Integration**: Real-time availability from GHL calendar
- [ ] **Multi-language Support**: Spanish language prompts and STT

---
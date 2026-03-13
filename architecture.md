# Production Architecture Diagram

This diagram shows the intended full production workflow for the assignment, using the technologies suggested.

## High-Level Architecture

```mermaid
flowchart LR
    A["GHL / GoHighLevel<br/>Lead Capture + CRM"] -->|contact.created webhook| B["Backend API<br/>FastAPI"]

    B --> C["Compliance + Eligibility Layer<br/>DND / DNC / phone validation"]
    C -->|call allowed| D["Voice Orchestrator"]
    C -->|blocked| A

    D --> E["Twilio Programmable Voice<br/>Outbound Call"]
    E --> F["Patient Phone"]

    E -->|audio stream / call events| G["Speech-to-Text<br/>Whisper API or Google STT"]
    G --> H["LLM Orchestrator<br/>GPT-4o"]
    H --> I["Text-to-Speech<br/>Amazon Polly or ElevenLabs"]
    I --> E

    H --> J["Scheduling + Safety Policy Layer<br/>urgent escalation / booking rules"]
    J --> K["Postgres<br/>lead state, transcripts,<br/>call logs, metrics"]
    J -->|qualified result| L["GHL Update Service<br/>notes / stage / appointment"]
    J -->|urgent escalation| M["Human Receptionist / Dentist"]

    L --> A
    M --> A
```

## Call Sequence

```mermaid
sequenceDiagram
    participant GHL as GoHighLevel
    participant API as Backend API
    participant TW as Twilio
    participant STT as Whisper / Google STT
    participant LLM as GPT-4o
    participant TTS as Polly / ElevenLabs
    participant DB as Postgres
    participant HUMAN as Human Receptionist

    GHL->>API: Webhook: contact.created
    API->>API: Validate DND / DNC / callable phone
    API->>DB: Store lead + queued call state

    alt Lead is callable
        API->>TW: Start outbound call
        TW->>STT: Stream caller speech
        STT->>LLM: Transcript text
        LLM->>LLM: Extract reason, pain, insurance, preferred slot
        LLM->>TTS: Next assistant response text
        TTS->>TW: Spoken audio
        LLM->>API: Structured result + safety flags
        API->>DB: Persist turn + update lead state

        alt Urgent symptoms or escalation needed
            API->>HUMAN: Transfer / handoff
            API->>GHL: Write urgent note + stage update
        else Qualified for scheduling
            API->>GHL: Write notes / stage / appointment details
        end
    else Lead blocked
        API->>GHL: Write blocked / opted-out status
    end
```

## Component Notes

- `GoHighLevel`: source of truth for inbound leads and final CRM updates.
- `Backend API (FastAPI)`: receives webhooks, enforces compliance, orchestrates the call, stores state, and writes back to GHL.
- `Twilio`: places the outbound call and handles the telephony session.
- `STT`: converts caller speech into text for the language model.
- `GPT-4o`: manages dialogue, structured extraction, and tool-calling style decisions.
- `TTS`: turns assistant responses into spoken audio for the live call.
- `Postgres`: stores lead records, call attempts, transcripts, structured outputs, and audit data.
- `Human handoff`: receives urgent or unsafe calls immediately when the AI should stop.

## Related Notes

- See [compliance.md](/home/josh/Desktop/Application/interview/compliance.md) for DND / DNC handling, PHI minimization, encryption expectations, and escalation rules.

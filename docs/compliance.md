# Compliance Notes

This system handles outbound calls to dental patients and processes limited health-related
information. Three compliance frameworks apply.

---

## 1. HIPAA — Health Insurance Portability and Accountability Act

HIPAA is the primary federal law governing patient health data in a dental practice.
The AI voice pipeline qualifies as a **Business Associate** under HIPAA because it
processes PHI on behalf of a Covered Entity (the dental clinic).

### Minimum Necessary Standard
Only three fields are collected and stored:

| Field | Why collected |
|-------|---------------|
| `pain_level` | Assess urgency; determines escalation threshold |
| `insurance_provider` | Required for appointment booking |
| `preferred_slot` | Required for appointment booking |

No SSN, DOB, diagnosis codes, medication names, or dental records are collected.

### PHI Protection in Transit
- All HTTP traffic uses TLS (enforced by Twilio and Express behind HTTPS termination).
- Twilio Media Streams use TLS WebSocket (`wss://`).
- OpenAI and ElevenLabs APIs are HTTPS-only.

### PHI Protection at Rest
- Postgres uses the `pgcrypto` extension (enabled in migration `1720000000000`).
- `phone` and `email` columns should use column-level encryption in production
  (e.g., `pgp_sym_encrypt` / `pgp_sym_decrypt` with a KMS-managed key).
- Collected fields (pain_level, insurance, slot) stored in `collected_fields` table
  with no patient identifiers in the row itself — linked only via `call_log_id`.

### Application Logs
PHI never appears in application logs:
- Phone numbers are truncated to last 4 digits in all log statements.
- `firstName` and `email` are never logged.

### Audit Trail
Every call session creates a `call_logs` row with `started_at`, `ended_at`, and `status`.
Every transcript turn is timestamped. Every collected field has `collected_at`.

### Business Associate Agreements (BAAs)
The following vendors process PHI and **must have signed BAAs before production use**:

| Vendor | PHI Involved |
|--------|-------------|
| **Twilio** | Carries patient audio; stores call recordings if enabled |
| **OpenAI** | Receives audio (Whisper) and transcript text (GPT-4o) |
| **ElevenLabs** | Receives assistant reply text |
| **GoHighLevel** | Stores contact data, notes, appointments |

> Twilio and GHL offer HIPAA BAAs on enterprise plans. OpenAI's API has a BAA available
> under its Enterprise agreements. Verify ElevenLabs' current BAA availability before
> production deployment.

### Right to Access / Delete
Cascade deletes are configured on the `leads` table — deleting a lead removes all
associated `lead_dnc`, `call_logs`, `call_escalations`, `transcripts`, and
`collected_fields` records.

---

## 2. TCPA — Telephone Consumer Protection Act

TCPA governs automated outbound calls to consumers in the United States.

### Prior Express Consent
The lead must have provided **prior express written consent** to receive automated calls
before a GHL `contact.created` event triggers this pipeline. This consent must be
captured at the opt-in form level in GHL (e.g., web form checkbox with disclosure text).

### DNC / DND Check
Implemented in `src/infrastructure/http/middleware/dncCheck.ts` and
`src/application/usecases/HandleInboundLeadUseCase.ts`:

1. GHL contact's `dndSettings.Call.status` is checked via `GHLGateway.getContact()`.
2. Internal `lead_dnc.is_dnc` flag is checked in `LeadRepository.getDncStatus()`.
3. If either flag is set, the call is blocked and a `200 skipped` response is returned
   (GHL must not retry DNC rejections).

### Call Time Restrictions
TCPA prohibits calls before **8:00 AM** or after **9:00 PM** in the called party's
**local timezone**. The current implementation uses UTC as a safe fallback.

> **Production note:** Derive the lead's timezone from the phone area code (e.g., using
> `libphonenumber-js`) or from a custom GHL field populated at opt-in.

### Required Disclosures
The Nova system prompt (Fabric `OUTPUT INSTRUCTIONS`) requires the AI to open every call:

> *"This call may be recorded for quality and training purposes. I'm an automated
> assistant and I'm not able to provide medical advice."*

### Opt-Out (DTMF digit 9)
> **Implementation note:** Wire Twilio's `<Gather digits="1">` to catch DTMF digit 9.
> On receipt: call `LeadRepository.setDnc(leadId, 'opted_out')` and
> `GHLGateway.setDnd(contactId, true)`. This immediately stops future calls.

### Two-Party Consent States
Several US states require **all parties** to consent to call recording:
CA, IL, WA, FL, PA, MD, NH, MA, CT, MI (and others). The call opening disclosure
covers this requirement when calls may be recorded.

---

## 3. OSHA — Occupational Safety and Health Administration

OSHA governs **physical workplace safety** for dental clinic staff. It does not directly
regulate AI voice systems, but it affects how staff respond when the AI escalates a call.

### Escalation Red Flags (AI → Human)
The AI calls `escalate_to_human` immediately when any of the following are detected:

| Trigger | Example patient statement |
|---------|--------------------------|
| Pain score ≥ 8/10 | *"It's about a 9, I can barely sleep"* |
| Swelling + fever | *"My cheek is really swollen and I have a fever"* |
| Trauma / injury | *"I fell and knocked out a tooth"* |
| Severe trismus | *"I can't open my mouth"* |
| Allergic reaction | *"I think I'm having a reaction to medication"* |
| Patient request | *"Can I speak to a real person?"* |
| Turn limit exceeded | More than 10 turns without completing intake |

### Staff Protocol on Escalation
When the AI transfers to a human team member, the following OSHA-aligned protocols apply:

1. **Never leave the patient on hold** — receptionist must pick up immediately.
2. **Dental emergency SOP** — if pain ≥ 8, swelling, or trauma: follow the clinic's
   emergency triage protocol; assess whether emergency department referral is needed.
3. **Workplace incident logging** — if a patient discloses workplace injury or accident,
   document per OSHA 300 log requirements if the incident is work-related.
4. **Mental health distress** — if a patient expresses distress beyond dental pain,
   follow the clinic's patient safety and duty-of-care procedures.

### What the AI Never Does
- Provides clinical advice, diagnosis, or treatment recommendations.
- Leaves a distressed or high-pain patient without an immediate human handoff.
- Stores or transmits more PHI than the three required fields.

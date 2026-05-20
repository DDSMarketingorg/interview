# Example Conversations

---

## Transcript 1 — Happy Path (All Fields Collected, Appointment Booked)

**Call context:** Sarah Chen, new lead from GHL web form. Pain 4/10, Sun Life insurance.

---

**Nova (AI):**
Hi, am I speaking with Sarah?

**Sarah:**
Yes, that's me.

**Nova:**
Hi Sarah, this is Nova calling from Nova Dental Clinic about your appointment request.
Just a quick heads-up — this call may be recorded for quality and training purposes,
and I'm an automated assistant so I'm not able to give medical advice.
Can I ask what's been bothering you and roughly how much discomfort you're in on a scale
of 1 to 10?

> 🔧 *[No tool call yet — waiting for pain level]*

**Sarah:**
Yeah, I've got this aching in my upper left molar. I'd say it's about a 4 out of 10.
It comes and goes.

> 🔧 **Tool call:** `collect_pain_info({ pain_level: "4/10", location: "upper left molar", duration: "comes and goes" })`
> → Saved to `collected_fields` (field: pain_level, value: "4/10")

**Nova:**
Got it — a 4 out of 10, upper left area, and it's intermittent. Thanks for letting me know.
Do you have dental insurance we should know about, or will you be paying out of pocket?

**Sarah:**
I have Sun Life.

> 🔧 **Tool call:** `collect_insurance({ provider: "Sun Life" })`
> → Saved to `collected_fields` (field: insurance_provider, value: "Sun Life")

**Nova:**
Perfect, Sun Life — we work with them. And do you have a preferred day or time for
your appointment? We have openings this week and next.

**Sarah:**
Maybe Thursday the 7th around 3:30 in the afternoon?

> 🔧 **Tool call:** `collect_appointment_preference({ preferred_date: "2025-09-07", preferred_time: "15:30" })`
> → Saved to `collected_fields` (field: preferred_slot, value: "2025-09-07 15:30")

**Nova:**
Thursday September 7th at 3:30 PM — noted! Someone from our team will reach out to
confirm that slot. Is there anything else I can help with before we go?

**Sarah:**
No, that's all. Thanks!

**Nova:**
Wonderful, have a great day Sarah. We'll be in touch soon!

> 🔧 **Tool call:** `end_conversation({ outcome: "qualified" })`

---

**Post-call GHL updates:**

- Note created:
  ```
  AI Voice Intake — 2025-09-05T18:42:00Z
  Outcome: qualified
  Pain level: 4/10
  Insurance: Sun Life
  Preferred slot: 2025-09-07 15:30
  ```
- Contact stage updated: `Qualified`
- Appointment created: September 7, 2025 at 15:30

---

## Transcript 2 — Emergency Escalation (Pain 9/10 + Swelling)

**Call context:** Marcus Reid, new lead. Reports severe pain and facial swelling.

---

**Nova (AI):**
Hi, is this Marcus?

**Marcus:**
Yeah.

**Nova:**
Hi Marcus, this is Nova from Nova Dental Clinic — we received your appointment request.
Quick note: this call may be recorded, and I'm an automated assistant so I can't give
medical advice. Can you tell me what's going on and how much pain you're in right now,
on a scale of 1 to 10?

**Marcus:**
It's really bad. Maybe a 9. My whole left cheek is swollen and I've had a fever since
yesterday. I can barely open my mouth.

> 🔧 **Tool call:** `collect_pain_info({ pain_level: "9/10", location: "left cheek", duration: "since yesterday" })`
> → Saved to `collected_fields`

> ⚠️ **Escalation triggered:** Pain ≥ 8/10 AND emergency keywords detected (swelling, fever, trismus)

> 🔧 **Tool call:** `escalate_to_human({ reason: "pain_score_9_swelling_fever_trismus" })`
> → Saved to `call_escalations` (reason: "pain_score_9_swelling_fever_trismus")

**Nova:**
Marcus, based on what you're describing — the level of pain, swelling, and fever —
I want to make sure you get immediate attention. I'm connecting you with a team member
right now. Please stay on the line.

> 🔧 **Tool call:** `end_conversation({ outcome: "escalated" })`

---

**What happens next (human handoff):**
- Twilio transfers to the clinic's reception queue.
- Receptionist receives alert: *"Escalated call — pain 9/10, swelling, fever, trismus"*
- Receptionist assesses urgency: swelling + fever + trismus = possible dental abscess.
- Patient is offered same-day emergency slot or directed to nearest emergency dental
  clinic / ER per the clinic's OSHA emergency protocol.

---

**Post-call GHL updates:**

- Note created:
  ```
  AI Voice Intake — 2025-09-05T14:10:00Z
  Outcome: escalated
  Pain level: 9/10
  ⚠️ Escalated to human — review required
  ```
- Contact stage updated: `Escalated`
- No appointment created (escalated calls require human follow-up)

---

## Structured Data Captured (both calls)

```json
// Transcript 1 — Sarah (collected_fields rows)
[
  { "field_name": "pain_level",          "field_value": "4/10" },
  { "field_name": "insurance_provider",  "field_value": "Sun Life" },
  { "field_name": "preferred_slot",      "field_value": "2025-09-07 15:30" }
]

// Transcript 2 — Marcus (collected_fields + call_escalations)
[
  { "field_name": "pain_level",          "field_value": "9/10" }
]
// call_escalations row:
{ "reason": "pain_score_9_swelling_fever_trismus", "escalated_at": "2025-09-05T14:10:05Z" }
```

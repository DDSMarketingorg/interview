# AI Voice Assistant – Interview Assignment

## 📌 Project Overview
Design a mini system for a **dental marketing AI voice assistant** that integrates with **GoHighLevel (GHL)**.  
The system should:  
1. Receive new leads from GHL (via webhook).  
2. Initiate an outbound call using Twilio (or another voice API).  
3. Use AI (STT + LLM + TTS) to qualify the lead and collect structured info.  
4. Update the lead’s status back in GHL (notes, stage, or appointment).

---

## 🎯 Objectives
- Show **system architecture** and data flow.  
- Provide **code snippets** for key interactions.  
- Demonstrate **compliance awareness** (DNC, PHI, escalation).  

---

## 🛠 Requirements

### 1. Architecture
- Diagram or clear explanation of the flow:  
  `GHL Webhook → Backend → Voice Provider → AI Pipeline → GHL Update`

### 2. Code Examples
Provide working or pseudocode for:  
- Handling a **GHL webhook** (new lead).  
- Initiating a **Twilio outbound call**.  
- LLM prompt design to capture structured data like:  
  ```json
  {
    "pain_level": "7/10",
    "insurance": "Sun Life",
    "preferred_slot": "2025-09-07 15:30"
  }
- 	•	Writing results back to GHL (appointment or note)
- 	### 3. Compliance
When designing a system that handles patient calls, compliance and safety are critical. In your solution, explain how you would address:  

- **Do Not Disturb (DND) / Do Not Call (DNC)**  
  - Respect the flags from GHL to avoid calling leads who opted out.  

- **Protected Health Information (PHI)**  
  - Collect only minimal data necessary for appointment booking (chief complaint, pain scale, insurance provider).  
  - Avoid storing sensitive information beyond what is needed.  
  - Ensure all stored data is encrypted at rest and in transit.  

- **Escalation & Safety**  
  - Define red-flag conditions (e.g., severe pain 8–10, swelling + fever, trauma, allergies).  
  - In such cases, the AI should **immediately transfer** to a human receptionist or dentist.  
  - Clearly state that the AI cannot provide clinical advice.  

---

## 📂 Deliverables
- A **short document (3–4 pages)** or a **GitHub repo** containing:  
  - Architecture diagram (flow from GHL → AI voice pipeline → GHL update).  
  - Code snippets (Node.js, Python, or your preferred language).  
  - Notes on compliance and design decisions.  
  - (Optional) Example conversations/transcripts showing how the AI responds.  

---

## ⚙️ Suggested Tech Stack
- **Voice Layer**: Twilio Programmable Voice (or SignalWire)  
- **Speech-to-Text (STT)**: Whisper API or Google Cloud Speech-to-Text  
- **Language Model (LLM)**: GPT-4o (or similar) for dialogue + tool calling  
- **Text-to-Speech (TTS)**: Amazon Polly or ElevenLabs  
- **Backend**: Node.js (Express) or Python (FastAPI) for handling webhooks and call logic  
- **Database (optional)**: Postgres (to store call logs, transcripts, and metrics)  

---

## 📅 Submission
- Submit your solution either as:  
  1. A **GitHub repo link**, or  
  2. A **PDF/Markdown doc** with architecture, code snippets, and explanations.  

- **Deadline:** 3 days after receiving this assignment.  

---

## 🔖 Reference Payloads

### Example GHL Webhook (New Lead)
```json
{
  "event": "contact.created",
  "contact": {
    "id": "CNT_xxx",
    "firstName": "Sarah",
    "phone": "+1416xxxxxxx",
    "email": "sarah@example.com"
  }
}
### Example Twilio Outbound Call (Node.js)
```js
import twilio from "twilio";

const client = twilio(
  process.env.TWILIO_ACCOUNT_SID,
  process.env.TWILIO_AUTH_TOKEN
);

async function makeCall(toNumber, greeting) {
  try {
    const call = await client.calls.create({
      to: toNumber,
      from: process.env.TWILIO_NUMBER,
      twiml: `<Response>
                <Say voice="alice">${greeting}</Say>
                <Pause length="5"/>
                <Say voice="alice">Thank you. Goodbye.</Say>
              </Response>`
    });

    console.log(`Call initiated. SID: ${call.sid}`);
    return call.sid;
  } catch (err) {
    console.error("Error initiating call:", err);
    throw err;
  }
}

// Example usage
makeCall("+1416xxxxxxx", "Hello Sarah, this is Nova Dentistry calling about your appointment request.");

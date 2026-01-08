# =============================================================================
# System Prompt - Defines the AI's persona and capabilities
# =============================================================================

SYSTEM_PROMPT = """You are Nova, a friendly and professional AI assistant for Nova Dentistry. You are calling to help qualify new patients and schedule appointments.

## Your Role
- Qualify leads by collecting essential information
- Schedule dental appointments
- Provide general office information
- Transfer to human staff when necessary

## MANDATORY Qualification Steps (Ask in order)
1. **Chief Complaint**: Why they're seeking dental care
2. **Pain Level**: YOU MUST ASK: "On a scale of 1 to 10, how is your pain?" (Skip for routine cleanings)
3. **Insurance Provider**: YOU MUST ASK: "Do you have dental insurance we should have on file?"
4. **Preferred Appointment Time**: Only AFTER getting the above info.

## Conversation Guidelines
- Be warm, empathetic, and conversational
- Use the patient's name when appropriate
- Keep responses concise (suitable for phone conversation)
- Ask ONE question at a time
- Acknowledge patient concerns before moving forward
- If they mention pain, show empathy first
- **DO NOT** ask for specific medical details (e.g., "which tooth", "upper or lower"). "Tooth pain" is sufficient.
- Accept general answers and move forward.
- **Infer appointment type** from context:
  - Pain/Trauma -> 'emergency'
  - Routine/Checkup -> 'checkup' or 'cleaning'
  - Otherwise -> 'consultation'
- **DO NOT** ask the user to choose "emergency vs consultation". Just book it.

## CRITICAL SAFETY RULES - ALWAYS FOLLOW
1. **Never provide medical advice** - You are not a dentist
2. **Severe Pain (8-10)**: Immediately offer to transfer to staff
3. **Emergency Signs**: Transfer immediately for:
   - Swelling with fever
   - Facial trauma or injury
   - Difficulty breathing or swallowing
   - Uncontrolled bleeding
   - Allergic reactions
4. **Uncertainty**: When in doubt, offer to transfer to a human

## What You CANNOT Do
- Diagnose conditions
- Recommend treatments or medications
- Provide pricing for specific procedures
- Access or modify patient medical records
- Guarantee appointment times (only suggest available slots)

## Ending the Call
- Summarize what was discussed
- **VERBALLY CONFIRM** the specific date and time of the appointment
- Thank them for calling Nova Dentistry
- Mention they'll receive a confirmation text/email
- If the user indicates they are done (e.g., "bye", "no questions"), YOU MUST call the `end_conversation` tool.
- When calling `end_conversation`, set the message to a simple closing statement like "Have a great day." or "Goodbye." DO NOT ask "Is there anything else?"

Always maintain a helpful, caring tone while being efficient with the caller's time."""


# =============================================================================
# Tool Definitions - For structured data extraction
# =============================================================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "record_patient_info",
            "description": "Record structured information collected from the patient during the call",
            "parameters": {
                "type": "object",
                "properties": {
                    "chief_complaint": {
                        "type": "string",
                        "description": "The main reason the patient is seeking dental care"
                    },
                    "pain_level": {
                        "type": "string",
                        "description": "Pain level on 1-10 scale, or 'none' if no pain"
                    },
                    "insurance": {
                        "type": "string",
                        "description": "Name of dental insurance provider, or 'none' if uninsured"
                    },
                    "preferred_slot": {
                        "type": "string",
                        "description": "Preferred appointment date/time in ISO format or natural language"
                    }
                },
                "required": []
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
                    "date": {
                        "type": "string",
                        "description": "Appointment date in YYYY-MM-DD format"
                    },
                    "time": {
                        "type": "string",
                        "description": "Appointment time in HH:MM format"
                    },
                    "appointment_type": {
                        "type": "string",
                        "enum": ["checkup", "cleaning", "consultation", "emergency", "follow_up"],
                        "description": "Type of appointment"
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
            "description": "Request transfer to human staff for emergencies or complex situations",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Reason for the transfer request"
                    },
                    "urgency": {
                        "type": "string",
                        "enum": ["routine", "urgent", "emergency"],
                        "description": "Urgency level of the transfer"
                    }
                },
                "required": ["reason", "urgency"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "end_conversation",
            "description": "End the conversation when the call is complete",
            "parameters": {
                "type": "object",
                "properties": {
                    "outcome": {
                        "type": "string",
                        "enum": ["appointment_booked", "callback_requested", "transferred", "no_appointment", "voicemail"],
                        "description": "Outcome of the call"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Brief summary of what was discussed"
                    }
                },
                "required": ["outcome", "summary"]
            }
        }
    }
]

# =============================================================================
# Safety Detection Keywords
# =============================================================================

EMERGENCY_KEYWORDS = [
    "can't breathe",
    "difficulty breathing",
    "swelling",
    "fever",
    "trauma",
    "accident",
    "bleeding won't stop",
    "allergic reaction",
    "face is swollen",
    "can't swallow",
    "knocked out tooth",
    "broken jaw"
]

HIGH_PAIN_PHRASES = [
    "10 out of 10",
    "worst pain",
    "unbearable",
    "can't take it",
    "excruciating",
    "9 out of 10",
    "8 out of 10"
]

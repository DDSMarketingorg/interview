import openai
import boto3
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import re

from ..models.models import (
    QualificationData, ConversationTurn, PainLevel,
    UrgencyLevel, CallSession, CallStatus
)

logger = logging.getLogger(__name__)


class AIService:
    """AI conversation pipeline with speech processing and LLM integration"""

    def __init__(self, openai_api_key: str, aws_access_key: str,
                 aws_secret_key: str, aws_region: str = "us-east-1"):
        # Initialize OpenAI client (modern v1+ API)
        self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)

        # Initialize AWS Polly for TTS
        self.polly_client = boto3.client(
            'polly',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )

        # Conversation state management
        self.active_sessions: Dict[str, Dict] = {}

        # System prompt for dental lead qualification
        self.system_prompt = """
You are Nova, an AI assistant for Premier Dental. Your role is to qualify dental leads through natural, empathetic conversation.

OBJECTIVES:
1. Collect essential qualification data: chief complaint, pain level, urgency, insurance, preferred appointment time
2. Maintain a warm, professional tone
3. Identify emergency conditions requiring immediate escalation
4. Respect patient privacy and collect only necessary information

EMERGENCY ESCALATION CONDITIONS:
- Pain level 9-10/10
- Mention of: severe swelling with fever, trauma/injury, uncontrolled bleeding, allergic reactions
- Any indication of life-threatening emergency

CONVERSATION GUIDELINES:
- Keep responses under 25 words when possible
- Ask one question at a time
- Use empathetic language for pain/discomfort
- Confirm understanding before proceeding
- Offer immediate escalation for emergencies

PRIVACY COMPLIANCE:
- Only collect information necessary for appointment scheduling
- Avoid asking for detailed medical history
- Don't provide medical advice or diagnosis
- Clearly state you're an AI assistant

Remember: Your goal is qualification and scheduling, not medical consultation.
"""

    async def generate_first_question(self, lead_id: str) -> str:
        """Generate the first qualification question"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": "Start the dental qualification conversation. Ask about their dental concern."}
                ],
                max_tokens=100,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating first question: {e}")
            return "What brings you to Premier Dental today? Are you experiencing any dental pain or discomfort?"

    async def process_conversation_turn(self, lead_id: str, user_speech: str,
                                        call_sid: str) -> Dict[str, Any]:
        """Process a conversation turn and generate appropriate response"""
        try:
            # Get or create session context
            session_context = self.active_sessions.get(lead_id, {
                "conversation_history": [],
                "qualification_data": QualificationData(),
                "turn_count": 0
            })

            # Add user input to conversation history
            user_turn = ConversationTurn(
                speaker="user",
                message=user_speech,
                confidence_score=0.95
            )
            session_context["conversation_history"].append(user_turn)
            session_context["turn_count"] += 1

            # Analyze user input for qualification data
            extracted_data = await self._extract_qualification_data(
                user_speech,
                session_context["qualification_data"]
            )
            session_context["qualification_data"] = extracted_data

            # Check for escalation conditions
            escalation_check = self._check_escalation_conditions(
                user_speech,
                extracted_data
            )

            if escalation_check["escalate"]:
                return {
                    "escalate": True,
                    "escalation_reason": escalation_check["reason"],
                    "response": escalation_check["message"]
                }

            # Generate AI response
            ai_response = await self._generate_ai_response(
                session_context["conversation_history"],
                session_context["qualification_data"],
                session_context["turn_count"]
            )

            # Add AI response to history
            ai_turn = ConversationTurn(
                speaker="assistant",
                message=ai_response["message"]
            )
            session_context["conversation_history"].append(ai_turn)

            # Update session
            self.active_sessions[lead_id] = session_context

            # Check if conversation is complete
            if ai_response.get("complete", False):
                return {
                    "complete": True,
                    "response": ai_response["message"],
                    "qualification_data": session_context["qualification_data"].dict(),
                    "appointment_scheduled": ai_response.get("appointment_scheduled", False)
                }

            return {
                "response": ai_response["message"],
                "qualification_data": session_context["qualification_data"].dict()
            }

        except Exception as e:
            logger.error(f"Error processing conversation turn: {e}")
            return {
                "escalate": True,
                "escalation_reason": "technical_error",
                "response": "I'm experiencing technical difficulties. Let me connect you with a team member."
            }

    async def _extract_qualification_data(self, user_input: str,
                                          current_data: QualificationData) -> QualificationData:
        """Extract and update qualification data from user input"""
        try:
            # Use LLM to extract structured data
            extraction_prompt = f"""
Extract dental qualification information from this patient response: "{user_input}"

Current data: {current_data.json()}

Extract and return JSON with any mentioned:
- chief_complaint: main dental issue/concern
- pain_level: scale 0-10 or descriptive (none/mild/moderate/severe/emergency)
- insurance_provider: dental insurance company name
- preferred_appointment_time: mentioned timeframe/preference
- emergency_indicators: any urgent symptoms mentioned

Only include fields that are explicitly mentioned. Return valid JSON.
"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant. Return only valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )

            extracted = json.loads(response.choices[0].message.content)

            # Update current data with extracted information
            for key, value in extracted.items():
                if value and hasattr(current_data, key):
                    if key == "pain_level":
                        current_data.pain_level = self._normalize_pain_level(
                            value)
                    else:
                        setattr(current_data, key, value)

            # Update urgency based on pain level and other factors
            current_data.urgency = self._calculate_urgency(current_data)

            return current_data

        except Exception as e:
            logger.error(f"Error extracting qualification data: {e}")
            return current_data

    def _normalize_pain_level(self, pain_input: str) -> Optional[PainLevel]:
        """Normalize pain level input to standard scale"""
        pain_str = str(pain_input).lower()

        # Direct number matches
        if any(num in pain_str for num in ['9', '10']):
            return PainLevel.EMERGENCY
        elif any(num in pain_str for num in ['7', '8']):
            return PainLevel.SEVERE
        elif any(num in pain_str for num in ['4', '5', '6']):
            return PainLevel.MODERATE
        elif any(num in pain_str for num in ['1', '2', '3']):
            return PainLevel.MILD
        elif '0' in pain_str or 'no pain' in pain_str:
            return PainLevel.NONE

        # Descriptive matches
        if any(word in pain_str for word in ['excruciating', 'unbearable', 'severe']):
            return PainLevel.SEVERE
        elif any(word in pain_str for word in ['moderate', 'strong', 'significant']):
            return PainLevel.MODERATE
        elif any(word in pain_str for word in ['mild', 'slight', 'minor']):
            return PainLevel.MILD
        elif any(word in pain_str for word in ['none', 'no', 'nothing']):
            return PainLevel.NONE

        return None

    def _calculate_urgency(self, data: QualificationData) -> UrgencyLevel:
        """Calculate urgency level based on qualification data"""
        if data.pain_level == PainLevel.EMERGENCY:
            return UrgencyLevel.EMERGENCY
        elif data.pain_level == PainLevel.SEVERE:
            return UrgencyLevel.HIGH
        elif data.pain_level == PainLevel.MODERATE:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW

    def _check_escalation_conditions(self, user_input: str,
                                     qualification_data: QualificationData) -> Dict[str, Any]:
        """Check if immediate escalation is required"""
        user_lower = user_input.lower()

        # Emergency pain levels
        if qualification_data.pain_level == PainLevel.EMERGENCY:
            return {
                "escalate": True,
                "reason": "severe_pain",
                "message": "I understand you're in severe pain. Let me connect you immediately with our emergency dental line."
            }

        # Emergency keywords
        emergency_keywords = [
            "can't breathe", "difficulty breathing", "swelling in throat",
            "severe bleeding", "won't stop bleeding", "facial swelling",
            "fever", "infection", "abscess", "trauma", "accident",
            "knocked out", "allergic reaction"
        ]

        for keyword in emergency_keywords:
            if keyword in user_lower:
                return {
                    "escalate": True,
                    "reason": "emergency_condition",
                    "message": f"This sounds like it needs immediate attention. I'm connecting you with our emergency dental team right now."
                }

        return {"escalate": False}

    async def _generate_ai_response(self, conversation_history: List[ConversationTurn],
                                    qualification_data: QualificationData,
                                    turn_count: int) -> Dict[str, Any]:
        """Generate appropriate AI response based on conversation context"""
        try:
            # Build conversation context
            conversation_text = "\n".join([
                # Last 6 turns
                f"{turn.speaker}: {turn.message}" for turn in conversation_history[-6:]
            ])

            # Determine conversation stage and next action
            missing_data = self._identify_missing_data(qualification_data)

            if turn_count >= 10 or not missing_data:
                # Conversation should conclude
                if qualification_data.chief_complaint and qualification_data.pain_level:
                    return {
                        "message": "Thank you for all that information. Based on what you've shared, I'd like to schedule you for an appointment. Let me connect you with our scheduling team.",
                        "complete": True,
                        "appointment_scheduled": True
                    }
                else:
                    return {
                        "message": "Thank you for your time. I'll have one of our team members follow up with you to discuss your dental needs in more detail.",
                        "complete": True,
                        "appointment_scheduled": False
                    }

            # Generate next question based on missing data
            next_question_prompt = f"""
Based on this conversation and missing data {missing_data}, generate the next appropriate question.

Conversation so far:
{conversation_text}

Current qualification data: {qualification_data.json()}

Generate a natural, empathetic follow-up question (under 25 words) to gather the most important missing information. Focus on the highest priority missing data first.
"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": next_question_prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )

            return {
                "message": response.choices[0].message.content.strip(),
                "complete": False
            }

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return {
                "message": "Let me connect you with one of our team members who can better assist you.",
                "complete": True,
                "appointment_scheduled": False
            }

    def _identify_missing_data(self, qualification_data: QualificationData) -> List[str]:
        """Identify what qualification data is still missing"""
        missing = []

        if not qualification_data.chief_complaint:
            missing.append("chief_complaint")
        if not qualification_data.pain_level:
            missing.append("pain_level")
        if not qualification_data.insurance_provider:
            missing.append("insurance_provider")
        if not qualification_data.preferred_appointment_time:
            missing.append("preferred_appointment_time")

        return missing

    async def cleanup_session(self, lead_id: str):
        """Clean up session data after call completion"""
        if lead_id in self.active_sessions:
            del self.active_sessions[lead_id]

    async def get_session_summary(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of the conversation session"""
        session = self.active_sessions.get(lead_id)
        if not session:
            return None

        return {
            "qualification_data": session["qualification_data"].dict(),
            "conversation_length": len(session["conversation_history"]),
            "turn_count": session["turn_count"]
        }

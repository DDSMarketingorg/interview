import json
import logging
import re
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from openai import AsyncOpenAI

from src.config import get_settings
from src.ai.prompts import SYSTEM_PROMPT, TOOL_DEFINITIONS, EMERGENCY_KEYWORDS, HIGH_PAIN_PHRASES
from src.services.ghl_client import CallData

logger = logging.getLogger(__name__)


# =============================================================================
# Safety Detection Classes (merged from safety.py)
# =============================================================================

class EscalationLevel(str, Enum):
    """Urgency levels for escalation."""
    NONE = "none"
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class SafetyCheckResult(BaseModel):
    """Result of a safety check on patient input."""
    needs_escalation: bool
    level: EscalationLevel
    reason: str | None = None
    detected_keywords: list[str] = []


class SafetyDetector:
    """
    Detects safety concerns and emergency situations in patient speech.
    
    Triggers:
    - High pain levels (8-10)
    - Emergency symptoms (swelling + fever, trauma, breathing issues)
    - Allergic reactions
    - Direct requests to speak with a human
    """
    
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
        self._transfer_request_pattern = re.compile(
            r"(speak|talk|transfer).*(human|person|someone|staff|dentist|doctor|real)",
            re.IGNORECASE
        )
        self._pain_scale_pattern = re.compile(
            r"(\d+)\s*(out of|\/)\s*10",
            re.IGNORECASE
        )
    
    def check_input(self, user_input: str) -> SafetyCheckResult:
        """
        Check user input for safety concerns.
        
        Args:
            user_input: Transcribed speech from patient
        
        Returns:
            SafetyCheckResult with escalation status
        """
        detected_keywords = []
        
        # Check for emergency keywords
        emergency_matches = self._emergency_pattern.findall(user_input)
        if emergency_matches:
            detected_keywords.extend(emergency_matches)
            logger.warning(f"Emergency keywords detected: {emergency_matches}")
            return SafetyCheckResult(
                needs_escalation=True,
                level=EscalationLevel.EMERGENCY,
                reason=f"Emergency condition detected: {', '.join(emergency_matches)}",
                detected_keywords=detected_keywords
            )
        
        # Check for high pain phrases
        high_pain_matches = self._high_pain_pattern.findall(user_input)
        if high_pain_matches:
            detected_keywords.extend(high_pain_matches)
            logger.warning(f"High pain detected: {high_pain_matches}")
            return SafetyCheckResult(
                needs_escalation=True,
                level=EscalationLevel.URGENT,
                reason=f"High pain level reported: {', '.join(high_pain_matches)}",
                detected_keywords=detected_keywords
            )
        
        # Check for numeric pain scale
        pain_match = self._pain_scale_pattern.search(user_input)
        if pain_match:
            pain_level = int(pain_match.group(1))
            if pain_level >= 8:
                logger.warning(f"High pain score detected: {pain_level}/10")
                return SafetyCheckResult(
                    needs_escalation=True,
                    level=EscalationLevel.URGENT,
                    reason=f"Pain level {pain_level}/10 - requires immediate attention",
                    detected_keywords=[f"{pain_level}/10"]
                )
        
        # Check for explicit transfer requests
        if self._transfer_request_pattern.search(user_input):
            logger.info("Patient requested human transfer")
            return SafetyCheckResult(
                needs_escalation=True,
                level=EscalationLevel.ROUTINE,
                reason="Patient requested to speak with a human",
                detected_keywords=["transfer request"]
            )
        
        # No safety concerns detected
        return SafetyCheckResult(
            needs_escalation=False,
            level=EscalationLevel.NONE
        )
    
    def check_combined_symptoms(
        self,
        symptoms: list[str]
    ) -> SafetyCheckResult:
        """
        Check for dangerous symptom combinations.
        
        Certain combinations require immediate escalation:
        - Swelling + Fever
        - Bleeding + Pain > 8
        - Any mention of difficulty breathing
        
        Args:
            symptoms: List of reported symptoms
        
        Returns:
            SafetyCheckResult with escalation status
        """
        symptom_text = " ".join(symptoms).lower()
        
        # Swelling + Fever combination
        if "swelling" in symptom_text and "fever" in symptom_text:
            return SafetyCheckResult(
                needs_escalation=True,
                level=EscalationLevel.EMERGENCY,
                reason="Potential dental infection: swelling with fever",
                detected_keywords=["swelling", "fever"]
            )
        
        # Breathing issues - always emergency
        if any(term in symptom_text for term in ["breathing", "breathe", "swallow"]):
            return SafetyCheckResult(
                needs_escalation=True,
                level=EscalationLevel.EMERGENCY,
                reason="Potential airway compromise",
                detected_keywords=["breathing difficulty"]
            )
        
        return SafetyCheckResult(
            needs_escalation=False,
            level=EscalationLevel.NONE
        )


# =============================================================================
# Agent Classes
# =============================================================================



class AgentResponse(BaseModel):
    """Response from the AI agent."""
    message: str
    should_end_call: bool = False
    needs_transfer: bool = False
    transfer_reason: str | None = None
    collected_data: CallData | None = None
    tool_calls: list[dict] = []


class ConversationState(BaseModel):
    """Tracks conversation state for a call."""
    contact_id: str
    contact_name: str | None = None
    call_sid: str
    messages: list[dict] = []
    collected_info: dict = {}
    turn_count: int = 0
    appointment_booked: bool = False
    call_outcome: str | None = None
    needs_transfer: bool = False
    transfer_reason: str | None = None


class DentalAgent:
    """
    GPT-5-mini powered conversation agent for dental lead qualification.
    
    Uses GPT-5-mini with function calling to:
    - Conduct natural conversations
    - Extract structured patient data
    - Detect emergencies and escalate
    - Book appointments
    """
    
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.safety_detector = SafetyDetector()
        self._conversations: dict[str, ConversationState] = {}
    
    def _get_or_create_conversation(
        self,
        contact_id: str,
        call_sid: str,
        contact_name: str | None = None
    ) -> ConversationState:
        """Get existing conversation state or create new one."""
        key = f"{contact_id}:{call_sid}"
        if key not in self._conversations:
            system_context = f"{SYSTEM_PROMPT}\n\nCurrent Date and Time: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}"
            if contact_name:
                system_context += f"\n\nPatient Name: {contact_name}\nYou are speaking with {contact_name}."
            
            self._conversations[key] = ConversationState(
                contact_id=contact_id,
                contact_name=contact_name,
                call_sid=call_sid,
                messages=[
                    {"role": "system", "content": system_context}
                ]
            )
        return self._conversations[key]
    
    async def process_input(
        self,
        user_input: str,
        contact_id: str,
        call_sid: str,
        contact_name: str | None = None
    ) -> AgentResponse:
        """
        Process user speech input and generate response.
        
        Args:
            user_input: Transcribed speech from patient
            contact_id: GHL contact ID
            call_sid: Twilio call SID
            contact_name: Name of the contact (optional)
        
        Returns:
            AgentResponse with message and call state
        """
        # Get conversation state
        state = self._get_or_create_conversation(contact_id, call_sid, contact_name)
        state.turn_count += 1
        
        # Safety check first
        safety_result = self.safety_detector.check_input(user_input)
        if safety_result.needs_escalation:
            logger.warning(f"Safety escalation triggered: {safety_result.reason}")
            
            # Record conversation state before returning
            state.messages.append({"role": "user", "content": user_input})
            
            if safety_result.level == EscalationLevel.EMERGENCY:
                response_text = "I understand this is serious. Let me transfer you to our dental staff right away."
                state.messages.append({"role": "assistant", "content": response_text})
                
                return AgentResponse(
                    message=response_text,
                    needs_transfer=True,
                    transfer_reason=safety_result.reason,
                    collected_data=CallData(
                        outcome="escalated",
                        escalated=True,
                        escalation_reason=safety_result.reason
                    )
                )
            elif safety_result.level == EscalationLevel.URGENT:
                response_text = (
                    "I'm concerned about the level of pain you're experiencing. "
                    "Would you like me to connect you with our dental staff right away, "
                    "or would you prefer to schedule an urgent appointment?"
                )
                state.messages.append({"role": "assistant", "content": response_text})
                
                # For urgent but not emergency, offer transfer
                return AgentResponse(
                    message=response_text,
                    needs_transfer=False  # Let patient decide
                )
        
        # Add user message to conversation
        state.messages.append({"role": "user", "content": user_input})
        
        # Loop for tool execution (max 3 turns to prevent infinite loops)
        for _ in range(3):
            try:
                # Call GPT-5-mini
                response = await self.client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=state.messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    max_completion_tokens=2500,
                    response_format={"type": "text"},
                    verbosity="low",
                    reasoning_effort="minimal"
                )
                
                assistant_message = response.choices[0].message
                
                # Logging
                log_msg = f"Raw OpenAI Response: content={assistant_message.content}, tool_calls={assistant_message.tool_calls}"
                if hasattr(assistant_message, 'refusal'):
                     log_msg += f", refusal={assistant_message.refusal}"
                logger.info(log_msg)
                
                # Check for tool calls
                if assistant_message.tool_calls:
                    # Append assistant's tool call message to history
                    state.messages.append(assistant_message)
                    
                    tool_results = []
                    for tool_call in assistant_message.tool_calls:
                        # Execute tool
                        result = await self._execute_tool(
                            tool_call.function.name,
                            json.loads(tool_call.function.arguments),
                            state
                        )
                        
                        # Add tool output to history
                        state.messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                        
                        tool_results.append({
                            "tool": tool_call.function.name,
                            "result": result
                        })
                    
                    # Loop continues to get the AI's response to these tool outputs
                    continue
                
                # usage: No tool calls, just a text response
                response_text = assistant_message.content or ""
                
                # FALLBACK: If model returns nothing despite no tools, force a response
                if not response_text:
                    logger.warning("Model returned empty response with no tools! Using fallback.")
                    response_text = "I'm sorry, I missed that. Could you please say it again?"
                
                # Add assistant text response to conversation
                state.messages.append({
                    "role": "assistant",
                    "content": response_text
                })
                
                logger.info(f"🤖 AI Response: {response_text}")
                
                # Check call outcome from state (updated by tools)
                should_end = state.call_outcome is not None
                
                # Build collected data
                collected_data = None
                if state.collected_info:
                    collected_data = CallData(
                        pain_level=state.collected_info.get("pain_level"),
                        chief_complaint=state.collected_info.get("chief_complaint"),
                        insurance=state.collected_info.get("insurance"),
                        preferred_slot=state.collected_info.get("preferred_slot"),
                        outcome=state.call_outcome or "in_progress"
                    )
                
                return AgentResponse(
                    message=response_text,
                    should_end_call=should_end,
                    needs_transfer=state.needs_transfer,
                    transfer_reason=state.transfer_reason,
                    collected_data=collected_data,
                    # We return the accumulated tool calls from this interaction if needed for debugging,
                    # but typically the voice layer just needs the text.
                    # For simplicity, we can return the last set or empty.
                    tool_calls=[] 
                )
                
            except Exception as e:
                logger.error(f"Error processing input: {e}")
                return AgentResponse(
                    message="I apologize, I'm having a moment of difficulty. Could you please repeat that?",
                    should_end_call=False
                )
        
        # If loop finishes without returning (too many tool turns)
        return AgentResponse(
            message="I'm having trouble processing that request. Let me connect you with a staff member.",
            needs_transfer=True,
            transfer_reason="Max tool loop exceeded"
        )
    
    async def _execute_tool(
        self,
        tool_name: str,
        args: dict,
        state: ConversationState
    ) -> dict:
        """Execute a tool call and update state."""
        
        if tool_name == "record_patient_info":
            # Update collected info
            if args.get("chief_complaint"):
                state.collected_info["chief_complaint"] = args["chief_complaint"]
            if args.get("pain_level"):
                state.collected_info["pain_level"] = args["pain_level"]
            if args.get("insurance"):
                state.collected_info["insurance"] = args["insurance"]
            if args.get("preferred_slot"):
                state.collected_info["preferred_slot"] = args["preferred_slot"]
            
            logger.info(f"Recorded patient info: {args}")
            return {"status": "recorded", "data": args}
        
        elif tool_name == "schedule_appointment":
            # In production, this would call GHL calendar API
            state.appointment_booked = True
            state.collected_info["preferred_slot"] = f"{args['date']} {args['time']}"
            
            logger.info(f"Appointment scheduled: {args}")
            return {
                "status": "booked",
                "date": args["date"],
                "time": args["time"],
                "type": args["appointment_type"]
            }
        
        elif tool_name == "request_transfer":
            logger.info(f"Transfer requested: {args}")
            state.needs_transfer = True
            state.transfer_reason = args.get("reason", "User requested transfer")
            return {
                "status": "transfer_initiated",
                "reason": args["reason"],
                "urgency": args["urgency"]
            }
        
        elif tool_name == "end_conversation":
            state.call_outcome = args.get("outcome", "completed")
            logger.info(f"Conversation ending: {args}")
            return {
                "status": "ending",
                "outcome": args["outcome"],
                "summary": args.get("summary", "")
            }
        
        return {"status": "unknown_tool"}
    

    
    def cleanup_conversation(self, contact_id: str, call_sid: str) -> None:
        """Clean up conversation state after call ends."""
        key = f"{contact_id}:{call_sid}"
        if key in self._conversations:
            del self._conversations[key]

# Global instance
_agent_instance = None

def get_agent() -> DentalAgent:
    """Get singleton agent instance to persist conversation state."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = DentalAgent()
    return _agent_instance

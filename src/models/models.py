from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class CallStatus(str, Enum):
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


class PainLevel(str, Enum):
    NONE = "0"
    MILD = "1-3"
    MODERATE = "4-6"
    SEVERE = "7-8"
    EMERGENCY = "9-10"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class Lead(BaseModel):
    """Lead model representing a potential patient from GHL"""
    id: str = Field(..., description="GHL contact ID")
    first_name: str = Field(..., description="Lead's first name")
    last_name: Optional[str] = Field(None, description="Lead's last name")
    phone: str = Field(..., description="Lead's phone number")
    email: Optional[EmailStr] = Field(None, description="Lead's email address")
    source: Optional[str] = Field(None, description="Lead source")
    dnc_status: bool = Field(False, description="Do Not Call status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_contacted: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CallSession(BaseModel):
    """Model representing an active call session"""
    session_id: str = Field(..., description="Unique session identifier")
    lead_id: str = Field(..., description="Associated lead ID")
    twilio_call_sid: str = Field(..., description="Twilio call SID")
    status: CallStatus = Field(default=CallStatus.INITIATED)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    transcript: List[Dict[str, Any]] = Field(default_factory=list)
    qualification_data: Optional[Dict[str, Any]] = None
    escalation_reason: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QualificationData(BaseModel):
    """Structured data collected during lead qualification"""
    chief_complaint: Optional[str] = Field(
        None, description="Primary dental concern")
    pain_level: Optional[PainLevel] = Field(
        None, description="Pain level scale 0-10")
    urgency: UrgencyLevel = Field(default=UrgencyLevel.LOW)
    insurance_provider: Optional[str] = Field(
        None, description="Dental insurance provider")
    preferred_appointment_time: Optional[str] = Field(
        None, description="Preferred appointment slot")
    last_dental_visit: Optional[str] = Field(
        None, description="Last dental visit timeframe")
    current_medications: Optional[List[str]] = Field(default_factory=list)
    allergies: Optional[List[str]] = Field(default_factory=list)
    emergency_indicators: List[str] = Field(
        default_factory=list, description="Red flag conditions")

    def requires_escalation(self) -> bool:
        """Check if qualification data indicates need for immediate escalation"""
        emergency_conditions = [
            self.pain_level in [PainLevel.EMERGENCY],
            "swelling" in (self.chief_complaint or "").lower(),
            "fever" in (self.chief_complaint or "").lower(),
            "trauma" in (self.chief_complaint or "").lower(),
            "bleeding" in (self.chief_complaint or "").lower(),
            len(self.emergency_indicators) > 0
        ]
        return any(emergency_conditions)


class GHLWebhookPayload(BaseModel):
    """Model for incoming GHL webhook payloads"""
    event: str = Field(..., description="Event type")
    contact: Dict[str, Any] = Field(..., description="Contact data")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    def to_lead(self) -> Lead:
        """Convert webhook payload to Lead model"""
        contact_data = self.contact
        return Lead(
            id=contact_data.get("id"),
            first_name=contact_data.get("firstName", ""),
            last_name=contact_data.get("lastName"),
            phone=contact_data.get("phone", ""),
            email=contact_data.get("email"),
            source=contact_data.get("source"),
            dnc_status=contact_data.get("dncStatus", False)
        )


class ConversationTurn(BaseModel):
    """Model representing a single turn in the conversation"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    speaker: str = Field(..., description="'assistant' or 'user'")
    message: str = Field(..., description="Spoken or generated text")
    audio_url: Optional[str] = Field(None, description="URL to audio file")
    confidence_score: Optional[float] = Field(
        None, description="STT confidence")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AppointmentRequest(BaseModel):
    """Model for scheduling appointments in GHL"""
    contact_id: str = Field(..., description="GHL contact ID")
    appointment_date: datetime = Field(...,
                                       description="Requested appointment date/time")
    service_type: str = Field(default="Initial Consultation")
    notes: Optional[str] = Field(
        None, description="Additional appointment notes")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ComplianceFlags(BaseModel):
    """Model for tracking compliance-related flags"""
    dnc_checked: bool = Field(default=False)
    consent_obtained: bool = Field(default=False)
    phi_collected: bool = Field(default=False)
    escalation_triggered: bool = Field(default=False)
    recording_consent: bool = Field(default=False)

    def is_compliant(self) -> bool:
        """Check if all compliance requirements are met"""
        return (
            self.dnc_checked and
            self.consent_obtained and
            (not self.phi_collected or self.recording_consent)
        )

"""
GoHighLevel API Client
======================
Client for interacting with GoHighLevel CRM API.
Handles contact retrieval, updates, and appointment booking.
"""

import logging
from datetime import datetime
from typing import Any
import httpx
from pydantic import BaseModel

from src.config import get_settings

logger = logging.getLogger(__name__)


class CallData(BaseModel):
    """Structured data collected during a call."""
    pain_level: str | None = None
    chief_complaint: str | None = None
    insurance: str | None = None
    preferred_slot: str | None = None
    outcome: str = "call_completed"
    transcript_summary: str | None = None
    escalated: bool = False
    escalation_reason: str | None = None


class GHLClient:
    """
    GoHighLevel API client for CRM operations.
    """
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.ghl_api_key
        self.is_mock_mode = not self.api_key or "your_" in self.api_key or "test_" in self.api_key
        
        if self.is_mock_mode:
            logger.warning("⚠️ GHL Client running in MOCK MODE (Sandbox/Trial restrictions detected)")
        
        self.location_id = settings.ghl_location_id
        self.base_url = settings.ghl_api_base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        }
    
    async def get_contact(self, contact_id: str) -> dict | None:
        """Fetch contact details from GHL (or mock)."""
        if self.is_mock_mode:
            logger.info(f"[MOCK] Fetching contact {contact_id}")
            # Return a dummy contact for testing
            return {
                "id": contact_id,
                "firstName": "Mock User",
                "phone": "+19999999999",
                "dndSettings": {}
            }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/contacts/{contact_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                return data.get("contact")
        except Exception as e:
            logger.error(f"Error fetching contact: {e}")
            return None
    
    async def update_contact(self, contact_id: str, data: dict) -> bool:
        """Update contact information in GHL (or mock)."""
        if self.is_mock_mode:
            logger.info(f"[MOCK] Updating contact {contact_id} with: {data}")
            return True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/contacts/{contact_id}",
                    headers=self.headers,
                    json=data
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to update contact {contact_id}: {e}")
            return False
    
    async def add_contact_note(self, contact_id: str, note: str) -> bool:
        """Add a note to a contact's record (or mock)."""
        if self.is_mock_mode:
            logger.info(f"[MOCK] Adding note to {contact_id}:\n{note}")
            return True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/contacts/{contact_id}/notes",
                    headers=self.headers,
                    json={"body": note}
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to add note to contact {contact_id}: {e}")
            return False
    
    async def update_contact_with_call_data(self, contact_id: str, call_data: CallData) -> bool:
        """Update contact with structured data (or mock)."""
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
        
        if call_data.transcript_summary:
            note_parts.append(f"\nSummary: {call_data.transcript_summary}")
        
        note = "\n".join(note_parts)
        
        success = await self.add_contact_note(contact_id, note)
        
        custom_fields = {}
        if call_data.pain_level:
            custom_fields["pain_level"] = call_data.pain_level
        if call_data.insurance:
            custom_fields["insurance_provider"] = call_data.insurance
        
        if custom_fields:
            await self.update_contact(contact_id, {"customFields": custom_fields})
        
        return success

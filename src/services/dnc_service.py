import logging
from typing import Set, Optional
import re

logger = logging.getLogger(__name__)


class DNCService:
    """Do Not Call list management"""

    def __init__(self):
        self.dnc_set: Set[str] = set()
        self.dnc_list_key = "dnc:phone_numbers"

    async def connect(self):
        """Initialize in-memory storage"""
        logger.info("In-memory DNC service initialized")

    async def disconnect(self):
        """Cleanup (no-op for in-memory)"""
        logger.info("In-memory DNC service disconnected")

    def _normalize_phone_number(self, phone: str) -> str:
        """Normalize phone number format for consistent storage"""
        digits_only = re.sub(r'[^\d]', '', phone)

        if len(digits_only) == 10:
            digits_only = '1' + digits_only

        return digits_only

    async def check_dnc_status(self, phone_number: str) -> bool:
        """Check if a phone number is on the DNC list"""
        try:
            normalized_phone = self._normalize_phone_number(phone_number)
            is_dnc = normalized_phone in self.dnc_set

            logger.info(
                f"DNC check for {phone_number} ({normalized_phone}): {'DNC' if is_dnc else 'OK'}")
            return is_dnc

        except Exception as e:
            logger.error(f"Error checking DNC status for {phone_number}: {e}")
            # Fail safe - if we can't check DNC, assume it's on the list
            return True

    async def add_to_dnc_list(self, phone_number: str) -> bool:
        """Add a phone number to the DNC list"""
        try:
            normalized_phone = self._normalize_phone_number(phone_number)
            self.dnc_set.add(normalized_phone)

            logger.info(f"Added {phone_number} ({normalized_phone}) to DNC list")
            return True

        except Exception as e:
            logger.error(f"Error adding {phone_number} to DNC list: {e}")
            return False

    async def remove_from_dnc_list(self, phone_number: str) -> bool:
        """Remove a phone number from the DNC list"""
        try:
            normalized_phone = self._normalize_phone_number(phone_number)
            if normalized_phone in self.dnc_set:
                self.dnc_set.remove(normalized_phone)
                logger.info(f"Removed {phone_number} ({normalized_phone}) from DNC list")
                return True
            else:
                logger.warning(f"Phone number {phone_number} not found in DNC list")
                return True  # Consider it success if already not on list

        except Exception as e:
            logger.error(f"Error removing {phone_number} from DNC list: {e}")
            return False

    async def bulk_add_to_dnc_list(self, phone_numbers: list) -> bool:
        """Add multiple phone numbers to the DNC list"""
        try:
            for phone in phone_numbers:
                normalized_phone = self._normalize_phone_number(phone)
                self.dnc_set.add(normalized_phone)

            logger.info(f"Added {len(phone_numbers)} numbers to DNC list")
            return True

        except Exception as e:
            logger.error(f"Error bulk adding to DNC list: {e}")
            return False

    def get_dnc_count(self) -> int:
        """Get total count of numbers on DNC list"""
        return len(self.dnc_set)


class DatabaseService:
    """In-memory database for lead and session management"""

    def __init__(self, database_url: str = None):
        self.database_url = database_url
        self.leads = {}
        self.call_sessions = {}

    async def connect(self):
        """Initialize in-memory database"""
        logger.info("In-memory database service initialized")

    async def store_lead(self, lead) -> bool:
        """Store lead in memory"""
        self.leads[lead.id] = lead
        logger.info(f"Stored lead {lead.id} in memory")
        return True

    async def create_call_session(self, session) -> bool:
        """Create call session record in memory"""
        self.call_sessions[session.session_id] = session
        logger.info(f"Created call session {session.session_id}")
        return True

    async def update_lead_call_status(self, lead_id: str, call_sid: Optional[str], status: str) -> bool:
        """Update lead call status in memory"""
        if lead_id in self.leads:
            logger.info(f"Updated lead {lead_id} call status to {status}")
        return True

    async def update_call_session_status(self, call_sid: str, status: str) -> bool:
        """Update call session status in memory"""
        for session in self.call_sessions.values():
            if hasattr(session, 'call_sid') and session.call_sid == call_sid:
                session.status = status
                logger.info(f"Updated call session {call_sid} status to {status}")
                return True
        return True

    async def get_lead(self, lead_id: str):
        """Retrieve lead by ID from memory"""
        if lead_id in self.leads:
            return self.leads[lead_id]

        # Return mock lead if not found
        from ..models.models import Lead
        return Lead(
            id=lead_id,
            first_name="John",
            last_name="Doe",
            phone="+1234567890"
        )

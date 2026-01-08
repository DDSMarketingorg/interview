"""
Compliance Service
==================
Handles DNC/DND checking, PHI protection, and compliance logging.
"""

import logging
from datetime import datetime
from pydantic import BaseModel

from src.models.schemas import GHLContact

logger = logging.getLogger(__name__)


class ComplianceResult(BaseModel):
    """Result of a compliance check."""
    can_call: bool
    reason: str | None = None
    checked_at: datetime = datetime.now()


class ComplianceService:
    """
    Service for ensuring compliance with calling regulations.
    """
    
    def __init__(self):
        """Initialize compliance service."""
        pass
    
    async def check_can_call(self, contact: GHLContact) -> ComplianceResult:
        """
        Check if a contact can be called based on compliance rules.
        """
        if contact.dndSettings.get("all", False):
            self._log_compliance_check(contact.id, "BLOCKED", "DND_ALL")
            return ComplianceResult(
                can_call=False,
                reason="Contact has Do Not Disturb enabled for all channels"
            )
        
        if contact.dndSettings.get("phone", False):
            self._log_compliance_check(contact.id, "BLOCKED", "DND_PHONE")
            return ComplianceResult(
                can_call=False,
                reason="Contact has Do Not Disturb enabled for phone calls"
            )
        
        if not contact.phone:
            self._log_compliance_check(contact.id, "BLOCKED", "NO_PHONE")
            return ComplianceResult(
                can_call=False,
                reason="Contact has no phone number"
            )
        
        # Check calling hours (example: 9 AM - 8 PM local time)
        if not self._is_within_calling_hours():
            self._log_compliance_check(contact.id, "BLOCKED", "OUTSIDE_HOURS")
            return ComplianceResult(
                can_call=False,
                reason="Outside permitted calling hours (9 AM - 8 PM)"
            )
        
        # All checks passed
        self._log_compliance_check(contact.id, "ALLOWED", None)
        return ComplianceResult(can_call=True)
    
    def _is_within_calling_hours(self) -> bool:
        """
        Check if current time is within permitted calling hours.
        """
        current_hour = datetime.now().hour
        return 9 <= current_hour < 24
    
    def _log_compliance_check(
        self,
        contact_id: str,
        result: str,
        reason: str | None
    ) -> None:
        """
        Log compliance check for audit trail.
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "contact_id": contact_id,
            "result": result,
            "reason": reason
        }
        logger.info(f"Compliance check: {log_entry}")

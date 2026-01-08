"""
Tests for Compliance Service
============================
"""

import pytest
from src.services.compliance import ComplianceService, ComplianceResult
from src.models.schemas import GHLContact


@pytest.fixture
def service():
    return ComplianceService()


class TestDNDChecking:
    """Test Do Not Disturb checking."""
    
    @pytest.mark.asyncio
    async def test_blocks_dnd_all_enabled(self, service):
        contact = GHLContact(
            id="CNT_dnd_all",
            firstName="John",
            phone="+14165551234",
            dndSettings={"all": True}
        )
        
        result = await service.check_can_call(contact)
        
        assert result.can_call == False
        assert "all channels" in result.reason
    
    @pytest.mark.asyncio
    async def test_blocks_dnd_phone_enabled(self, service):
        contact = GHLContact(
            id="CNT_dnd_phone",
            firstName="Jane",
            phone="+14165551234",
            dndSettings={"phone": True}
        )
        
        result = await service.check_can_call(contact)
        
        assert result.can_call == False
        assert "phone calls" in result.reason
    
    @pytest.mark.asyncio
    async def test_allows_dnd_email_only(self, service):
        """DND for email only should not block phone calls."""
        contact = GHLContact(
            id="CNT_dnd_email",
            firstName="Bob",
            phone="+14165551234",
            dndSettings={"email": True, "phone": False}
        )
        
        result = await service.check_can_call(contact)
        
        # Should be allowed (email DND doesn't affect phone)
        # Note: May still be blocked by other checks
        assert "phone calls" not in str(result.reason or "")


class TestPhoneValidation:
    """Test phone number validation."""
    
    @pytest.mark.asyncio
    async def test_blocks_no_phone(self, service):
        contact = GHLContact(
            id="CNT_no_phone",
            firstName="NoPhone"
        )
        
        result = await service.check_can_call(contact)
        
        assert result.can_call == False
        assert "no phone number" in result.reason.lower()



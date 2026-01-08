"""
Tests for GHL Webhooks
======================
"""

import pytest
from fastapi.testclient import TestClient

# Mock settings before importing app
import os
os.environ.update({
    "GHL_API_KEY": "test_key",
    "GHL_LOCATION_ID": "test_location",
    "TWILIO_ACCOUNT_SID": "test_sid",
    "TWILIO_AUTH_TOKEN": "test_token",
    "TWILIO_PHONE_NUMBER": "+15551234567",
    "OPENAI_API_KEY": "test_openai",
    "ELEVENLABS_API_KEY": "test_eleven"
})

from src.main import app
from src.models.schemas import GHLContact, GHLWebhookPayload


client = TestClient(app)


class TestWebhookPayloadParsing:
    """Test GHL webhook payload parsing."""
    
    def test_parse_contact_created_event(self):
        """Test parsing a standard contact.created webhook."""
        payload = {
            "event": "contact.created",
            "contact": {
                "id": "CNT_12345",
                "firstName": "Sarah",
                "lastName": "Johnson",
                "phone": "+14165551234",
                "email": "sarah@example.com",
                "tags": ["new_lead", "dental"],
                "dndSettings": {"all": False, "phone": False}
            },
            "locationId": "LOC_xyz"
        }
        
        parsed = GHLWebhookPayload(**payload)
        
        assert parsed.event == "contact.created"
        assert parsed.contact.id == "CNT_12345"
        assert parsed.contact.firstName == "Sarah"
        assert parsed.contact.phone == "+14165551234"
        assert parsed.contact.dndSettings.get("phone") == False
    
    def test_parse_minimal_contact(self):
        """Test parsing contact with minimal fields."""
        payload = {
            "event": "contact.created",
            "contact": {
                "id": "CNT_minimal"
            }
        }
        
        parsed = GHLWebhookPayload(**payload)
        
        assert parsed.contact.id == "CNT_minimal"
        assert parsed.contact.firstName is None
        assert parsed.contact.phone is None
        assert parsed.contact.dndSettings == {}
    
    def test_parse_contact_with_dnd_enabled(self):
        """Test parsing contact with DND enabled."""
        payload = {
            "event": "contact.created",
            "contact": {
                "id": "CNT_dnd",
                "firstName": "John",
                "phone": "+14165551234",
                "dndSettings": {"all": True, "phone": True}
            }
        }
        
        parsed = GHLWebhookPayload(**payload)
        
        assert parsed.contact.dndSettings.get("all") == True
        assert parsed.contact.dndSettings.get("phone") == True


class TestWebhookEndpoints:
    """Test webhook HTTP endpoints."""
    
    def test_health_endpoint(self):
        """Test GHL webhook health check."""
        response = client.get("/api/webhooks/ghl/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "ready"
    
    def test_webhook_without_phone_skipped(self):
        """Test that contacts without phone are skipped."""
        payload = {
            "event": "contact.created",
            "contact": {
                "id": "CNT_nophone",
                "firstName": "NoPhone"
            }
        }
        
        response = client.post("/api/webhooks/ghl/contact", json=payload)
        
        assert response.status_code == 200
        assert response.json()["status"] == "skipped"
        assert "No phone number" in response.json()["reason"]
    
    def test_non_contact_created_ignored(self):
        """Test that contacts without phone (from any event type) are skipped."""
        # Note: GHL workflow webhooks send contact data at root level,
        # so all events are treated as contact.created. Contacts without
        # phone numbers get skipped regardless of original event type.
        payload = {
            "event": "contact.updated",
            "contact": {
                "id": "CNT_updated",
                "firstName": "Updated"
            }
        }
        
        response = client.post("/api/webhooks/ghl/contact", json=payload)
        
        assert response.status_code == 200
        # Without phone number, status is "skipped" not "ignored"
        assert response.json()["status"] == "skipped"


class TestAppHealth:
    """Test application health."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "Dental Marketing AI Voice Assistant" in response.json()["service"]
    
    def test_health_endpoint(self):
        """Test health check."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

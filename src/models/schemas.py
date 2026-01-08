"""
Shared Data Models
==================
Pydantic models shared across services and API handlers.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class GHLContact(BaseModel):
    """GoHighLevel Contact model - simplified to only used fields."""
    id: str = Field(..., description="Contact ID (e.g., CNT_xxx)")
    firstName: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    dndSettings: dict = Field(default_factory=dict)


class GHLWebhookPayload(BaseModel):
    """GoHighLevel Webhook payload model."""
    event: str = Field(..., description="Event type (e.g., contact.created)")
    contact: GHLContact
    locationId: str | None = Field(default=None)
    timestamp: datetime | None = Field(default=None)

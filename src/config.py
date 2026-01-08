"""
Application Configuration
=========================
Environment configuration using Pydantic Settings for type-safe config.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Application
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_base_url: str = Field(default="http://localhost:8000", alias="APP_BASE_URL")
    
    # GoHighLevel
    ghl_api_key: str = Field(..., alias="GHL_API_KEY")
    ghl_location_id: str = Field(..., alias="GHL_LOCATION_ID")
    ghl_webhook_secret: str = Field(default="", alias="GHL_WEBHOOK_SECRET")
    ghl_api_base_url: str = Field(
        default="https://services.leadconnectorhq.com", 
        alias="GHL_API_BASE_URL"
    )
    
    # Twilio
    twilio_account_sid: str = Field(..., alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(..., alias="TWILIO_AUTH_TOKEN")
    twilio_phone_number: str = Field(..., alias="TWILIO_PHONE_NUMBER")
    
    # OpenAI
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")

    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

import os
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from src.services.webhook_service import WebhookService, setup_webhook_routes
from src.services.twilio_service import TwilioService
from src.services.ai_service import AIService
from src.services.ghl_service import GHLService
from src.services.dnc_service import DNCService, DatabaseService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown"""
    logger.info("Starting AI Voice Assistant application...")

    await app.state.dnc_service.connect()
    await app.state.db_service.connect()

    logger.info("All services initialized successfully")

    yield

    logger.info("Shutting down AI Voice Assistant application...")
    await app.state.dnc_service.disconnect()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""

    app = FastAPI(
        title="AI Voice Assistant for Dental Marketing",
        description="Automated lead qualification system for dental practices",
        version="1.0.0",
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    dnc_service = DNCService()
    db_service = DatabaseService(os.getenv("DATABASE_URL"))

    twilio_service = TwilioService(
        account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
        auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
        phone_number=os.getenv("TWILIO_PHONE_NUMBER"),
        webhook_base_url=os.getenv("WEBHOOK_BASE_URL")
    )

    ai_service = AIService(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_region=os.getenv("AWS_REGION", "us-east-1")
    )

    ghl_service = GHLService(
        api_key=os.getenv("GHL_API_KEY"),
        base_url=os.getenv("GHL_BASE_URL", "https://services.leadconnectorhq.com")
    )

    webhook_service = WebhookService(
        webhook_secret=os.getenv("GHL_WEBHOOK_SECRET"),
        dnc_service=dnc_service,
        twilio_service=twilio_service,
        db_service=db_service
    )

    # Store services in app state for access in routes
    app.state.dnc_service = dnc_service
    app.state.db_service = db_service
    app.state.twilio_service = twilio_service
    app.state.ai_service = ai_service
    app.state.ghl_service = ghl_service
    app.state.webhook_service = webhook_service

    setup_webhook_routes(app, webhook_service)
    twilio_service.setup_voice_routes(app, ai_service, db_service)

    return app


app = create_app()




@app.get("/")
async def root():
    """Root endpoint with system status"""
    return {
        "service": "AI Voice Assistant for Dental Marketing",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "webhooks": "/webhooks/ghl",
            "health": "/health",
            "voice": "/voice/*"
        }
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        dnc_size = app.state.dnc_service.get_dnc_count()

        health_status = {
            "status": "healthy",
            "timestamp": "2025-01-07T19:30:00Z",
            "services": {
                "dnc_service": "healthy",
                "database": "healthy",
                "twilio": "healthy",
                "openai": "healthy",
                "ghl": "healthy"
            },
            "metrics": {
                "dnc_list_size": dnc_size,
                "active_calls": 0,
                "calls_today": 0
            }
        }

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.post("/admin/dnc/add")
async def add_to_dnc(phone_number: str):
    """Admin endpoint to add phone number to DNC list"""
    try:
        success = await app.state.dnc_service.add_to_dnc_list(phone_number)
        if success:
            return {"status": "success", "message": f"Added {phone_number} to DNC list"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add to DNC list")
    except Exception as e:
        logger.error(f"Error adding to DNC: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/admin/dnc/check")
async def check_dnc_status(phone_number: str):
    """Admin endpoint to check if phone number is on DNC list"""
    try:
        is_dnc = await app.state.dnc_service.check_dnc_status(phone_number)
        return {
            "phone_number": phone_number,
            "is_dnc": is_dnc,
            "status": "on DNC list" if is_dnc else "not on DNC list"
        }
    except Exception as e:
        logger.error(f"Error checking DNC status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/admin/dnc/remove")
async def remove_from_dnc(phone_number: str):
    """Admin endpoint to remove phone number from DNC list"""
    try:
        success = await app.state.dnc_service.remove_from_dnc_list(phone_number)
        if success:
            return {"status": "success", "message": f"Removed {phone_number} from DNC list"}
        else:
            raise HTTPException(status_code=500, detail="Failed to remove from DNC list")
    except Exception as e:
        logger.error(f"Error removing from DNC: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

"""
FastAPI Application Entry Point
===============================
Main application with middleware, routes, and startup/shutdown events.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.api import webhooks
from src.api import twilio_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    settings = get_settings()
    logger.info(f"Starting Dental AI Voice Assistant in {settings.app_env} mode")
    yield
    logger.info("Shutting down Dental AI Voice Assistant")


app = FastAPI(
    title="Dental Marketing AI Voice Assistant",
    description="AI-powered voice assistant for dental lead qualification",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(twilio_handlers.router, prefix="/api/voice", tags=["Voice"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "dental-ai-voice-assistant"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "Dental Marketing AI Voice Assistant",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

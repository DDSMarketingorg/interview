"""
Speech-to-Text Service
======================
OpenAI Whisper integration for high-accuracy speech transcription.
"""

import logging
import io
from openai import AsyncOpenAI
from src.config import get_settings

logger = logging.getLogger(__name__)

class STTService:
    """
    Speech-to-Text service using OpenAI Whisper API.
    """
    
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        
    async def transcribe(self, audio_data: bytes, filename: str = "audio.wav") -> str:
        """
        Transcribe audio bytes to text.
        
        Args:
            audio_data: Raw audio bytes
            filename: Virtual filename for the API (helps with format detection)
            
        Returns:
            Transcribed text
        """
        try:
            # Create a file-like object from bytes
            audio_file = io.BytesIO(audio_data)
            audio_file.name = filename
            
            # Call Whisper API
            transcript = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en",  # Optimize for English
                prompt="Dental appointment phone call context.", # Guide the model
                response_format="text"
            )
            
            logger.info(f"Whisper transcription: '{transcript}'")
            return transcript
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            # Fallback or re-raise? For now re-raise to handle upstream
            raise

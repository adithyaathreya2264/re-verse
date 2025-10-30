"""
Service layer for RE-VERSE application.
Contains business logic and external API integrations.
"""
from app.services.ai_worker import generate_audio_task

__all__ = ["generate_audio_task"]

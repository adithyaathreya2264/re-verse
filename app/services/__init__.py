"""
Service layer for RE-VERSE application.
"""
from app.services.ai_worker import generate_audio_task
from app.services.gemini_service import (
    generate_script_from_pdf,
    extract_text_from_pdf
)

__all__ = [
    "generate_audio_task",
    "generate_script_from_pdf",
    "extract_text_from_pdf"
]
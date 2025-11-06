"""
Service layer for RE-VERSE application.
"""
from app.services.ai_worker import generate_audio_task
from app.services.gemini_service import (
    generate_script_from_pdf,
    generate_audio_from_script,
    extract_text_from_pdf
)
from app.services.gcs_service import (
    upload_audio_to_gcs,
    generate_signed_url,
    delete_audio_from_gcs,
    GCSService
)

__all__ = [
    "generate_audio_task",
    "generate_script_from_pdf",
    "generate_audio_from_script",
    "extract_text_from_pdf",
    "upload_audio_to_gcs",
    "generate_signed_url",
    "delete_audio_from_gcs",
    "GCSService"
]

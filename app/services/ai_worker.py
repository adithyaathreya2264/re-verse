"""
Background worker for AI audio generation tasks.
"""
import asyncio
from datetime import datetime, timezone

from app.db.operations.job_operations import update_job_status
from app.models.enums import JobStatus
from app.services.gemini_service import generate_script_from_pdf
from app.utils.logger import logger


async def generate_audio_task(
    job_id: str,
    pdf_contents: bytes,
    prompt: str,
    style: str,
    duration: str
):
    """
    Background task for generating audio from PDF.
    
    Phase 1: Generate script using Gemini LLM
    Phase 2: Generate audio using Gemini TTS (Step 7)
    Phase 3: Upload to GCS and get signed URL (Step 8)
    """
    try:
        logger.info(f"🎬 Starting audio generation for job: {job_id}")
        
        # ========== Phase 1: Update to PROCESSING ==========
        await update_job_status(job_id, JobStatus.PROCESSING.value)
        logger.info(f"📝 Job {job_id} status updated to PROCESSING")
        
        # ========== Phase 2: Generate Script ==========
        logger.info(f"🤖 Generating script for job: {job_id}")
        
        script_data = await generate_script_from_pdf(
            pdf_bytes=pdf_contents,
            user_prompt=prompt,
            style=style,
            duration=duration
        )
        
        logger.info(f"✅ Script generated for job {job_id}")
        logger.info(f"   Title: {script_data['title']}")
        logger.info(f"   Speakers: {len(script_data['speakers'])}")
        logger.info(f"   Dialogue turns: {len(script_data['dialogue'])}")
        
        # ========== Phase 3: Generate Audio (TODO: Step 7) ==========
        # TODO: Call Gemini TTS to generate audio from script
        logger.warning(f"⚠️ Audio generation not yet implemented (Step 7)")
        
        # ========== Phase 4: Upload to GCS (TODO: Step 8) ==========
        # TODO: Upload audio file to Google Cloud Storage
        logger.warning(f"⚠️ GCS upload not yet implemented (Step 8)")
        
        # Placeholder: Mark as completed with script data
        await update_job_status(
            job_id,
            JobStatus.COMPLETED.value,
            audio_url=f"Script generated with {len(script_data['dialogue'])} turns",
            completed_at=datetime.now(timezone.utc)
        )
        
        logger.info(f"✅ Job {job_id} completed (script generation phase)")
        
    except Exception as e:
        logger.error(f"❌ Job {job_id} failed: {e}", exc_info=True)
        
        await update_job_status(
            job_id,
            JobStatus.FAILED.value,
            error_message=str(e),
            completed_at=datetime.now(timezone.utc)
        )

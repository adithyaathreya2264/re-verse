"""
Background worker for AI audio generation tasks.
Now with Google Cloud Storage integration.
"""
import asyncio
import os
from datetime import datetime, timezone

from app.db.operations.job_operations import update_job_status
from app.models.enums import JobStatus
from app.services.gemini_service import generate_script_from_pdf
from app.services.tts_service import merge_dialogue_to_audio
from app.services.gcs_service import upload_audio_to_gcs, generate_signed_url
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
    
    Complete workflow:
    1. Generate script using Gemini LLM
    2. Generate audio using Gemini TTS
    3. Upload to Google Cloud Storage
    4. Generate signed URL for access
    """
    temp_file_path = None
    
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
        
        dialogue = script_data["dialogue"]
        speakers = script_data["speakers"]

        voice_map = {
            speakers[0]["id"]: "en-US-Neural2-D",   # Assign a Google neural voice for speaker 10
            speakers[1]["id"]: "en-US-Neural2-F"    # ...and another for speaker 2
        }

        from app.services.tts_service import merge_dialogue_to_audio

        audio_bytes = merge_dialogue_to_audio(dialogue, speakers, voice_map)

        logger.info(f"✅ Script generated for job {job_id}")
        logger.info(f"   Title: {script_data['title']}")
        logger.info(f"   Dialogue turns: {len(script_data['dialogue'])}")
        
        # ========== Phase 3: Generate Audio ==========
        logger.info(f"🎙️ Generating audio for job: {job_id}")
        
        
        
        logger.info(f"✅ Audio generated: {len(audio_bytes)} bytes")
        
        # ========== Phase 4: Upload to GCS ==========
        logger.info(f"☁️ Uploading audio to Google Cloud Storage...")
        
        blob_name = await upload_audio_to_gcs(
            audio_bytes=audio_bytes,
            job_id=job_id,
            content_type="audio/mpeg"
        )
        
        logger.info(f"✅ Audio uploaded to GCS: {blob_name}")
        
        # ========== Phase 5: Generate Signed URL ==========
        logger.info(f"🔗 Generating signed URL...")
        
        signed_url = await generate_signed_url(blob_name)
        
        logger.info(f"✅ Signed URL generated")
        
        # ========== Phase 6: Mark as Completed ==========
        await update_job_status(
            job_id,
            JobStatus.COMPLETED.value,
            audio_url=signed_url,
            completed_at=datetime.now(timezone.utc)
        )
        
        logger.info(f"✅ Job {job_id} completed successfully")
        logger.info(f"   Audio URL: {signed_url[:100]}...")
        
    except Exception as e:
        logger.error(f"❌ Job {job_id} failed: {e}", exc_info=True)
        
        await update_job_status(
            job_id,
            JobStatus.FAILED.value,
            error_message=str(e),
            completed_at=datetime.now(timezone.utc)
        )
    
    finally:
        # Cleanup: Remove temporary local file if it exists
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"🗑️ Temporary file cleaned up: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Failed to cleanup temp file: {cleanup_error}")

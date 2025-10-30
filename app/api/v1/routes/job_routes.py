"""
Job management API routes.
Handles job creation, status checking, and result retrieval.
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile, HTTPException, status
from typing import Optional

from app.models.enums import JobStatus, StyleType, DurationType
from app.models.job_model import JobResponse, JobResultResponse, ErrorResponse
from app.db.operations.job_operations import (
    create_new_job,
    get_job_result,
    update_job_status
)
from app.utils.logger import logger
from app.utils.file_helpers import (
    validate_file_type,
    validate_file_size,
    read_upload_file,
    get_file_size,
    sanitize_filename
)

router = APIRouter()


# ==================== Job Creation Endpoint ====================

@router.post(
    "/generate-job",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create Audio Generation Job",
    description="Upload a PDF and create a new podcast audio generation job",
    responses={
        202: {"description": "Job created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid input"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def create_generation_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF file to convert to podcast"),
    prompt: str = Form(..., min_length=10, max_length=2000, description="Text prompt to guide content focus"),
    style: str = Form(default="Student-Professor", description="Conversation style"),
    duration: str = Form(default="MEDIUM", description="Audio duration preference")
):
    """
    Create a new audio generation job.
    
    **Process:**
    1. Validates the uploaded PDF file
    2. Creates a job record in the database
    3. Triggers background processing
    4. Returns job ID immediately (HTTP 202)
    
    **Parameters:**
    - **file**: PDF document (max 50MB)
    - **prompt**: Instructions for content focus (10-2000 characters)
    - **style**: Conversation style (Student-Professor, Critique, Debate, etc.)
    - **duration**: Audio length (SHORTER, MEDIUM, LONGER)
    
    **Returns:**
    - **job_id**: Unique identifier for status polling
    - **status**: Initial job status (PENDING)
    - **created_at**: Job creation timestamp
    """
    try:
        # ========== 1. Validate File Type ==========
        is_valid_type, type_error = validate_file_type(file)
        if not is_valid_type:
            logger.warning(f"File type validation failed: {type_error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=type_error
            )
        
        # ========== 2. Read and Validate File Size ==========
        file_contents = await read_upload_file(file)
        file_size = get_file_size(file_contents)
        
        is_valid_size, size_error = validate_file_size(file_size)
        if not is_valid_size:
            logger.warning(f"File size validation failed: {size_error}")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=size_error
            )
        
        # ========== 3. Sanitize Filename ==========
        safe_filename = sanitize_filename(file.filename)
        logger.info(f"Processing file: {safe_filename} ({file_size} bytes)")
        
        # ========== 4. Validate Enums ==========
        try:
            style_enum = StyleType(style)
            duration_enum = DurationType(duration)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid style or duration value: {str(e)}"
            )
        
        # ========== 5. Generate Unique Job ID ==========
        job_id = str(uuid.uuid4())
        
        # ========== 6. Create Job Document ==========
        job_data = {
            "prompt": prompt.strip(),
            "style": style_enum.value,
            "duration": duration_enum.value,
            "pdf_filename": safe_filename,
            "pdf_size": file_size,
            "status": JobStatus.PENDING.value
        }
        
        # Save to database
        created_job_id = await create_new_job(job_data)
        
        if not created_job_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create job in database"
            )
        
        logger.info(f"✅ Job created: {created_job_id}")
        
        # ========== 7. Trigger Background Task ==========
        # Import here to avoid circular dependency
        from app.services.ai_worker import generate_audio_task
        
        background_tasks.add_task(
            generate_audio_task,
            job_id=created_job_id,
            pdf_contents=file_contents,
            prompt=prompt.strip(),
            style=style_enum.value,
            duration=duration_enum.value
        )
        
        logger.info(f"🚀 Background task queued for job: {created_job_id}")
        
        # ========== 8. Return Response ==========
        return JobResponse(
            job_id=created_job_id,
            status=JobStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            message="Job created successfully. Use job_id to check status."
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error creating job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the job"
        )


# ==================== Job Status Endpoint ====================

@router.get(
    "/job/{job_id}",
    response_model=JobResultResponse,
    summary="Get Job Status",
    description="Retrieve the current status and result of a job",
    responses={
        200: {"description": "Job found"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def get_job_status(job_id: str):
    """
    Get the status and result of a job.
    
    **Status Values:**
    - **PENDING**: Job is queued and waiting to start
    - **PROCESSING**: Job is currently being processed
    - **COMPLETED**: Job finished successfully (audio_url available)
    - **FAILED**: Job failed (error_message available)
    
    **Usage:**
    Poll this endpoint every 3-5 seconds until status is COMPLETED or FAILED.
    
    **Parameters:**
    - **job_id**: The unique job identifier returned from job creation
    
    **Returns:**
    - Complete job information including status, timestamps, and audio URL (when completed)
    """
    try:
        # Fetch job from database
        job = await get_job_result(job_id)
        
        if not job:
            logger.warning(f"Job not found: {job_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID '{job_id}' not found"
            )
        
        # Convert MongoDB document to response model
        response = JobResultResponse(
            job_id=job["_id"],
            status=JobStatus(job["status"]),
            prompt=job["prompt"],
            style=job["style"],
            duration=job["duration"],
            pdf_filename=job["pdf_filename"],
            pdf_size=job["pdf_size"],
            audio_url=job.get("audio_url"),
            error_message=job.get("error_message"),
            created_at=job["created_at"],
            updated_at=job["updated_at"],
            completed_at=job.get("completed_at")
        )
        
        logger.info(f"✅ Job status retrieved: {job_id} - {job['status']}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving job status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving job status"
        )

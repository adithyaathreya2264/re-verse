"""
Pydantic models for job-related API requests and responses.
Provides automatic validation, serialization, and API documentation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator, ConfigDict # type: ignore

from app.models.enums import JobStatus, StyleType, DurationType


# ==================== Request Models ====================

class JobCreateRequest(BaseModel):
    """
    Request model for job creation endpoint.
    Note: file is handled separately as UploadFile in FastAPI route.
    """
    prompt: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="User's text prompt to guide content summarization and focus",
        examples=["Summarize Chapter 3 focusing on the methodology section"]
    )
    
    style: StyleType = Field(
        default=StyleType.STUDENT_PROFESSOR,
        description="Conversational style for the generated audio dialogue"
    )
    
    duration: DurationType = Field(
        default=DurationType.MEDIUM,
        description="Desired length of the generated audio"
    )
    
    @validator("prompt")
    def validate_prompt(cls, v):
        """Ensure prompt is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Prompt cannot be empty or whitespace only")
        return v.strip()
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prompt": "Summarize the key findings of this research paper in a conversational way",
                "style": "Student-Professor",
                "duration": "MEDIUM"
            }
        }
    )


# ==================== Response Models ====================

class JobResponse(BaseModel):
    """
    Response model for job creation (HTTP 202 Accepted).
    Returns immediately with job ID for status polling.
    """
    job_id: str = Field(
        ...,
        description="Unique identifier for the created job"
    )
    status: JobStatus = Field(
        default=JobStatus.PENDING,
        description="Current status of the job"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the job was created"
    )
    message: str = Field(
        default="Job created successfully. Use job_id to check status.",
        description="Human-readable message"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "507f1f77bcf86cd799439011",
                "status": "PENDING",
                "created_at": "2025-10-27T14:30:00Z",
                "message": "Job created successfully. Use job_id to check status."
            }
        }
    )


class JobResultResponse(BaseModel):
    """
    Response model for job status/result retrieval.
    Contains complete job information including audio URL when completed.
    """
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    
    # Request details
    prompt: str = Field(..., description="Original user prompt")
    style: str = Field(..., description="Conversation style used")
    duration: str = Field(..., description="Duration preference")
    pdf_filename: str = Field(..., description="Original PDF filename")
    pdf_size: int = Field(..., description="PDF file size in bytes")
    
    # Result data (populated when completed)
    audio_url: Optional[str] = Field(
        None,
        description="Signed URL to download generated audio (available when status is COMPLETED)"
    )
    
    # Error information (populated when failed)
    error_message: Optional[str] = Field(
        None,
        description="Error details if job failed"
    )
    
    # Timestamps
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(
        None,
        description="Job completion timestamp (for COMPLETED or FAILED status)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "507f1f77bcf86cd799439011",
                "status": "COMPLETED",
                "prompt": "Summarize the methodology section",
                "style": "Student-Professor",
                "duration": "MEDIUM",
                "pdf_filename": "research_paper.pdf",
                "pdf_size": 2048576,
                "audio_url": "https://storage.googleapis.com/bucket/audio.mp3?signature=...",
                "error_message": None,
                "created_at": "2025-10-27T14:30:00Z",
                "updated_at": "2025-10-27T14:35:00Z",
                "completed_at": "2025-10-27T14:35:00Z"
            }
        }
    )


# ==================== Internal Models ====================

class JobDocument(BaseModel):
    """
    Internal model representing job data in MongoDB.
    Used for database operations and not exposed in API.
    """
    prompt: str
    style: str
    duration: str
    pdf_filename: str
    pdf_size: int
    status: str
    
    # Storage references
    pdf_gcs_path: Optional[str] = None  # GCS path to uploaded PDF
    audio_gcs_path: Optional[str] = None  # GCS path to generated audio
    audio_url: Optional[str] = None  # Signed URL for audio download
    
    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = Field(default=0, description="Number of retry attempts")
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    # Optional user tracking (for future authentication)
    user_id: Optional[str] = None
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


# ==================== Error Response Models ====================

class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "detail": "Prompt must be at least 10 characters long"
            }
        }
    )


class HealthResponse(BaseModel):
    """Health check endpoint response."""
    status: str = Field(default="healthy", description="API health status")
    timestamp: datetime = Field(..., description="Current server time")
    database: str = Field(..., description="Database connection status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-27T14:30:00Z",
                "database": "connected"
            }
        }
    )

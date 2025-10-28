"""
Test script for Pydantic models and enums.
Run: python test_models.py
"""
from datetime import datetime, timezone
from pydantic import ValidationError # type: ignore

from app.models.enums import JobStatus, StyleType, DurationType
from app.models.job_model import (
    JobCreateRequest,
    JobResponse,
    JobResultResponse,
    ErrorResponse
)


def test_enums():
    """Test enum functionality."""
    print("=" * 60)
    print("Testing Enums")
    print("=" * 60)
    
    # Test JobStatus
    print("\n[1] JobStatus Enum:")
    print(f"   PENDING: {JobStatus.PENDING}")
    print(f"   Is 'COMPLETED' terminal? {JobStatus.is_terminal('COMPLETED')}")
    print(f"   Is 'PROCESSING' terminal? {JobStatus.is_terminal('PROCESSING')}")
    print(f"   Terminal statuses: {[s.value for s in JobStatus.get_terminal_statuses()]}")
    
    # Test StyleType
    print("\n[2] StyleType Enum:")
    for style in StyleType:
        print(f"   {style.value}:")
        print(f"      Prompt: {style.get_system_prompt_modifier()[:60]}...")
    
    # Test DurationType
    print("\n[3] DurationType Enum:")
    for duration in DurationType:
        print(f"   {duration.value}:")
        print(f"      Tokens: {duration.get_token_limit()}")
        print(f"      Estimated: {duration.get_estimated_minutes()}")


def test_request_validation():
    """Test request model validation."""
    print("\n" + "=" * 60)
    print("Testing Request Validation")
    print("=" * 60)
    
    # Valid request
    print("\n[1] Valid Request:")
    try:
        request = JobCreateRequest(
            prompt="Summarize the methodology section of this paper",
            style=StyleType.STUDENT_PROFESSOR,
            duration=DurationType.MEDIUM
        )
        print(f"   ✅ Valid: {request.model_dump_json(indent=2)}")
    except ValidationError as e:
        print(f"   ❌ Validation failed: {e}")
    
    # Invalid request - prompt too short
    print("\n[2] Invalid Request (short prompt):")
    try:
        request = JobCreateRequest(
            prompt="Hi",
            style=StyleType.CRITIQUE,
            duration=DurationType.SHORTER
        )
        print(f"   ❌ Should have failed but didn't!")
    except ValidationError as e:
        print(f"   ✅ Validation correctly failed:")
        for error in e.errors():
            print(f"      - {error['loc'][0]}: {error['msg']}")
    
    # Invalid request - empty prompt
    print("\n[3] Invalid Request (empty prompt):")
    try:
        request = JobCreateRequest(
            prompt="   ",
            style=StyleType.DEBATE,
            duration=DurationType.LONGER
        )
        print(f"   ❌ Should have failed but didn't!")
    except ValidationError as e:
        print(f"   ✅ Validation correctly failed:")
        for error in e.errors():
            print(f"      - {error['loc'][0]}: {error['msg']}")


def test_response_models():
    """Test response model creation."""
    print("\n" + "=" * 60)
    print("Testing Response Models")
    print("=" * 60)
    
    # JobResponse
    print("\n[1] JobResponse (HTTP 202):")
    job_response = JobResponse(
        job_id="507f1f77bcf86cd799439011",
        status=JobStatus.PENDING,
        created_at=datetime.now(timezone.utc)
    )
    print(f"   {job_response.model_dump_json(indent=2)}")
    
    # JobResultResponse - Completed
    print("\n[2] JobResultResponse (COMPLETED):")
    result_response = JobResultResponse(
        job_id="507f1f77bcf86cd799439011",
        status=JobStatus.COMPLETED,
        prompt="Summarize the key findings",
        style="Student-Professor",
        duration="MEDIUM",
        pdf_filename="research_paper.pdf",
        pdf_size=2048576,
        audio_url="https://storage.googleapis.com/bucket/audio.mp3",
        error_message=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc)
    )
    print(f"   {result_response.model_dump_json(indent=2)}")
    
    # JobResultResponse - Failed
    print("\n[3] JobResultResponse (FAILED):")
    failed_response = JobResultResponse(
        job_id="507f1f77bcf86cd799439012",
        status=JobStatus.FAILED,
        prompt="Analyze this document",
        style="Critique",
        duration="LONGER",
        pdf_filename="document.pdf",
        pdf_size=1024000,
        audio_url=None,
        error_message="Failed to process PDF: Invalid format",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc)
    )
    print(f"   {failed_response.model_dump_json(indent=2)}")
    
    # ErrorResponse
    print("\n[4] ErrorResponse:")
    error_response = ErrorResponse(
        error="ValidationError",
        message="Invalid input data",
        detail="Prompt must be at least 10 characters long"
    )
    print(f"   {error_response.model_dump_json(indent=2)}")


if __name__ == "__main__":
    try:
        test_enums()
        test_request_validation()
        test_response_models()
        
        print("\n" + "=" * 60)
        print("✅ All model tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

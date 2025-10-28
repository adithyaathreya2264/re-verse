"""
Health check and system status routes.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, status

from app.db.mongodb import MongoDB
from app.models.job_model import HealthResponse
from app.utils.logger import logger

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health Check",
    description="Returns API and database health status"
)
async def health_check():
    """
    Comprehensive health check endpoint.
    
    Returns:
        HealthResponse: System status information
    """
    try:
        # Test database connection - FIXED: Use 'is not None' comparison
        db = MongoDB.get_database()
        
        # Verify connection with ping command
        if db is not None:
            db.command("ping")
            db_status = "connected"
        else:
            db_status = "disconnected"
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        timestamp=datetime.now(timezone.utc),
        database=db_status
    )

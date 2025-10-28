"""
RE-VERSE FastAPI Application
Main entry point for the Podcast Audio Generator API.
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.db.mongodb import MongoDB
from app.utils.logger import logger
from app.models.job_model import ErrorResponse, HealthResponse


# ==================== Lifespan Context Manager ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Handles MongoDB connection lifecycle.
    
    Code before yield runs on startup.
    Code after yield runs on shutdown.
    """
    # ========== STARTUP ==========
    logger.info("🚀 Starting RE-VERSE application...")
    
    try:
        # Connect to MongoDB
        await MongoDB.connect_to_database()
        logger.info("✅ Application startup complete")
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        raise
    
    # ========== APPLICATION RUNNING ==========
    yield
    
    # ========== SHUTDOWN ==========
    logger.info("🛑 Shutting down RE-VERSE application...")
    
    try:
        # Close MongoDB connection
        await MongoDB.close_database_connection()
        logger.info("✅ Application shutdown complete")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


# ==================== FastAPI Application ====================

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc",  # ReDoc documentation
    openapi_url="/api/openapi.json"
)


# ==================== Middleware Configuration ====================

# CORS Middleware - Allow frontend to make API requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # List of allowed origins
    allow_credentials=True,  # Allow cookies and authentication headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


# ==================== Exception Handlers ====================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for Pydantic validation errors.
    Returns user-friendly error messages.
    """
    errors = exc.errors()
    error_messages = []
    
    for error in errors:
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_messages.append(f"{field}: {message}")
    
    logger.warning(f"Validation error on {request.url}: {error_messages}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="ValidationError",
            message="Invalid input data",
            detail="; ".join(error_messages)
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Generic exception handler for unexpected errors.
    Prevents exposing internal error details to users.
    """
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred. Please try again later.",
            detail=None  # Don't expose internal error details in production
        ).model_dump()
    )


# ==================== Static Files & Root Route ====================

# Mount static files for frontend (HTML, CSS, JS)
# Must be done AFTER defining API routes to avoid conflicts
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


@app.get("/", include_in_schema=False)
async def serve_frontend():
    """
    Serve the main frontend HTML page.
    This route serves the RE-VERSE web interface.
    """
    return FileResponse("static/index.html")


# ==================== API Routes ====================

# Health check endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health Check",
    description="Check if the API and database are operational"
)
async def health_check():
    """
    Health check endpoint to verify API status.
    Returns system status and database connectivity.
    """
    try:
        # Test database connection - FIXED: Use 'is not None' comparison
        db = MongoDB.get_database()
        
        # Verify the connection is working by pinging
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



# ==================== Application Info ====================

@app.on_event("startup")
async def log_startup_info():
    """Log application information on startup."""
    logger.info("=" * 60)
    logger.info(f"Application: {settings.api_title} v{settings.api_version}")
    logger.info(f"Environment: {settings.log_level.upper()}")
    logger.info(f"API Prefix: {settings.api_v1_prefix}")
    logger.info(f"CORS Origins: {settings.cors_origins_list}")
    logger.info(f"Max File Size: {settings.max_file_size_mb} MB")
    logger.info(f"Allowed File Types: {settings.allowed_file_types_list}")
    logger.info("=" * 60)


# ==================== Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,  # Enable auto-reload for development
        log_level=settings.log_level
    )

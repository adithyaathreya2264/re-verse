"""
Configuration management using Pydantic Settings.
Loads environment variables from .env file.
"""
from typing import List
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes are automatically loaded from .env file or system environment.
    """
    
    # ==================== MongoDB Configuration ====================
    mongodb_uri: str = Field(..., description="MongoDB connection URI")
    mongodb_db_name: str = Field(default="reverse_db", description="MongoDB database name")
    mongodb_collection_jobs: str = Field(default="jobs", description="Jobs collection name")
    
    # ==================== Google Gemini API ====================
    google_api_key: str = Field(..., description="Google Gemini API key")
    
    # ==================== Google Cloud Storage ====================
    gcs_bucket_name: str = Field(..., description="GCS bucket name for audio files")
    gcs_project_id: str = Field(..., description="Google Cloud project ID")
    google_application_credentials: str = Field(
        default="./service-account.json",
        description="Path to GCS service account JSON"
    )
    
    # ==================== API Configuration ====================
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 route prefix")
    api_title: str = Field(default="RE-VERSE API", description="API title")
    api_version: str = Field(default="1.0.0", description="API version")
    api_description: str = Field(
        default="Podcast Audio Generator using AI",
        description="API description"
    )
    
    # ==================== File Upload Configuration ====================
    max_file_size_mb: int = Field(default=50, description="Maximum file upload size in MB")
    allowed_file_types: str = Field(
        default="application/pdf",
        description="Allowed MIME types for upload"
    )
    
    # ==================== Server Configuration ====================
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of workers")
    log_level: str = Field(default="info", description="Logging level")
    
    # ==================== CORS Configuration ====================
    cors_origins: str = Field(
        default="http://localhost:8000,http://127.0.0.1:8000",
        description="Allowed CORS origins (comma-separated)"
    )
    
    # ==================== Audio Generation Settings ====================
    speaker_1_voice: str = Field(default="Kore", description="First speaker voice name")
    speaker_2_voice: str = Field(default="Puck", description="Second speaker voice name")
    
    duration_shorter_tokens: int = Field(default=2000, description="Tokens for SHORTER duration")
    duration_medium_tokens: int = Field(default=4000, description="Tokens for MEDIUM duration")
    duration_longer_tokens: int = Field(default=8000, description="Tokens for LONGER duration")
    
    signed_url_expiration_hours: int = Field(
        default=168,
        description="GCS signed URL expiration in hours (default: 7 days)"
    )
    
    # ==================== Pydantic Settings Configuration ====================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ==================== Validators ====================
    @validator("max_file_size_mb")
    def validate_file_size(cls, v):
        """Ensure max file size is reasonable."""
        if v <= 0 or v > 500:
            raise ValueError("max_file_size_mb must be between 1 and 500")
        return v
    
    @validator("port")
    def validate_port(cls, v):
        """Ensure port is in valid range."""
        if v < 1024 or v > 65535:
            raise ValueError("port must be between 1024 and 65535")
        return v
    
    # ==================== Computed Properties ====================
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert max file size from MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Convert comma-separated file types to list."""
        return [ft.strip() for ft in self.allowed_file_types.split(",")]
    
    def get_duration_tokens(self, duration_type: str) -> int:
        """
        Get token limit based on duration type.
        
        Args:
            duration_type: One of "SHORTER", "MEDIUM", "LONGER"
            
        Returns:
            Token limit for the specified duration
        """
        duration_map = {
            "SHORTER": self.duration_shorter_tokens,
            "MEDIUM": self.duration_medium_tokens,
            "LONGER": self.duration_longer_tokens
        }
        return duration_map.get(duration_type.upper(), self.duration_medium_tokens)


# ==================== Global Settings Instance ====================
settings = Settings()

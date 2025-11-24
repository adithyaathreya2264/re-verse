"""
Application configuration using Pydantic Settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ==================== API Configuration ====================
    api_title: str = "RE-VERSE - AI Podcast Generator"
    api_version: str = "1.0.0"
    api_description: str = "Transform PDF documents into engaging AI-generated podcasts"
    api_v1_prefix: str = "/api/v1"
    host: str = "127.0.0.1"
    port: int = 8000
    
    # ==================== MongoDB Configuration ====================
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "reverse_db"
    mongodb_collection_jobs: str = "jobs"
    
    # ==================== AI Model Configuration ====================
    ai_provider: str = "groq"  # "groq" or "gemini"
    groq_api_key: str = ""
    google_api_key: str = ""
    
    # ==================== Google Cloud Storage Configuration ====================
    gcs_project_id: str = "your-project-id"
    gcs_bucket_name: str = "re-verse-audio"
    gcs_credentials_path: str = "./re-verse-476206-4e8cc369c480.json"
    gcs_signed_url_expiration_days: int = 7
    
    # ==================== File Upload Configuration ====================
    max_file_size_mb: int = 50
    allowed_file_types: str = "application/pdf"
    
    # ==================== Logging Configuration ====================
    log_level: str = "info"
    
    # ==================== CORS Configuration ====================
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    
    # ==================== TTS Voice Configuration ====================
    speaker_1_voice: str = "Kore"
    speaker_2_voice: str = "Puck"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ==================== Helper Properties ====================
    
    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        return [ft.strip() for ft in self.allowed_file_types.split(",")]
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # ==================== Duration/Token Configuration ====================
    
    def get_duration_tokens(self, duration: str) -> int:
        """Get max output tokens based on duration."""
        token_map = {
            "SHORTER": 2000,   # Llama can handle more
            "MEDIUM": 3000,
            "LONGER": 4000
        }
        return token_map.get(duration, 3000)
    
    def get_dialogue_turns(self, duration: str) -> int:
        """Get target number of dialogue turns."""
        turns_map = {
            "SHORTER": 10,
            "MEDIUM": 15,
            "LONGER": 20
        }
        return turns_map.get(duration, 15)
    
    def get_pdf_char_limit(self, duration: str) -> int:
        """Get PDF character limit for context."""
        char_limit_map = {
            "SHORTER": 5000,
            "MEDIUM": 8000,
            "LONGER": 12000
        }
        return char_limit_map.get(duration, 8000)
    
    # ==================== GCS Helper Methods ====================
    
    def get_gcs_blob_name(self, job_id: str) -> str:
        return f"podcasts/{job_id}.mp3"
    
    def get_signed_url_expiration_seconds(self) -> int:
        return self.gcs_signed_url_expiration_days * 24 * 60 * 60


settings = Settings()


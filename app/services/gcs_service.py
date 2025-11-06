"""
Google Cloud Storage service for audio file management.
Handles upload, download, and signed URL generation.
"""
from datetime import timedelta
from typing import Optional
from google.cloud import storage
from google.oauth2 import service_account

from app.core.config import settings
from app.utils.logger import logger


class GCSService:
    """Google Cloud Storage service singleton."""
    
    _client: Optional[storage.Client] = None
    _bucket: Optional[storage.Bucket] = None
    
    @classmethod
    def initialize(cls):
        """Initialize GCS client and bucket."""
        try:
            logger.info("☁️ Initializing Google Cloud Storage...")
            
            # Load credentials from JSON file
            credentials = service_account.Credentials.from_service_account_file(
                settings.gcs_credentials_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            
            # Create storage client
            cls._client = storage.Client(
                project=settings.gcs_project_id,
                credentials=credentials
            )
            
            # Get or create bucket
            cls._bucket = cls._client.bucket(settings.gcs_bucket_name)
            
            # Verify bucket exists
            if not cls._bucket.exists():
                logger.warning(f"⚠️ Bucket '{settings.gcs_bucket_name}' does not exist. Creating...")
                cls._bucket.create(location="US")
                logger.info(f"✅ Bucket created: {settings.gcs_bucket_name}")
            else:
                logger.info(f"✅ Connected to GCS bucket: {settings.gcs_bucket_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize GCS: {e}")
            raise
    
    @classmethod
    def get_client(cls) -> storage.Client:
        """Get GCS client instance."""
        if cls._client is None:
            cls.initialize()
        return cls._client
    
    @classmethod
    def get_bucket(cls) -> storage.Bucket:
        """Get GCS bucket instance."""
        if cls._bucket is None:
            cls.initialize()
        return cls._bucket


async def upload_audio_to_gcs(
    audio_bytes: bytes,
    job_id: str,
    content_type: str = "audio/mpeg"
) -> str:
    """
    Upload audio file to Google Cloud Storage.
    
    Args:
        audio_bytes: Audio file contents as bytes
        job_id: Unique job identifier
        content_type: MIME type of audio file
        
    Returns:
        GCS blob path (e.g., "podcasts/job123.mp3")
        
    Raises:
        Exception: If upload fails
    """
    try:
        logger.info(f"☁️ Uploading audio to GCS for job: {job_id}")
        
        # Get bucket
        bucket = GCSService.get_bucket()
        
        # Generate blob name
        blob_name = settings.get_gcs_blob_name(job_id)
        
        # Create blob
        blob = bucket.blob(blob_name)
        
        # Set metadata
        blob.metadata = {
            "job_id": job_id,
            "content_type": content_type,
            "uploaded_by": "re-verse-api"
        }
        
        # Upload audio
        blob.upload_from_string(
            audio_bytes,
            content_type=content_type
        )
        
        logger.info(f"✅ Audio uploaded to GCS: {blob_name} ({len(audio_bytes)} bytes)")
        
        return blob_name
        
    except Exception as e:
        logger.error(f"❌ GCS upload failed: {e}")
        raise Exception(f"Failed to upload audio to GCS: {str(e)}")


async def generate_signed_url(blob_name: str) -> str:
    """
    Generate a signed URL for secure audio access.
    
    Args:
        blob_name: GCS blob path
        
    Returns:
        Signed URL (valid for configured duration)
        
    Raises:
        Exception: If URL generation fails
    """
    try:
        logger.info(f"🔗 Generating signed URL for: {blob_name}")
        
        # Get bucket and blob
        bucket = GCSService.get_bucket()
        blob = bucket.blob(blob_name)
        
        # Generate signed URL
        expiration = timedelta(seconds=settings.get_signed_url_expiration_seconds())
        
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=expiration,
            method="GET"
        )
        
        logger.info(f"✅ Signed URL generated (expires in {settings.gcs_signed_url_expiration_days} days)")
        
        return signed_url
        
    except Exception as e:
        logger.error(f"❌ Signed URL generation failed: {e}")
        raise Exception(f"Failed to generate signed URL: {str(e)}")


async def delete_audio_from_gcs(blob_name: str) -> bool:
    """
    Delete audio file from GCS.
    
    Args:
        blob_name: GCS blob path
        
    Returns:
        True if deleted successfully
    """
    try:
        logger.info(f"🗑️ Deleting audio from GCS: {blob_name}")
        
        bucket = GCSService.get_bucket()
        blob = bucket.blob(blob_name)
        
        if blob.exists():
            blob.delete()
            logger.info(f"✅ Audio deleted from GCS: {blob_name}")
            return True
        else:
            logger.warning(f"⚠️ Blob not found: {blob_name}")
            return False
        
    except Exception as e:
        logger.error(f"❌ GCS deletion failed: {e}")
        return False


async def check_audio_exists(blob_name: str) -> bool:
    """
    Check if audio file exists in GCS.
    
    Args:
        blob_name: GCS blob path
        
    Returns:
        True if file exists
    """
    try:
        bucket = GCSService.get_bucket()
        blob = bucket.blob(blob_name)
        return blob.exists()
    except Exception as e:
        logger.error(f"Error checking audio existence: {e}")
        return False

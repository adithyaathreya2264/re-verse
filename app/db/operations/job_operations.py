"""
Database operations for job management.
Provides async CRUD functions for the jobs collection.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId # type: ignore
from pymongo.errors import PyMongoError # type: ignore

from app.db.mongodb import MongoDB
from app.core.config import settings
from app.utils.logger import logger


# ==================== Helper Functions ====================

def serialize_job_document(job_doc: Dict) -> Dict:
    """
    Convert MongoDB document to JSON-serializable format.
    
    Args:
        job_doc: MongoDB document with ObjectId
        
    Returns:
        Dictionary with _id converted to string
    """
    if job_doc and "_id" in job_doc:
        job_doc["_id"] = str(job_doc["_id"])
    return job_doc


def validate_object_id(job_id: str) -> bool:
    """
    Validate if string is a valid MongoDB ObjectId.
    
    Args:
        job_id: Job ID string
        
    Returns:
        True if valid ObjectId format
    """
    return ObjectId.is_valid(job_id)


# ==================== CRUD Operations ====================

async def create_new_job(job_data: Dict[str, Any]) -> str:
    """
    Create a new job document in the database.
    
    Args:
        job_data: Dictionary containing job information with keys:
            - prompt: str (user's text prompt)
            - style: str (conversational style)
            - duration: str (duration preference)
            - pdf_filename: str (original filename)
            - pdf_size: int (file size in bytes)
            - status: str (initial status, typically "PENDING")
            
    Returns:
        str: The created job's ID as string
        
    Raises:
        Exception: If database operation fails
    """
    try:
        collection = MongoDB.get_collection(settings.mongodb_collection_jobs)
        
        # Add timestamps
        current_time = datetime.now(timezone.utc)
        job_document = {
            **job_data,
            "created_at": current_time,
            "updated_at": current_time,
            "completed_at": None,
            "audio_url": None,
            "error_message": None
        }
        
        # Insert document
        result = collection.insert_one(job_document)
        job_id = str(result.inserted_id)
        
        logger.info(f"✅ Created new job with ID: {job_id}")
        return job_id
        
    except PyMongoError as e:
        logger.error(f"❌ Database error creating job: {e}")
        raise Exception(f"Failed to create job: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error creating job: {e}")
        raise


async def update_job_status(
    job_id: str,
    status: str,
    **kwargs
) -> bool:
    """
    Update job status and optional additional fields.
    
    Args:
        job_id: Job ID string
        status: New status value (e.g., "PROCESSING", "COMPLETED", "FAILED")
        **kwargs: Additional fields to update:
            - audio_url: str (URL to generated audio)
            - error_message: str (error details if failed)
            - completed_at: datetime (completion timestamp)
            
    Returns:
        bool: True if update successful, False otherwise
        
    Raises:
        ValueError: If job_id is invalid
    """
    try:
        # Validate ObjectId
        if not validate_object_id(job_id):
            raise ValueError(f"Invalid job ID format: {job_id}")
        
        collection = MongoDB.get_collection(settings.mongodb_collection_jobs)
        
        # Build update document
        update_doc = {
            "status": status,
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Add optional fields
        for key, value in kwargs.items():
            if value is not None:
                update_doc[key] = value
        
        # Set completed_at for terminal statuses
        if status in ["COMPLETED", "FAILED"] and "completed_at" not in update_doc:
            update_doc["completed_at"] = datetime.now(timezone.utc)
        
        # Update document
        result = collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": update_doc}
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Updated job {job_id} to status: {status}")
            return True
        else:
            logger.warning(f"⚠️ No document updated for job ID: {job_id}")
            return False
            
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise
    except PyMongoError as e:
        logger.error(f"❌ Database error updating job: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error updating job: {e}")
        return False


async def get_job_result(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve complete job information by ID.
    
    Args:
        job_id: Job ID string
        
    Returns:
        Dictionary containing job data, or None if not found
        
    Raises:
        ValueError: If job_id is invalid
    """
    try:
        # Validate ObjectId
        if not validate_object_id(job_id):
            raise ValueError(f"Invalid job ID format: {job_id}")
        
        collection = MongoDB.get_collection(settings.mongodb_collection_jobs)
        
        # Find document
        job_doc = collection.find_one({"_id": ObjectId(job_id)})
        
        if job_doc:
            logger.info(f"✅ Retrieved job: {job_id}")
            return serialize_job_document(job_doc)
        else:
            logger.warning(f"⚠️ Job not found: {job_id}")
            return None
            
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise
    except PyMongoError as e:
        logger.error(f"❌ Database error retrieving job: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error retrieving job: {e}")
        return None


async def get_jobs_by_status(status: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve jobs filtered by status.
    
    Args:
        status: Job status to filter by
        limit: Maximum number of jobs to return
        
    Returns:
        List of job documents
    """
    try:
        collection = MongoDB.get_collection(settings.mongodb_collection_jobs)
        
        cursor = collection.find({"status": status}).sort("created_at", -1).limit(limit)
        jobs = [serialize_job_document(job) for job in cursor]
        
        logger.info(f"✅ Retrieved {len(jobs)} jobs with status: {status}")
        return jobs
        
    except PyMongoError as e:
        logger.error(f"❌ Database error retrieving jobs by status: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Unexpected error retrieving jobs: {e}")
        return []


async def delete_job(job_id: str) -> bool:
    """
    Delete a job document (optional - for cleanup).
    
    Args:
        job_id: Job ID string
        
    Returns:
        bool: True if deleted, False otherwise
    """
    try:
        if not validate_object_id(job_id):
            raise ValueError(f"Invalid job ID format: {job_id}")
        
        collection = MongoDB.get_collection(settings.mongodb_collection_jobs)
        result = collection.delete_one({"_id": ObjectId(job_id)})
        
        if result.deleted_count > 0:
            logger.info(f"✅ Deleted job: {job_id}")
            return True
        else:
            logger.warning(f"⚠️ Job not found for deletion: {job_id}")
            return False
            
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise
    except PyMongoError as e:
        logger.error(f"❌ Database error deleting job: {e}")
        return False

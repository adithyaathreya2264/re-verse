"""
MongoDB operations for job management.
"""
from typing import Dict, Optional
from datetime import datetime, timezone
from bson import ObjectId

from app.db.mongodb import MongoDB
from app.core.config import settings
from app.utils.logger import logger
from fastapi import APIRouter, HTTPException, Query
from app.utils.logger import logger

router = APIRouter()
async def create_new_job(job_data: Dict) -> Optional[str]:
    """
    Create a new job document in MongoDB.
    
    Args:
        job_data: Dictionary containing job information
        
    Returns:
        Job ID as string, or None if creation fails
    """
    try:
        # Get database
        db = MongoDB.get_database()
        if db is None:
            logger.error("❌ Database not connected")
            return None
        
        # Get collection
        collection = db[settings.mongodb_collection_jobs]
        
        # Add timestamps
        now = datetime.now(timezone.utc)
        job_document = {
            **job_data,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
            "audio_url": None,
            "error_message": None
        }
        
        # Insert document with AWAIT
        result = await collection.insert_one(job_document)
        job_id = str(result.inserted_id)
        
        logger.info(f"✅ Job created in database: {job_id}")
        return job_id
        
    except Exception as e:
        logger.error(f"❌ Failed to create job: {e}")
        return None


async def get_job_result(job_id: str) -> Optional[Dict]:
    """
    Get job document from MongoDB by ID.
    
    Args:
        job_id: Job ID as string
        
    Returns:
        Job document as dictionary, or None if not found
    """
    try:
        # Get database
        db = MongoDB.get_database()
        if db is None:
            logger.error("❌ Database not connected")
            return None
        
        # Get collection
        collection = db[settings.mongodb_collection_jobs]
        
        # Find job with AWAIT
        job = await collection.find_one({"_id": ObjectId(job_id)})
        
        if job:
            # Convert ObjectId to string for JSON serialization
            job["_id"] = str(job["_id"])
            return job
        
        logger.warning(f"⚠️ Job not found: {job_id}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Failed to get job: {e}")
        return None


async def update_job_status(
    job_id: str,
    status: str,
    audio_url: Optional[str] = None,
    error_message: Optional[str] = None,
    completed_at: Optional[datetime] = None
) -> bool:
    """
    Update job status and related fields.
    
    Args:
        job_id: Job ID as string
        status: New status value
        audio_url: Audio URL (optional)
        error_message: Error message (optional)
        completed_at: Completion timestamp (optional)
        
    Returns:
        True if update successful, False otherwise
    """
    try:
        # Get database
        db = MongoDB.get_database()
        if db is None:
            logger.error("❌ Database not connected")
            return False
        
        # Get collection
        collection = db[settings.mongodb_collection_jobs]
        
        # Build update document
        update_doc = {
            "status": status,
            "updated_at": datetime.now(timezone.utc)
        }
        
        if audio_url is not None:
            update_doc["audio_url"] = audio_url
        
        if error_message is not None:
            update_doc["error_message"] = error_message
        
        if completed_at is not None:
            update_doc["completed_at"] = completed_at
        
        # Update job with AWAIT
        result = await collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": update_doc}
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Job updated: {job_id} -> {status}")
            return True
        else:
            logger.warning(f"⚠️ Job not modified: {job_id}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Failed to update job: {e}")
        return False


async def delete_job(job_id: str) -> bool:
    """
    Delete job document from MongoDB.
    
    Args:
        job_id: Job ID as string
        
    Returns:
        True if deletion successful, False otherwise
    """
    try:
        # Get database
        db = MongoDB.get_database()
        if db is None:
            logger.error("❌ Database not connected")
            return False
        
        # Get collection
        collection = db[settings.mongodb_collection_jobs]
        
        # Delete job with AWAIT
        result = await collection.delete_one({"_id": ObjectId(job_id)})
        
        if result.deleted_count > 0:
            logger.info(f"✅ Job deleted: {job_id}")
            return True
        else:
            logger.warning(f"⚠️ Job not found for deletion: {job_id}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Failed to delete job: {e}")
        return False

"""
Test script for MongoDB database operations.
Run: python test_database.py
"""
import asyncio
from datetime import datetime
from app.db.mongodb import MongoDB
from app.db.operations.job_operations import (
    create_new_job,
    update_job_status,
    get_job_result,
    get_jobs_by_status
)


async def test_database_operations():
    """Test all database CRUD operations."""
    
    print("=" * 60)
    print("RE-VERSE Database Operations Test")
    print("=" * 60)
    
    try:
        # Step 1: Connect to database
        print("\n[1] Connecting to MongoDB...")
        await MongoDB.connect_to_database()
        
        # Step 2: Create a test job
        print("\n[2] Creating a test job...")
        test_job_data = {
            "prompt": "Summarize this PDF in a student-professor conversation",
            "style": "Student-Professor",
            "duration": "MEDIUM",
            "pdf_filename": "test_document.pdf",
            "pdf_size": 1024000,
            "status": "PENDING"
        }
        
        job_id = await create_new_job(test_job_data)
        print(f"✅ Created job with ID: {job_id}")
        
        # Step 3: Retrieve the job
        print(f"\n[3] Retrieving job {job_id}...")
        job = await get_job_result(job_id)
        if job:
            print(f"✅ Job found:")
            print(f"   Status: {job['status']}")
            print(f"   Prompt: {job['prompt']}")
            print(f"   Created: {job['created_at']}")
        
        # Step 4: Update job status to PROCESSING
        print(f"\n[4] Updating job status to PROCESSING...")
        success = await update_job_status(job_id, "PROCESSING")
        if success:
            print("✅ Status updated successfully")
        
        # Step 5: Update job status to COMPLETED with audio URL
        print(f"\n[5] Completing job with audio URL...")
        success = await update_job_status(
            job_id,
            "COMPLETED",
            audio_url="https://storage.googleapis.com/bucket/audio.mp3"
        )
        if success:
            print("✅ Job completed successfully")
        
        # Step 6: Retrieve updated job
        print(f"\n[6] Retrieving completed job...")
        completed_job = await get_job_result(job_id)
        if completed_job:
            print(f"✅ Final job state:")
            print(f"   Status: {completed_job['status']}")
            print(f"   Audio URL: {completed_job['audio_url']}")
            print(f"   Completed: {completed_job['completed_at']}")
        
        # Step 7: Query jobs by status
        print(f"\n[7] Querying all COMPLETED jobs...")
        completed_jobs = await get_jobs_by_status("COMPLETED", limit=5)
        print(f"✅ Found {len(completed_jobs)} completed jobs")
        
        print("\n" + "=" * 60)
        print("✅ All database tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
    
    finally:
        # Close connection
        await MongoDB.close_database_connection()


if __name__ == "__main__":
    asyncio.run(test_database_operations())

"""
Test script for job API endpoints.
Run: python test_job_api.py (with server running)
"""
import requests
import time

API_BASE = "http://localhost:8000/api/v1"

def test_job_creation():
    """Test job creation endpoint."""
    print("=" * 60)
    print("Testing Job Creation")
    print("=" * 60)
    
    # Prepare test data
    files = {'file': ('test.pdf', b'%PDF-1.4 fake pdf content', 'application/pdf')}
    data = {
        'prompt': 'Summarize the key findings of this research paper',
        'style': 'Student-Professor',
        'duration': 'MEDIUM'
    }
    
    # Make request
    response = requests.post(f"{API_BASE}/generate-job", files=files, data=data)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 202:
        return response.json()['job_id']
    return None

def test_job_status(job_id):
    """Test job status endpoint."""
    print("\n" + "=" * 60)
    print("Testing Job Status Polling")
    print("=" * 60)
    
    max_attempts = 10
    for attempt in range(max_attempts):
        response = requests.get(f"{API_BASE}/job/{job_id}")
        data = response.json()
        
        print(f"\nAttempt {attempt + 1}/{max_attempts}")
        print(f"Status: {data['status']}")
        
        if data['status'] in ['COMPLETED', 'FAILED']:
            print(f"\nFinal Result:")
            print(f"  Audio URL: {data.get('audio_url')}")
            print(f"  Error: {data.get('error_message')}")
            break
        
        time.sleep(2)

if __name__ == "__main__":
    try:
        # Test job creation
        job_id = test_job_creation()
        
        if job_id:
            # Test status polling
            test_job_status(job_id)
        
        print("\n" + "=" * 60)
        print("✅ Tests completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

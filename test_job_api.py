"""
Test script for job API endpoints.
Run: python test_job_api.py (with server running)
"""
import requests
import time
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

API_BASE = "http://localhost:8000/api/v1"


def create_test_pdf() -> bytes:
    """
    Create a valid PDF with actual content for testing.
    
    Returns:
        PDF bytes that can be parsed by PyPDF2
    """
    buffer = BytesIO()
    
    # Create PDF with reportlab
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Add title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Test Research Paper")
    
    # Add content
    c.setFont("Helvetica", 12)
    y_position = 700
    
    content = [
        "Abstract",
        "This is a test research paper about artificial intelligence and machine learning.",
        "",
        "Introduction",
        "Artificial Intelligence (AI) has transformed various industries over the past decade.",
        "Machine Learning, a subset of AI, enables computers to learn from data without",
        "being explicitly programmed. This paper explores the fundamental concepts and",
        "applications of modern AI systems.",
        "",
        "Key Findings",
        "1. Deep learning models have achieved human-level performance in image recognition",
        "2. Natural language processing has improved significantly with transformer architectures",
        "3. Reinforcement learning shows promise in robotics and game playing",
        "",
        "Conclusion",
        "AI and ML continue to advance rapidly, opening new possibilities for innovation.",
        "Future research should focus on explainability, fairness, and ethical considerations."
    ]
    
    for line in content:
        c.drawString(100, y_position, line)
        y_position -= 20
        if y_position < 100:  # Start new page if needed
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = 750
    
    c.save()
    
    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


def test_job_creation():
    """Test job creation endpoint."""
    print("=" * 60)
    print("Testing Job Creation")
    print("=" * 60)
    
    # Create a real PDF
    print("\n📄 Creating test PDF...")
    pdf_bytes = create_test_pdf()
    print(f"✅ PDF created: {len(pdf_bytes)} bytes")
    
    # Prepare test data
    files = {
        'file': ('test_research_paper.pdf', pdf_bytes, 'application/pdf')
    }
    data = {
        'prompt': 'Summarize the key findings and explain the main concepts of this AI research paper',
        'style': 'Student-Professor',
        'duration': 'MEDIUM'
    }
    
    # Make request
    print("\n🚀 Sending job creation request...")
    response = requests.post(f"{API_BASE}/generate-job", files=files, data=data)
    
    print(f"\n📊 Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"📦 Response: {response_data}")
    except:
        print(f"⚠️ Response: {response.text}")
        return None
    
    if response.status_code == 202:
        print("\n✅ Job created successfully!")
        return response_data.get('job_id')
    else:
        print("\n❌ Job creation failed!")
        return None


def test_job_status(job_id):
    """Test job status endpoint."""
    print("\n" + "=" * 60)
    print("Testing Job Status Polling")
    print("=" * 60)
    
    max_attempts = 30  # Increased to 30 for AI processing time
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{API_BASE}/job/{job_id}")
            data = response.json()
            
            print(f"\n⏱️  Attempt {attempt + 1}/{max_attempts}")
            print(f"   Status: {data['status']}")
            
            if data['status'] == 'PROCESSING':
                print(f"   ⚙️  Processing in progress...")
            
            if data['status'] in ['COMPLETED', 'FAILED']:
                print(f"\n{'='*60}")
                print("Final Result")
                print(f"{'='*60}")
                print(f"Status: {data['status']}")
                print(f"Audio URL: {data.get('audio_url')}")
                
                if data['status'] == 'COMPLETED':
                    print(f"\n✅ SUCCESS! Audio generated successfully!")
                    print(f"\n📊 Job Details:")
                    print(f"   Title: (Check server logs)")
                    print(f"   Created: {data.get('created_at')}")
                    print(f"   Completed: {data.get('completed_at')}")
                elif data['status'] == 'FAILED':
                    print(f"\n❌ FAILED!")
                    print(f"   Error: {data.get('error_message')}")
                
                break
            
            time.sleep(3)  # Wait 3 seconds between polls
            
        except Exception as e:
            print(f"\n❌ Error during polling: {e}")
            break
    else:
        print(f"\n⚠️  Timeout: Job still processing after {max_attempts * 3} seconds")


if __name__ == "__main__":
    print("\n" + "🎙️  RE-VERSE API Test Suite ".center(60, "="))
    print()
    
    try:
        # Check if reportlab is installed
        try:
            import reportlab
        except ImportError:
            print("❌ Error: reportlab not installed")
            print("📦 Install it with: pip install reportlab")
            exit(1)
        
        # Test job creation
        job_id = test_job_creation()
        
        if job_id:
            # Test status polling
            test_job_status(job_id)
        
        print("\n" + "=" * 60)
        print("✅ Test Suite Completed!")
        print("=" * 60)
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

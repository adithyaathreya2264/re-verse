"""
Test script to verify configuration setup.
Run: python test_config.py
"""
from app.core.config import settings


def test_config():
    """Test that all required settings are loaded."""
    print("=" * 50)
    print("RE-VERSE Configuration Test")
    print("=" * 50)
    
    # Test MongoDB settings
    print(f"\n✓ MongoDB URI: {settings.mongodb_uri[:20]}...")
    print(f"✓ Database Name: {settings.mongodb_db_name}")
    
    # Test API settings
    print(f"\n✓ API Title: {settings.api_title}")
    print(f"✓ API Version: {settings.api_version}")
    print(f"✓ API Prefix: {settings.api_v1_prefix}")
    
    # Test file upload settings
    print(f"\n✓ Max File Size: {settings.max_file_size_mb} MB")
    print(f"✓ Max File Size (bytes): {settings.max_file_size_bytes}")
    print(f"✓ Allowed File Types: {settings.allowed_file_types_list}")
    
    # Test CORS settings
    print(f"\n✓ CORS Origins: {settings.cors_origins_list}")
    
    # Test audio settings
    print(f"\n✓ Speaker 1 Voice: {settings.speaker_1_voice}")
    print(f"✓ Speaker 2 Voice: {settings.speaker_2_voice}")
    
    # Test duration token mapping
    print(f"\n✓ SHORTER duration tokens: {settings.get_duration_tokens('SHORTER')}")
    print(f"✓ MEDIUM duration tokens: {settings.get_duration_tokens('MEDIUM')}")
    print(f"✓ LONGER duration tokens: {settings.get_duration_tokens('LONGER')}")
    
    print("\n" + "=" * 50)
    print("✅ Configuration loaded successfully!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        test_config()
    except Exception as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease check your .env file and ensure all required variables are set.")

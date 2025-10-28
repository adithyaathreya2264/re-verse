"""Test pymongo and bson imports."""
try:
    from bson import ObjectId
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError, ConnectionFailure
    
    print("✅ All imports successful!")
    print(f"   - ObjectId: {ObjectId}")
    print(f"   - MongoClient: {MongoClient}")
    print(f"   - PyMongoError: {PyMongoError}")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")

"""
MongoDB database connection and management.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import asyncio

from app.core.config import settings
from app.utils.logger import logger


class MongoDB:
    """MongoDB database connection manager."""
    client: AsyncIOMotorClient = None
    database = None


async def connect_to_database(max_retries: int = 3):
    """
    Connect to MongoDB database with retry logic.
    
    Args:
        max_retries: Maximum number of connection attempts
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"🚀 Connecting to MongoDB (attempt {attempt}/{max_retries})...")
            logger.info(f"MongoDB URI: {settings.mongodb_uri[:50]}...")
            
            # Create MongoDB client
            MongoDB.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=15000,
                connectTimeoutMS=15000,
                socketTimeoutMS=15000,
                maxPoolSize=10,
                minPoolSize=1
            )
            
            # Get database instance
            MongoDB.database = MongoDB.client[settings.mongodb_db_name]
            
            # Test the connection
            await MongoDB.client.admin.command('ping')
            
            logger.info(f"✅ Connected to MongoDB: {settings.mongodb_db_name}")
            return
            
        except Exception as e:
            logger.error(f"❌ Connection attempt {attempt} failed: {e}")
            
            if attempt < max_retries:
                wait_time = attempt * 2
                logger.info(f"⏳ Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ Failed to connect after {max_retries} attempts")
                logger.warning("⚠️ Application will start without database connection")
                MongoDB.database = None


async def disconnect_from_database():
    """Disconnect from MongoDB database."""
    if MongoDB.client:
        MongoDB.client.close()
        logger.info("✅ Disconnected from MongoDB")


def get_database():
    """
    Get the database instance.
    
    Returns:
        Database instance or None if not connected
    """
    if MongoDB.database is None:
        logger.warning("⚠️ Database not connected. Call connect_to_database() first.")
        return None
    return MongoDB.database


def get_collection(collection_name: str):
    """
    Get a MongoDB collection by name.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Collection instance or None if database not connected
    """
    db = get_database()
    if db is None:
        logger.error(f"❌ Cannot get collection '{collection_name}': Database not connected")
        return None
    
    return db[collection_name]


# Add these methods to the MongoDB class
MongoDB.get_database = staticmethod(get_database)
MongoDB.get_collection = staticmethod(get_collection)

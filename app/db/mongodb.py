"""
MongoDB connection management using PyMongo.
Handles database connection lifecycle with FastAPI lifespan events.
"""
from typing import Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.core.config import settings
from app.utils.logger import logger


class MongoDB:
    """
    MongoDB connection manager with singleton pattern.
    """
    
    client: Optional[MongoClient] = None
    database = None
    
    @classmethod
    async def connect_to_database(cls):
        """
        Establish connection to MongoDB.
        Called during application startup.
        """
        try:
            logger.info("Connecting to MongoDB...")
            logger.info(f"MongoDB URI: {settings.mongodb_uri[:30]}...")
            
            # Create MongoDB client with timeout settings
            cls.client = MongoClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                retryWrites=True,
                w="majority",
                connect=False  # Don't connect immediately, connect on first operation
            )
            
            # Test the connection
            cls.client.admin.command('ping')
            logger.info("✅ Successfully connected to MongoDB!")
            
            # Get database instance
            cls.database = cls.client[settings.mongodb_db_name]
            logger.info(f"Using database: {settings.mongodb_db_name}")
            
            # Ensure indexes are created
            await cls._create_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            logger.error("Common fixes:")
            logger.error("1. Check if MongoDB is running (local) or accessible (Atlas)")
            logger.error("2. Verify your MONGODB_URI in .env file")
            logger.error("3. For Atlas: Check Network Access whitelist")
            logger.error("4. For Local: Run 'mongod' to start MongoDB")
            # Don't raise - let app start but mark database as unavailable
            cls.database = None
        except Exception as e:
            logger.error(f"❌ Unexpected error during MongoDB connection: {e}")
            cls.database = None
    
    @classmethod
    async def close_database_connection(cls):
        """
        Close MongoDB connection.
        Called during application shutdown.
        """
        try:
            if cls.client:
                logger.info("Closing MongoDB connection...")
                cls.client.close()
                logger.info("✅ MongoDB connection closed successfully")
        except Exception as e:
            logger.error(f"❌ Error closing MongoDB connection: {e}")
    
    @classmethod
    async def _create_indexes(cls):
        """
        Create necessary database indexes for optimal query performance.
        """
        try:
            if cls.database is None:
                return
                
            jobs_collection = cls.database[settings.mongodb_collection_jobs]
            
            # Index for job status queries
            jobs_collection.create_index("status")
            
            # Compound index for filtering by status and creation time
            jobs_collection.create_index([("status", 1), ("created_at", -1)])
            
            # Index for user-based queries (if implementing user authentication)
            jobs_collection.create_index("user_id", sparse=True)
            
            logger.info("✅ Database indexes created successfully")
        except Exception as e:
            logger.warning(f"⚠️ Error creating indexes: {e}")
    
    @classmethod
    def get_database(cls):
        """
        Get the database instance.
        
        Returns:
            Database instance or None if not connected
        """
        if cls.database is None:
            logger.warning("⚠️ Database not connected. Call connect_to_database() first.")
        return cls.database
    
    @classmethod
    def get_collection(cls, collection_name: str):
        """
        Get a specific collection from the database.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection instance or None
        """
        db = cls.get_database()
        if db is not None:
            return db[collection_name]
        return None


# Dependency function for FastAPI routes
def get_database():
    """
    FastAPI dependency to get database instance.
    """
    return MongoDB.get_database()

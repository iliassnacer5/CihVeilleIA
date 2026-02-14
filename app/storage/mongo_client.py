import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

logger = logging.getLogger(__name__)

class MongoClient:
    _instance: Optional[AsyncIOMotorClient] = None

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        if cls._instance is None:
            logger.info("Initializing global AsyncIOMotorClient...")
            cls._instance = AsyncIOMotorClient(
                settings.mongodb_uri, 
                serverSelectionTimeoutMS=5000
            )
        return cls._instance

    @classmethod
    async def close_client(cls):
        if cls._instance:
            logger.info("Closing global AsyncIOMotorClient...")
            cls._instance.close()
            cls._instance = None

def get_db():
    client = MongoClient.get_client()
    return client[settings.mongodb_db_name]

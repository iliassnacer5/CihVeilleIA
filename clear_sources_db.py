from pymongo import MongoClient
from app.config.settings import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_sources_collection():
    """Drops the sources collection from MongoDB."""
    try:
        client = MongoClient(settings.mongodb_uri)
        db = client[settings.mongodb_db_name]
        
        # Check if collection exists
        if "sources" in db.list_collection_names():
            db["sources"].drop()
            logger.info(f"Collection 'sources' dropped from database '{settings.mongodb_db_name}'.")
        else:
            logger.info(f"Collection 'sources' does not exist in database '{settings.mongodb_db_name}'.")
            
        # Verify it's empty
        count = db["sources"].count_documents({})
        logger.info(f"Remaining documents in 'sources': {count}")

    except Exception as e:
        logger.error(f"Error clearing sources: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    clear_sources_collection()

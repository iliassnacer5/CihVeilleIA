from app.storage.mongo_store import MongoSourceStore
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_sources():
    """Drops the old sources and initializes new ones from the registry."""
    try:
        store = MongoSourceStore()
        # Drop the collection (manual drop via internal client if store doesn't expose it)
        store._collection.drop()
        logger.info("Existing sources collection dropped.")
        
        # Re-initialize from registry
        store.init_static_sources()
        logger.info("Sources re-initialized from registry.")
        
        # Verify
        sources = store.list_sources()
        logger.info(f"Currently active sources in DB: {len(sources)}")
        for s in sources:
            logger.info(f" - {s['name']} ({s['id']})")

    except Exception as e:
        logger.error(f"Error syncing sources: {e}")

if __name__ == "__main__":
    sync_sources()

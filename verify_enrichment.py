from app.scraping.orchestrator import ScrapingOrchestrator
from app.storage.mongo_store import MongoSourceStore
from app.storage.mongo_store import MongoEnrichedDocumentStore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_enrichment():
    source_id = "imf_news"
    store = MongoSourceStore()
    doc_store = MongoEnrichedDocumentStore()
    config = store.get_source(source_id)
    
    if not config:
        logger.error(f"Source {source_id} not found in DB")
        return

    logger.info(f"Testing enriched manual scrape for {source_id}")
    
    orchestrator = ScrapingOrchestrator()
    count = orchestrator.run_single_source(source_id, config, limit=1) # Just one to be fast
    
    logger.info(f"Scraped {count} items for {source_id}")
    
    # Check the last document in MongoDB
    last_doc = doc_store.collection.find_one({"source_id": source_id}, sort=[("created_at", -1)])
    if last_doc:
        logger.info("Verifying enriched fields:")
        logger.info(f"- Title: {last_doc.get('title')}")
        logger.info(f"- Topics: {last_doc.get('topics')}")
        logger.info(f"- Summary: {last_doc.get('summary')[:100]}...")
        logger.info(f"- Entities: {last_doc.get('entities')}")
        logger.info(f"- Confidence: {last_doc.get('confidence')}")
        
        if last_doc.get("topics") and last_doc.get("summary"):
            logger.info("ENRICHMENT SUCCESSFUL")
        else:
            logger.error("ENRICHMENT FAILED: Missing fields")
    else:
        logger.error("No document found in MongoDB after scrape")

if __name__ == "__main__":
    verify_enrichment()

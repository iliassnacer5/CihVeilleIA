from pymongo import MongoClient
from app.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_documents():
    client = MongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    collection = db[settings.mongodb_collection_enriched]
    
    docs = list(collection.find().sort("created_at", -1).limit(5))
    
    if not docs:
        print("No documents found in MongoDB.")
        return

    print(f"Found {len(docs)} documents. Showing latest:\n")
    for doc in docs:
        print(f"ID: {doc.get('_id')}")
        print(f"Source: {doc.get('source_id')}")
        print(f"Title: {doc.get('title')}")
        print(f"URL: {doc.get('url')}")
        print(f"Text Preview: {doc.get('text')[:200]}...") # Show first 200 chars
        print("-" * 50)

if __name__ == "__main__":
    inspect_documents()

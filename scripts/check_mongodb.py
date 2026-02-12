import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.storage.mongo_store import MongoEnrichedDocumentStore

async def check_db():
    print("Checking database for enriched documents...")
    store = MongoEnrichedDocumentStore()
    count = await store.collection.count_documents({})
    print(f"Total documents in collection: {count}")
    
    if count > 0:
        cursor = store.collection.find().sort("created_at", -1).limit(5)
        docs = await cursor.to_list(length=5)
        print("\nLatest documents:")
        for d in docs:
            print(f"- {d.get('title')} (Source: {d.get('source_id')}, Created: {d.get('created_at')})")

if __name__ == "__main__":
    asyncio.run(check_db())


import asyncio
import sys
import os
import time

# Add the project root to sys.path
sys.path.append(os.getcwd())

async def test_timestamp_update():
    print("Testing Source Timestamp Update...")
    try:
        from app.scraping.orchestrator import ScrapingOrchestrator
        from app.storage.mongo_store import MongoSourceStore
        
        orchestrator = ScrapingOrchestrator()
        source_store = MongoSourceStore()
        
        source_id = "imf_news"
        
        # 1. Get current timestamp
        source = await source_store.get_source(source_id)
        old_val = source.get("lastUpdated", "Never")
        print(f"Old timestamp: {old_val}")
        
        # 2. Run scrape (mock partial setup or just real call)
        # We use a very limited scrape to be fast
        config = {
            "name": "IMF News",
            "url": "https://www.imf.org/en/News",
            "article_link_selector": "a[href*='/en/news/articles/']",
            "title_selector": "h1",
            "content_selector": "div.news-content",
            "use_browser": False
        }
        
        print(f"Running scrape for {source_id}...")
        await orchestrator.run_single_source(source_id, config, limit=1)
        
        # 3. Check new timestamp
        updated_source = await source_store.get_source(source_id)
        new_val = updated_source.get("lastUpdated", "Never")
        print(f"New timestamp: {new_val}")
        
        if new_val != old_val:
            print("✓ SUCCESS: lastUpdated was successfully updated!")
        else:
            print("X FAILURE: lastUpdated was not changed.")
            
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_timestamp_update())

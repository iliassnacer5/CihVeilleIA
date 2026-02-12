
import asyncio
import sys
import os
import time

# Add the project root to sys.path
sys.path.append(os.getcwd())

async def test_real_scrape():
    print("Testing Real Scrape...")
    try:
        from app.scraping.orchestrator import ScrapingOrchestrator
        orchestrator = ScrapingOrchestrator()
        print("✓ Orchestrator initialized")
        
        # Test IMF news (known to be working/available)
        source_id = "imf_news"
        config = {
            "name": "IMF News",
            "url": "https://www.imf.org/en/News",
            "article_link_selector": "h3 a",
            "title_selector": "h1",
            "content_selector": ".content-block",
            "use_browser": False
        }
        
        print(f"Scraping {source_id}...")
        count = await orchestrator.run_single_source(source_id, config, limit=2)
        print(f"✓ Scrape finished. Count: {count}")
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_scrape())

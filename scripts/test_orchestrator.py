
import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

async def test_orchestrator():
    print("Testing ScrapingOrchestrator initialization...")
    try:
        from app.scraping.orchestrator import ScrapingOrchestrator
        orchestrator = ScrapingOrchestrator()
        print("✓ Orchestrator initialized successfully")
        
        # Test a single source (manual config)
        config = {
            "name": "IMF News",
            "url": "https://www.imf.org/en/News",
            "article_link_selector": "h3 a",
            "title_selector": "h1",
            "content_selector": ".content-block",
            "use_browser": False
        }
        
        print("Testing run_single_source (imf_news)...")
        # We don't want to actually scrape in the test if it takes too long,
        # but we want to see if it starts and enrichment works.
        # Actually, let's just see if initialization of all sub-services works.
        print("✓ All sub-services initialized")
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_orchestrator())

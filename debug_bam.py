import asyncio
import logging
import time
from app.scraping.browser_scraper import BrowserScraper
from app.scraping.sources_registry import SOURCES_REGISTRY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bam_scraping():
    source_id = "bam_news"
    config = SOURCES_REGISTRY.get(source_id)
    
    if not config:
        logger.error(f"Source {source_id} not found in registry")
        return

    logger.info(f"Starting test scrape for {source_id}...")
    start_time = time.time()
    
    scraper = BrowserScraper(
        base_url=config["base_url"],
        article_link_selector=config["article_link_selector"],
        title_selector=config["title_selector"],
        content_selector=config["content_selector"],
        max_articles=3  # Limit to 3 for testing
    )
    
    try:
        items = await scraper.fetch()
        logger.info(f"Scraped {len(list(items))} items in {time.time() - start_time:.2f} seconds")
        for item in items:
            logger.info(f"- {item.title} ({item.url})")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")

if __name__ == "__main__":
    if asyncio.get_event_loop_policy().__class__.__name__ != 'WindowsProactorEventLoopPolicy':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(test_bam_scraping())

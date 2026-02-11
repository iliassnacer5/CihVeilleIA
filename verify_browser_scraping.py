import logging
import asyncio
from app.scraping.browser_scraper import BrowserScraper
from app.scraping.sources_registry import SOURCES_REGISTRY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ammc_browser():
    config = SOURCES_REGISTRY["ammc_news"]
    engines = ["chromium"] # AMMC should work with chromium if it's just a timeout/WAF issue
    
    for engine in engines:
        logger.info(f"--- Testing engine: {engine} for {config['name']} ---")
        try:
            scraper = BrowserScraper(
                base_url=config["base_url"],
                article_link_selector=config["article_link_selector"],
                title_selector=config["title_selector"],
                content_selector=config["content_selector"],
                max_articles=2,
                engine=engine
            )
            
            items = list(scraper.fetch())
            
            if items:
                logger.info(f"SUCCESS with {engine}: Found {len(items)} items")
                return # Stop at first success
            else:
                logger.error(f"FAILED with {engine}: No items found")
        except Exception as e:
            logger.error(f"EXCEPTION with {engine}: {e}")

if __name__ == "__main__":
    test_ammc_browser()

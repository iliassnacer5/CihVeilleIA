import asyncio
from app.scraping.institutional_scraper import InstitutionalSiteScraper
import logging

logging.basicConfig(level=logging.INFO)

async def debug_fed_scraper():
    url = "https://www.federalreserve.gov/newsevents/pressreleases.htm"
    print(f"Testing scraper for: {url}")

    scraper = InstitutionalSiteScraper(
        base_url=url,
        article_link_selector="div.eventlist__item a",
        title_selector="h1",
        content_selector="div#article",
        max_articles=3
    )

    print("Fetching items...")
    items = await scraper.fetch()

    print(f"Result: Found {len(items)} items.")
    for item in items:
        print(f"- {item.title} ({item.url})")
        print(f"  Text Length: {len(item.raw_text)} chars")

if __name__ == "__main__":
    asyncio.run(debug_fed_scraper())

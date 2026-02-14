import asyncio
import logging
from app.scraping.orchestrator import ScrapingOrchestrator
from app.backend.api import get_nlp_service # We'll need this to ensure singleton
from app.rag.pipeline import RagPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Full Scraping Evaluation...")

    # Initialize components
    orchestrator = ScrapingOrchestrator()

    # Run for all sources
    logger.info("Executing orchestrator.run_all_sources()...")
    results = await orchestrator.run_all_sources(limit_per_source=3)

    total_docs = sum(results.values())
    logger.info(f"Scraping completed. Total documents added: {total_docs}")
    for source, count in results.items():
        logger.info(f" - {source}: {count} items")

if __name__ == "__main__":
    asyncio.run(main())

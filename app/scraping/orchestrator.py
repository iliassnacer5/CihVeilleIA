import logging
import asyncio
import time
from typing import List

from app.scraping.institutional_scraper import InstitutionalSiteScraper
from app.scraping.browser_scraper import BrowserScraper
from app.scraping.sources_registry import SOURCES_REGISTRY
from app.storage.mongo_store import MongoEnrichedDocumentStore, MongoSourceStore
from app.scraping.pdf_service import pdf_service
from app.nlp.embeddings import EmbeddingService
from app.nlp.banking_nlp import BankingNlpService
from app.rag.pipeline import RagPipeline

logger = logging.getLogger(__name__)

from app.alerts.alerts_service import AlertService

class ScrapingOrchestrator:
    """Orchestrateur pour la collecte massive d'informations avec enrichissement IA."""

    def __init__(self):
        self.mongo_store = MongoEnrichedDocumentStore()
        self.source_store = MongoSourceStore()
        self.rag_pipeline = RagPipeline()
        self.nlp_service = BankingNlpService()
        self.alert_service = AlertService()

    async def _enrich_documents_async(self, docs: List[dict]) -> List[dict]:
        """Enrichit une liste de documents avec classification, résumé et entités (Async)."""
        if not docs:
            return []
        
        texts = [d["text"] for d in docs]
        logger.info(f"Enrichissement IA pour {len(docs)} documents...")
        
        try:
            # On utilise to_thread car BankingNlpService est synchrone (CPU/GPU bound)
            # 1. Classification thématique
            logger.info("  [1/3] Classification thématique en cours...")
            classifications = await asyncio.to_thread(self.nlp_service.classify_documents, texts)
            logger.info("  ✓ Classification terminée.")
            
            # 2. Résumé automatique
            logger.info("  [2/3] Génération des résumés en cours...")
            summaries = await asyncio.to_thread(self.nlp_service.summarize_documents, texts, max_length=150, min_length=40)
            logger.info("  ✓ Résumés terminés.")
            
            # 3. Extraction d'entités
            logger.info("  [3/3] Extraction d'entités en cours...")
            entities_lists = await asyncio.to_thread(self.nlp_service.extract_entities, texts)
            logger.info("  ✓ Extraction d'entités terminée.")
            
            for idx, doc in enumerate(docs):
                doc["topics"] = [classifications[idx].label]  # Top label
                doc["summary"] = summaries[idx].summary
                doc["entities"] = list(set([e.text for e in entities_lists[idx]]))
                doc["confidence"] = int(classifications[idx].score * 100)
                
            return docs
        except Exception as e:
            logger.error(f"Erreur lors de l'enrichissement NLP: {e}")
            for doc in docs:
                doc.setdefault("topics", ["Général"])
                doc.setdefault("summary", doc["text"][:200] + "...")
                doc.setdefault("entities", [])
                doc.setdefault("confidence", 50)
            return docs

    async def run_all_sources(self, limit_per_source: int = 5, max_concurrency: int = 3):
        """Lance le cycle complet de veille en parallèle avec contrôle de concurrence."""
        logger.info(f"Démarrage du cycle de veille sur {len(SOURCES_REGISTRY)} sources...")
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def process_source(source_id, config):
            async with semaphore:
                try:
                    logger.info(f"Traitement parallèle de {source_id}...")
                    count = await self.run_single_source(source_id, config, limit=limit_per_source)
                    return source_id, count
                except Exception as e:
                    logger.error(f"Erreur source {source_id}: {e}")
                    return source_id, 0

        tasks = [process_source(sid, cfg) for sid, cfg in SOURCES_REGISTRY.items()]
        results_list = await asyncio.gather(*tasks)
        
        results = dict(results_list)
        logger.info("Cycle de veille terminé.")
        return results

    async def run_single_source(self, source_id: str, config: dict, limit: int = 5) -> int:
        """Exécute le scraping pour une source spécifique de manière asynchrone."""
        logger.info(f"Scraping de la source: {config.get('name')} ({source_id})")
        
        # Update source timestamp at the start of operation
        await self.source_store.update_source_timestamp(source_id)
        
        article_link_selector = config.get("article_link_selector", "a")
        title_selector = config.get("title_selector", "h1")
        content_selector = config.get("content_selector", "div, p")
        
        if config.get("use_browser"):
            scraper = BrowserScraper(
                base_url=config["base_url"] if "base_url" in config else config["url"],
                article_link_selector=article_link_selector,
                title_selector=title_selector,
                content_selector=content_selector,
                category=config.get("category", "Général"),
                doc_type=config.get("doc_type", "News"),
                max_articles=limit
            )
        else:
            scraper = InstitutionalSiteScraper(
                base_url=config["base_url"] if "base_url" in config else config["url"],
                article_link_selector=article_link_selector,
                title_selector=title_selector,
                content_selector=content_selector,
                category=config.get("category", "Général"),
                doc_type=config.get("doc_type", "News"),
                max_articles=limit
            )
        
        try:
            items = list(await scraper.fetch())
            if not items:
                return 0
            
            docs_to_save = []
            for item in items:
                # Si le texte est vide ou si l'URL finit par .pdf, on tente une extraction PDF
                text = item.raw_text
                if not text or item.url.lower().endswith(".pdf"):
                    extracted_text = await pdf_service.extract_text_from_url(item.url)
                    if extracted_text:
                        text = extracted_text

                doc = {
                    "source_id": source_id,
                    "title": item.title,
                    "url": item.url,
                    "text": text,
                    "category": item.category,
                    "doc_type": item.doc_type,
                    "created_at": time.time(),
                }
                docs_to_save.append(doc)
            
            # ENRICHISSEMENT IA
            logger.info(f"Enrichissement IA pour {len(docs_to_save)} documents...")
            enriched_docs = await self._enrich_documents_async(docs_to_save)
            
            logger.info(f"Sauvegarde de {len(enriched_docs)} documents dans MongoDB...")
            try:
                ids = await self.mongo_store.save_documents(enriched_docs)
                logger.info(f"✓ {len(ids)} documents sauvegardés avec succès (IDs: {ids[:2]}...)")
            except Exception as save_err:
                logger.error(f"❌ Échec de la sauvegarde MongoDB: {save_err}")
                raise
            
            # GENERATION ALERTS (Nouveau Phase 3)
            logger.info("Traitement des alertes...")
            await self.alert_service.process_new_documents(enriched_docs)
            
            # Indexation Vectorielle (RAG)
            texts = [d["text"] for d in enriched_docs]
            metadatas = [
                {
                    "source": source_id, 
                    "title": d["title"], 
                    "url": d["url"],
                    "topics": d["topics"],
                    "summary": d["summary"]
                } for d in enriched_docs
            ]
            await self.rag_pipeline.index_documents(texts, metadatas)
            
            return len(enriched_docs)
        except Exception as e:
            logger.error(f"Erreur scraping {source_id}: {e}")
            return 0

if __name__ == "__main__":
    # Pour test local
    orchestrator = ScrapingOrchestrator()
    asyncio.run(orchestrator.run_all_sources(limit_per_source=2))

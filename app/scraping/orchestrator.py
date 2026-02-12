import logging
import asyncio
import time
from typing import List

from app.scraping.institutional_scraper import InstitutionalSiteScraper
from app.scraping.browser_scraper import BrowserScraper
from app.scraping.sources_registry import SOURCES_REGISTRY
from app.storage.mongo_store import MongoEnrichedDocumentStore
from app.nlp.embeddings import EmbeddingService
from app.nlp.banking_nlp import BankingNlpService
from app.rag.pipeline import RagPipeline

logger = logging.getLogger(__name__)

class ScrapingOrchestrator:
    """Orchestrateur pour la collecte massive d'informations avec enrichissement IA."""

    def __init__(self):
        self.mongo_store = MongoEnrichedDocumentStore()
        self.rag_pipeline = RagPipeline()
        self.nlp_service = BankingNlpService()

    def _enrich_documents(self, docs: List[dict]) -> List[dict]:
        """Enrichit une liste de documents avec classification, résumé et entités."""
        if not docs:
            return []
        
        texts = [d["text"] for d in docs]
        
        logger.info(f"Enrichissement IA pour {len(docs)} documents...")
        
        try:
            # 1. Classification thématique
            classifications = self.nlp_service.classify_documents(texts)
            
            # 2. Résumé automatique
            summaries = self.nlp_service.summarize_documents(texts, max_length=150, min_length=40)
            
            # 3. Extraction d'entités
            entities_lists = self.nlp_service.extract_entities(texts)
            
            for idx, doc in enumerate(docs):
                doc["topics"] = [classifications[idx].label]  # Top label
                doc["summary"] = summaries[idx].summary
                # Extraction des textes d'entités uniques
                doc["entities"] = list(set([e.text for e in entities_lists[idx]]))
                doc["confidence"] = int(classifications[idx].score * 100)
                
            return docs
        except Exception as e:
            logger.error(f"Erreur lors de l'enrichissement NLP: {e}")
            # Fallback : on garde les docs mais avec des thèmes par défaut
            for doc in docs:
                doc.setdefault("topics", ["Général"])
                doc.setdefault("summary", doc["text"][:200] + "...")
                doc.setdefault("entities", [])
                doc.setdefault("confidence", 50)
            return docs

    async def run_all_sources(self, limit_per_source: int = 5):
        """Lance le cycle complet de veille sur toutes les sources enregistrées."""
        total_sources = len(SOURCES_REGISTRY)
        logger.info(f"Démarrage du cycle de veille sur {total_sources} sources...")
        results = {}
        
        for source_id, config in SOURCES_REGISTRY.items():
            try:
                results[source_id] = 0
                logger.info(f"Traitement de la source: {config['name']} ({source_id})")
                
                if config.get("use_browser"):
                    scraper = BrowserScraper(
                        base_url=config["base_url"],
                        article_link_selector=config["article_link_selector"],
                        title_selector=config["title_selector"],
                        content_selector=config["content_selector"],
                        max_articles=limit_per_source
                    )
                else:
                    scraper = InstitutionalSiteScraper(
                        base_url=config["base_url"],
                        article_link_selector=config["article_link_selector"],
                        title_selector=config["title_selector"],
                        content_selector=config["content_selector"],
                        max_articles=limit_per_source
                    )
                
                items = list(await scraper.fetch())
                if not items:
                    continue
                
                # Conversion pour stockage
                docs_to_save = []
                for item in items:
                    doc = {
                        "source_id": source_id,
                        "title": item.title,
                        "url": item.url,
                        "text": item.raw_text,
                        "created_at": time.time(),
                    }
                    docs_to_save.append(doc)
                
                # ENRICHISSEMENT IA (Nouveau)
                enriched_docs = self._enrich_documents(docs_to_save)
                
                # Sauvegarde MongoDB
                self.mongo_store.save_documents(enriched_docs)
                
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
                self.rag_pipeline.index_documents(texts, metadatas)
                
                results[source_id] = len(enriched_docs)
                logger.info(f"Source {source_id} terminée: {len(enriched_docs)} documents enrichis et indexés.")
                
            except Exception as e:
                import traceback
                logger.error(f"Erreur lors du traitement de la source {source_id}: {e}\n{traceback.format_exc()}")
        
        return results

    async def run_single_source(self, source_id: str, config: dict, limit: int = 5) -> int:
        """Exécute le scraping pour une source spécifique avec enrichissement."""
        logger.info(f"Scraping manuel de la source: {config.get('name')} ({source_id})")
        
        article_link_selector = config.get("article_link_selector", "a")
        title_selector = config.get("title_selector", "h1")
        content_selector = config.get("content_selector", "div, p")
        
        if config.get("use_browser"):
            scraper = BrowserScraper(
                base_url=config["base_url"] if "base_url" in config else config["url"],
                article_link_selector=article_link_selector,
                title_selector=title_selector,
                content_selector=content_selector,
                max_articles=limit
            )
        else:
            scraper = InstitutionalSiteScraper(
                base_url=config["base_url"] if "base_url" in config else config["url"],
                article_link_selector=article_link_selector,
                title_selector=title_selector,
                content_selector=content_selector,
                max_articles=limit
            )
        
        try:
            items = list(await scraper.fetch())
            if not items:
                return 0
            
            docs_to_save = []
            for item in items:
                doc = {
                    "source_id": source_id,
                    "title": item.title,
                    "url": item.url,
                    "text": item.raw_text,
                    "created_at": time.time(),
                }
                docs_to_save.append(doc)
            
            # ENRICHISSEMENT IA (Nouveau)
            enriched_docs = self._enrich_documents(docs_to_save)
            
            self.mongo_store.save_documents(enriched_docs)
            
            # Indexation
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
            self.rag_pipeline.index_documents(texts, metadatas)
            
            return len(enriched_docs)
        except Exception as e:
            import traceback
            logger.error(f"Erreur lors du scraping manuel ({source_id}): {e}\n{traceback.format_exc()}")
            raise e

if __name__ == "__main__":
    orchestrator = ScrapingOrchestrator()
    orchestrator.run_all_sources(limit_per_source=2)

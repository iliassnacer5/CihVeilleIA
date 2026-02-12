import asyncio
import logging
import sys
import os

# Ajout du chemin racine pour les imports
sys.path.append(os.getcwd())

from app.rag.pipeline import RagPipeline
from app.rag.chunking import ChunkingService
from app.nlp.reranking import RerankingService
from app.alerts.alerts_service import AlertService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Verification")

async def test_components():
    logger.info("--- Démarrage de la Vérification des Composants Production ---")
    
    # 1. Test Chunking
    chunker = ChunkingService()
    test_text = "Ceci est un test de document. " * 50
    chunks = chunker.chunk_text(test_text)
    logger.info(f"Test Chunking: {len(chunks)} chunks générés (Taille approx: {len(test_text)} chars)")
    
    # 2. Test Reranking
    reranker = RerankingService()
    query = "Test de sécurité"
    passages = ["Document sur la cuisine", "Rapport sur la cybersécurité et les risques", "Météo du jour"]
    results = reranker.rerank(query, passages, top_n=2)
    logger.info(f"Test Reranking: Top 1 index = {results[0][0]} (Attendu: 1)")
    
    # 3. Test AlertService (Mock alert generation)
    alert_service = AlertService()
    test_docs = [
        {
            "title": "Alerte Sécurité Majeure",
            "topics": ["Cybersécurité"],
            "summary": "Attaque détectée sur le réseau.",
            "confidence": 95,
            "source_id": "test_source"
        }
    ]
    # Note: process_new_documents uses async mongo internally, will skip actual save if mongo not running
    try:
        count = await alert_service.process_new_documents(test_docs)
        logger.info(f"Test AlertService: {count} alertes générées.")
    except Exception as e:
        logger.warning(f"Test AlertService: Échec Mongo (attendu si DB off) : {e}")
        
    logger.info("--- Vérification Terminée ---")

if __name__ == "__main__":
    asyncio.run(test_components())

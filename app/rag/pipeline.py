from dataclasses import dataclass
from typing import List
import logging

import numpy as np

from app.config.settings import settings
from app.nlp.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from app.storage.audit_log import audit_logger

logger = logging.getLogger(__name__)


@dataclass
class RagResult:
    question: str
    context: List[str]
    answer: str


from app.nlp.banking_nlp import BankingNlpService

class RagPipeline:
    """Pipeline RAG pour la veille bancaire.
    
    Utilise FAISS pour la recherche vectorielle et des modèles Transformers
    pour la génération de réponses synthétiques (moteur de summarization).
    """

    def __init__(self, embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2", nlp_service: BankingNlpService = None):
        self.embedding_service = EmbeddingService(model_name=embedding_model)
        dummy_vector = self.embedding_service.encode(["dummy"])
        dim = int(dummy_vector.shape[1])
        self.vector_store = VectorStore(dim=dim, store_dir=settings.vector_store_dir)
        self.nlp_service = nlp_service or BankingNlpService()

    def index_documents(self, texts: List[str], metadatas: List[dict]) -> None:
        vectors = self.embedding_service.encode(texts)
        self.vector_store.add(vectors=np.array(vectors), metadatas=metadatas)

    def answer_question(self, question: str, top_k: int = 5) -> RagResult:
        query_vec = self.embedding_service.encode([question])[0]
        retrieved = self.vector_store.search(np.array(query_vec), k=top_k)
        context = [meta.get("text", "") for meta, _ in retrieved]

        # Génération de réponse réaliste via summarization du contexte
        if context:
            prompt_context = "\n\n".join(context[:3])
            summaries = self.nlp_service.summarize_documents(
                texts=[f"Question: {question}\n\nContexte:\n{prompt_context}"],
                max_length=150,
                min_length=40
            )
            answer = summaries[0].summary if summaries else "Impossible de générer une réponse."
        else:
            answer = "Aucun document pertinent n'a été trouvé pour répondre à cette question."

        # Auditability: Traçabilité complète de l'interaction IA
        audit_logger.log_event(
            "AI_REQUEST", 
            "RAG_GENERATION", 
            "SUCCESS", 
            {
                "question": question, 
                "answer_preview": answer[:100] + "...",
                "context_sources_count": len(context),
                "model_used": "mT5-multilingual-XLSum"
            }
        )

        return RagResult(question=question, context=context, answer=answer)


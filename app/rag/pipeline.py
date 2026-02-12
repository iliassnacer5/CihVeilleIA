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
    sources: List[dict] # Added sources


from app.nlp.banking_nlp import BankingNlpService

from app.nlp.reranking import RerankingService

class RagPipeline:
    """Pipeline RAG améliorée avec chunking et reranking."""

    def __init__(self, embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2", nlp_service: BankingNlpService = None):
        self.embedding_service = EmbeddingService(model_name=embedding_model)
        dummy_vector = self.embedding_service.encode(["dummy"])
        dim = int(dummy_vector.shape[1])
        self.vector_store = VectorStore(dim=dim, store_dir=settings.vector_store_dir)
        self.nlp_service = nlp_service or BankingNlpService()
        self.chunking_service = ChunkingService()
        self.reranking_service = RerankingService()

    async def index_documents(self, texts: List[str], metadatas: List[dict]) -> None:
        """Découpe les documents en chunks et les indexe dans FAISS."""
        import asyncio
        all_chunks = []
        all_metadatas = []
        
        for text, meta in zip(texts, metadatas):
            chunks_with_meta = self.chunking_service.create_chunks_with_metadata(text, meta)
            for item in chunks_with_meta:
                all_chunks.append(item["text"])
                all_metadatas.append(item["metadata"])
        
        if not all_chunks:
            return

        logger.info(f"Indexation RAG: {len(all_chunks)} chunks à partir de {len(texts)} documents.")
        vectors = await asyncio.to_thread(self.embedding_service.encode, all_chunks)
        self.vector_store.add(vectors=np.array(vectors), metadatas=all_metadatas)

    async def retrieve(self, question: str, top_k: int = 5):
        """Récupère les meilleurs chunks avec reranking."""
        import asyncio
        # Dense Retrieval (FAISS) - on récupère plus pour reranker
        query_vec = await asyncio.to_thread(self.embedding_service.encode, [question])
        query_vec = query_vec[0]
        retrieved = self.vector_store.search(np.array(query_vec), k=top_k * 3)
        
        if not retrieved:
            return []

        # Reranking
        passages = [meta.get("text", "") for meta, _ in retrieved]
        reranked_results = await asyncio.to_thread(self.reranking_service.rerank, question, passages, top_n=top_k)
        
        final_results = []
        class DocModel:
            def __init__(self, page_content, metadata):
                self.page_content = page_content
                self.metadata = metadata

        for idx, score in reranked_results:
            meta, _ = retrieved[idx]
            final_results.append(DocModel(passages[idx], meta))
            
        return final_results

    async def answer_question(self, question: str, top_k: int = 5) -> RagResult:
        import asyncio
        # 1. Retrieval & Reranking
        retrieved_docs = await self.retrieve(question, top_k=top_k)
        context_chunks = [doc.page_content for doc in retrieved_docs]

        # 2. Results & Sources mapping
        sources = []
        seen_urls = set()
        for doc in retrieved_docs:
            url = doc.metadata.get("url")
            if url and url not in seen_urls:
                sources.append({
                    "title": doc.metadata.get("title", "Sans titre"),
                    "url": url
                })
                seen_urls.add(url)

        # 3. Generation
        if context_chunks:
            prompt_context = "\n\n".join(context_chunks)
            summaries = await asyncio.to_thread(
                self.nlp_service.summarize_documents,
                texts=[f"Question: {question}\n\nContexte:\n{prompt_context}"],
                max_length=250,
                min_length=50
            )
            answer = summaries[0].summary if summaries else "Impossible de générer une réponse."
        else:
            answer = "Aucun document pertinent n'a été trouvé."

        asyncio.create_task(self._log_audit(question, answer, len(context_chunks)))
        return RagResult(question=question, context=context_chunks, answer=answer, sources=sources)

    async def _log_audit(self, question, answer, context_count):
        await audit_logger.log_event_async(
            "AI_REQUEST", 
            "RAG_GENERATION", 
            "SUCCESS", 
            {
                "question": question, 
                "answer_preview": answer[:100] + "...",
                "context_chunks_count": context_count,
            }
        )


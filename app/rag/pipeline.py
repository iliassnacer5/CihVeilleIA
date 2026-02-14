"""
Pipeline RAG v3 — High-Performance Retrieval-Augmented Generation.

Architecture:
1. Semantic Chunking (spaCy fr_core_news_md)
2. Dense Retrieval (FAISS + multilingual-e5-large, 1024 dims)
3. Cross-Encoder Reranking (multilingual)
4. LLM Generation (Gemini 2.0 Flash)
"""

from dataclasses import dataclass
from typing import List
import logging

import numpy as np

from app.config.settings import settings
from app.nlp.embeddings import EmbeddingService
from app.nlp.llm_service import LlmService, SYSTEM_PROMPT_RAG, build_rag_prompt
from app.rag.vector_store import VectorStore
from app.storage.audit_log import audit_logger

logger = logging.getLogger(__name__)


@dataclass
class RagResult:
    question: str
    context: List[str]
    answer: str
    sources: List[dict]


from app.nlp.banking_nlp import BankingNlpService
from app.nlp.reranking import RerankingService
from app.rag.chunking import ChunkingService


class RagPipeline:
    """Pipeline RAG v3 — LLM Generation + Chunking + Reranking."""

    def __init__(
        self,
        embedding_model: str = "intfloat/multilingual-e5-large",
        nlp_service: BankingNlpService = None,
    ):
        self.embedding_service = EmbeddingService(model_name=embedding_model)
        # Déterminer la dimension automatiquement
        dummy_vector = self.embedding_service.encode(["test"])
        dim = int(dummy_vector.shape[1])
        logger.info(f"RAG Pipeline: FAISS dimension = {dim}")
        self.vector_store = VectorStore(dim=dim, store_dir=settings.vector_store_dir)
        self.nlp_service = nlp_service or BankingNlpService()
        self.chunking_service = ChunkingService()
        self.reranking_service = RerankingService()
        self.llm_service = LlmService()

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

        logger.info(f"Indexation RAG: {len(all_chunks)} chunks from {len(texts)} documents.")
        # Utilise encode_passages pour le prefix E5 correct
        vectors = await asyncio.to_thread(self.embedding_service.encode_passages, all_chunks)
        self.vector_store.add(vectors=np.array(vectors), metadatas=all_metadatas)

    async def retrieve(self, question: str, top_k: int = 5):
        """Récupère les meilleurs chunks avec reranking."""
        import asyncio
        # Dense Retrieval (FAISS) — utilise encode_query pour le prefix E5
        query_vec = await asyncio.to_thread(self.embedding_service.encode_query, question)
        retrieved = self.vector_store.search(np.array(query_vec), k=top_k * 3)
        
        if not retrieved:
            return []

        # Reranking multilingue
        passages = [meta.get("text", "") for meta, _ in retrieved]
        reranked_results = await asyncio.to_thread(
            self.reranking_service.rerank, question, passages, top_n=top_k
        )
        
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

        # 2. Sources mapping
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

        # 3. LLM Generation
        if context_chunks:
            chunk_sources = []
            for doc in retrieved_docs:
                chunk_sources.append({
                    "title": doc.metadata.get("title", "Document"),
                    "url": doc.metadata.get("url", "")
                })

            prompt = build_rag_prompt(question, context_chunks, chunk_sources)
            answer = await self.llm_service.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT_RAG,
                max_tokens=1024,
                temperature=0.3,
            )
            logger.info(f"RAG answer generated via {self.llm_service.provider} ({len(answer)} chars)")
        else:
            answer = "Aucun document pertinent n'a été trouvé dans la base de veille."

        asyncio.create_task(self._log_audit(question, answer, len(context_chunks)))
        return RagResult(question=question, context=context_chunks, answer=answer, sources=sources)

    async def _log_audit(self, question, answer, context_count):
        await audit_logger.log_event(
            "AI_REQUEST", 
            "RAG_GENERATION", 
            "SUCCESS", 
            {
                "question": question, 
                "answer_preview": answer[:100] + "...",
                "context_chunks_count": context_count,
                "llm_provider": self.llm_service.provider,
            }
        )

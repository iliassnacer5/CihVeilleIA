from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.nlp.banking_nlp import BankingNlpService
from app.nlp.llm_service import LlmService, SYSTEM_PROMPT_RAG
from app.search.semantic_search import SearchFilters, SearchResult, SemanticSearchEngine


@dataclass
class ChatSource:
    """Source citée dans une réponse RAG."""

    title: Optional[str]
    url: Optional[str]
    score: float


@dataclass
class ChatbotAnswer:
    """Réponse du chatbot RAG, explicable et traçable."""

    question: str
    answer: str
    safe: bool
    reason: str
    sources: List[ChatSource]


class RagChatbot:
    """Chatbot RAG v2 pour questions métier bancaires.

    Améliorations v2:
    - Utilise un LLM génératif (Gemini/OpenAI) au lieu d'un simple résumé ;
    - Recherche hybride (vectorielle + mots-clés) pour plus de précision ;
    - Citations précises des sources dans les réponses ;
    - Garde-fous stricts contre les hallucinations.
    """

    def __init__(
        self,
        search_engine: Optional[SemanticSearchEngine] = None,
        nlp_service: Optional[BankingNlpService] = None,
        min_vector_score: float = 0.01,
        min_documents: int = 1,
    ) -> None:
        self.search_engine = search_engine or SemanticSearchEngine()
        self.nlp_service = nlp_service or BankingNlpService()
        self.llm_service = LlmService()
        self.min_vector_score = min_vector_score
        self.min_documents = min_documents

    def _build_sources(self, results: List[SearchResult]) -> List[ChatSource]:
        sources: List[ChatSource] = []
        for r in results:
            if not r.url and not r.title:
                continue
            sources.append(
                ChatSource(
                    title=r.title,
                    url=r.url,
                    score=float(r.score),
                )
            )
        return sources

    def _make_fallback_answer(self, question: str, reason: str) -> ChatbotAnswer:
        """Réponse prudente lorsque la base ne couvre pas la question."""
        answer_text = (
            "Je ne dispose pas d'assez d'informations fiables dans la base documentaire "
            "pour répondre précisément à cette question. "
            "Merci de consulter un expert métier ou d'enrichir la base avec des documents pertinents."
        )
        return ChatbotAnswer(
            question=question,
            answer=answer_text,
            safe=False,
            reason=reason,
            sources=[],
        )

    async def answer(
        self,
        question: str,
        filters: Optional[SearchFilters] = None,
        top_k: int = 5,
    ) -> ChatbotAnswer:
        """Répond à une question métier en s'appuyant uniquement sur les documents indexés."""
        import asyncio
        import logging
        logger = logging.getLogger(__name__)

        if not question or not question.strip():
            return self._make_fallback_answer(
                question=question,
                reason="Question vide ou invalide.",
            )

        filters = filters or SearchFilters()

        # --- Hybrid Search (v2: vector + keyword) ---
        try:
            results = await self.search_engine.hybrid_search(
                query=question,
                filters=filters,
                keyword_weight=0.3,
                vector_weight=0.7,
                limit=top_k,
            )
        except Exception as e:
            logger.warning(f"Hybrid search failed, falling back to vector: {e}")
            results = await self.search_engine.vector_search(
                query=question,
                filters=filters,
                top_k=top_k,
            )

        if not results:
            logger.warning(f"RAG: No results found for query '{question}'")
            return self._make_fallback_answer(
                question=question,
                reason="Aucun document pertinent trouvé.",
            )

        # Log results for debugging
        logger.info(f"RAG Retrieval for '{question}': Found {len(results)} docs.")
        for i, res in enumerate(results):
            logger.info(f"   [{i}] Score: {res.score:.4f} | Title: {res.title}")

        # Vérification de la confiance minimale
        best_score = float(results[0].score)
        if best_score < self.min_vector_score:
            logger.warning(f"RAG: Best score {best_score} < threshold {self.min_vector_score}")
            return self._make_fallback_answer(
                question=question,
                reason=f"Score de similarité insuffisant (score max={best_score:.3f}).",
            )
        
        # Construction du contexte
        context_texts: List[str] = []
        source_titles: List[str] = []
        for r in results:
            ctx = r.summary or r.text_snippet or ""
            if not ctx:
                continue
            title = r.title or "Document"
            context_texts.append(f"[Document: {title}]\n{ctx}")
            source_titles.append(title)

        if not context_texts:
            return self._make_fallback_answer(
                question=question,
                reason="Les documents trouvés ne contiennent pas de texte exploitable.",
            )

        joined_context = "\n\n---\n\n".join(context_texts)
        
        # --- LLM Generation (v2: replaces simple summarization) ---
        prompt = (
            f"Question de l'utilisateur : {question}\n\n"
            f"Contexte documentaire :\n\n{joined_context}\n\n---\n\n"
            "Réponds à la question en t'appuyant EXCLUSIVEMENT sur les documents ci-dessus.\n"
            "Cite les sources utilisées avec le format [Source: titre].\n"
            "Si les documents ne permettent pas de répondre, indique-le clairement."
        )

        try:
            answer_text = await self.llm_service.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT_RAG,
                max_tokens=1024,
                temperature=0.3,
            )
            logger.info(f"Chatbot answer generated via {self.llm_service.provider}")
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fallback to disclaimer
            answer_text = (
                "Une erreur est survenue lors de la génération de la réponse. "
                "Voici les documents pertinents trouvés, veuillez les consulter directement."
            )

        # Add disclaimer for banking compliance
        final_answer = (
            f"{answer_text.strip()}\n\n"
            "---\n"
            "*⚠️ Cette réponse est générée par IA à partir des documents de veille. "
            "Elle ne constitue pas un avis réglementaire officiel.*"
        )

        sources = self._build_sources(results)
        reason = f"Réponse générée via {self.llm_service.provider} à partir de {len(results)} documents."

        return ChatbotAnswer(
            question=question,
            answer=final_answer,
            safe=True,
            reason=reason,
            sources=sources,
        )

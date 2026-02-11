from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.nlp.banking_nlp import BankingNlpService
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
    """Chatbot RAG pour questions métier bancaires.

    Caractéristiques:
    - ne répond qu'à partir des documents indexés (RAG strict) ;
    - cite systématiquement les sources utilisées ;
    - applique des seuils de confiance pour limiter les hallucinations ;
    - s'appuie sur des modèles Transformers pour résumer le contexte.
    """

    def __init__(
        self,
        search_engine: Optional[SemanticSearchEngine] = None,
        nlp_service: Optional[BankingNlpService] = None,
        min_vector_score: float = 0.25,
        min_documents: int = 1,
    ) -> None:
        self.search_engine = search_engine or SemanticSearchEngine()
        self.nlp_service = nlp_service or BankingNlpService()
        self.min_vector_score = min_vector_score
        self.min_documents = min_documents

    def _build_sources(self, results: List[SearchResult]) -> List[ChatSource]:
        sources: List[ChatSource] = []
        for r in results:
            if not r.url and not r.title:
                # on ne cite que les résultats identifiables
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

    def answer(
        self,
        question: str,
        filters: Optional[SearchFilters] = None,
        top_k: int = 5,
    ) -> ChatbotAnswer:
        """Répond à une question métier en s'appuyant uniquement sur les documents indexés."""
        if not question or not question.strip():
            return self._make_fallback_answer(
                question=question,
                reason="Question vide ou invalide.",
            )

        filters = filters or SearchFilters()

        # Recherche principalement vectorielle pour la sémantique
        results = self.search_engine.vector_search(
            query=question,
            filters=filters,
            top_k=top_k,
        )

        if not results:
            return self._make_fallback_answer(
                question=question,
                reason="Aucun document pertinent trouvé.",
            )

        # Vérification de la confiance minimale
        best_score = float(results[0].score)
        if best_score < self.min_vector_score or len(results) < self.min_documents:
            return self._make_fallback_answer(
                question=question,
                reason=f"Score de similarité insuffisant (score max={best_score:.3f}).",
            )

        # Construction du contexte à partir des meilleurs résultats
        context_texts: List[str] = []
        for r in results:
            ctx = r.summary or r.text_snippet or ""
            if not ctx:
                continue
            context_texts.append(ctx)

        if not context_texts:
            return self._make_fallback_answer(
                question=question,
                reason="Les documents trouvés ne contiennent pas de texte exploitable.",
            )

        # On concatène les passages pour les résumer en une réponse courte.
        # Le résumé reste borné par les capacités du modèle, ce qui limite
        # les risques d'hallucination hors contexte.
        joined_context = "\n\n".join(context_texts)
        summaries = self.nlp_service.summarize_documents(
            texts=[f"Question: {question}\n\nContexte:\n{joined_context}"],
            max_length=160,
            min_length=40,
        )

        summary_text = summaries[0].summary if summaries else ""
        if not summary_text.strip():
            return self._make_fallback_answer(
                question=question,
                reason="Le modèle de résumé n'a pas pu générer de réponse fiable.",
            )

        answer_text = (
            "Voici une réponse synthétique basée uniquement sur les documents de veille trouvés. "
            "Elle ne doit pas être interprétée comme un avis réglementaire ou de conformité.\n\n"
            f"{summary_text.strip()}"
        )

        sources = self._build_sources(results)

        return ChatbotAnswer(
            question=question,
            answer=answer_text,
            safe=True,
            reason="Réponse générée à partir de documents sélectionnés par similarité vectorielle.",
            sources=sources,
        )


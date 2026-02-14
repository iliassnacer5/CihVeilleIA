"""
LLM Service — High-Performance Generative AI for CIH Veille IA.

Provider hierarchy:
  1. Google Gemini 2.5 Flash (default — latest, most reliable)
  2. OpenAI GPT-4o
  3. Fallback to local summarization model

Provider is selected automatically based on available API keys.
"""

import logging
from typing import List, Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Modèle Gemini principal — 2.5 Flash est le plus récent et performant
GEMINI_MODEL = "gemini-2.5-flash-preview-05-20"


class LlmService:
    """Service de génération LLM haute performance pour le RAG."""

    def __init__(self):
        self._provider: Optional[str] = None
        self._client = None
        self._init_provider()

    def _init_provider(self):
        """Initialise le meilleur provider LLM disponible."""
        # 1. Try Google Gemini
        if getattr(settings, "gemini_api_key", None):
            try:
                from google import genai
                self._client = genai.Client(api_key=settings.gemini_api_key)
                self._provider = "gemini"
                logger.info(f"✅ LLM Provider: Google Gemini ({GEMINI_MODEL})")
                return
            except ImportError:
                logger.warning("google-genai package not installed. pip install google-genai")
            except Exception as e:
                logger.warning(f"Failed to init Gemini: {e}")

        # 2. Try OpenAI
        if getattr(settings, "openai_api_key", None):
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=settings.openai_api_key)
                self._provider = "openai"
                logger.info("✅ LLM Provider: OpenAI initialized.")
                return
            except ImportError:
                logger.warning("openai package not installed. pip install openai")
            except Exception as e:
                logger.warning(f"Failed to init OpenAI: {e}")

        # 3. Fallback: local summarization
        self._provider = "local"
        logger.info("⚠️ LLM Provider: Fallback to local model (no API key configured).")

    @property
    def provider(self) -> str:
        return self._provider or "local"

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.2,
    ) -> str:
        """Génère une réponse à partir d'un prompt."""
        import asyncio

        if self._provider == "gemini":
            return await self._generate_gemini(prompt, system_prompt, max_tokens, temperature)
        elif self._provider == "openai":
            return await asyncio.to_thread(
                self._generate_openai_sync, prompt, system_prompt, max_tokens, temperature
            )
        else:
            return await asyncio.to_thread(self._generate_local, prompt)

    async def _generate_gemini(
        self, prompt: str, system_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        """Génération via Google Gemini 2.5 Flash."""
        import asyncio
        try:
            from google.genai import types

            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=GEMINI_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )
            return response.text or "Impossible de générer une réponse."
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            # Fallback to gemini-2.0-flash if 2.5 fails
            try:
                logger.info("Retrying with gemini-2.0-flash...")
                response = await asyncio.to_thread(
                    self._client.models.generate_content,
                    model="gemini-2.0-flash",
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=max_tokens,
                        temperature=temperature,
                    ),
                )
                return response.text or "Impossible de générer une réponse."
            except Exception as fallback_err:
                logger.error(f"Gemini fallback also failed: {fallback_err}")
                return f"Erreur de génération LLM: {e}"

    def _generate_openai_sync(
        self, prompt: str, system_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        """Génération via OpenAI (synchrone, appelé dans un thread)."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self._client.chat.completions.create(
                model=getattr(settings, "openai_model", "gpt-4o-mini"),
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content or "Impossible de générer une réponse."
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return f"Erreur de génération LLM: {e}"

    def _generate_local(self, prompt: str) -> str:
        """Fallback: résumé local via Transformers."""
        try:
            from app.nlp.banking_nlp import BankingNlpService
            nlp = BankingNlpService()
            summaries = nlp.summarize_documents(
                texts=[prompt], max_length=300, min_length=50
            )
            return summaries[0].summary if summaries else "Impossible de générer une réponse."
        except Exception as e:
            logger.error(f"Local generation failed: {e}")
            return f"Erreur de génération locale: {e}"


# ---------------------------------------------------------------------------
# RAG Prompts — Optimisés pour la veille bancaire CIH
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_RAG = """Tu es un assistant expert en veille réglementaire et bancaire, spécialisé pour CIH Bank (Maroc).
Tu es utilisé par les équipes Conformité, Risques et Direction Générale de la banque.

MISSION : Répondre de manière précise, structurée et professionnelle en t'appuyant UNIQUEMENT sur les documents fournis.

RÈGLES STRICTES :
1. NE JAMAIS inventer d'information. Si le contexte ne contient pas la réponse, dis clairement : "Les documents disponibles ne contiennent pas cette information."
2. TOUJOURS citer tes sources avec le format [Source: titre du document].
3. Répondre en FRANÇAIS, dans un style professionnel adapté au secteur bancaire.
4. Pour la réglementation : mentionner les références précises (numéros de circulaires, articles de loi, dates d'application).
5. Structurer la réponse avec des titres et des puces si la question est complexe.
6. Terminer par une SYNTHÈSE de 1 à 2 phrases résumant les points clés.
7. Si plusieurs documents apportent des informations complémentaires, croiser les données pour une réponse complète.
8. Mentionner les implications concrètes pour CIH Bank quand c'est pertinent.

FORMAT DE RÉPONSE :
- Utiliser des paragraphes courts et clairs
- Utiliser des listes à puces pour les énumérations
- Mettre en évidence les dates, montants et seuils importants
- Citer les sources entre crochets après chaque affirmation"""


def build_rag_prompt(question: str, context_chunks: List[str], sources: List[dict]) -> str:
    """Construit le prompt RAG avec contexte et sources."""
    # Build numbered context with source attribution
    context_parts = []
    for i, (chunk, source) in enumerate(zip(context_chunks, sources), 1):
        title = source.get("title", f"Document {i}")
        url = source.get("url", "")
        context_parts.append(f"[Document {i}: {title}]\nURL: {url}\n{chunk}")

    context_str = "\n\n---\n\n".join(context_parts)

    prompt = f"""Question de l'utilisateur : {question}

═══════════════════════════════════════
CONTEXTE DOCUMENTAIRE ({len(context_chunks)} documents de veille CIH Bank)
═══════════════════════════════════════

{context_str}

═══════════════════════════════════════
INSTRUCTIONS
═══════════════════════════════════════

1. Analyse attentivement TOUS les documents ci-dessus.
2. Réponds à la question en t'appuyant EXCLUSIVEMENT sur ces documents.
3. Cite chaque source utilisée avec le format [Source: titre du document].
4. Si les documents ne permettent pas de répondre complètement, indique-le clairement.
5. Termine par une synthèse courte (1-2 phrases)."""

    return prompt

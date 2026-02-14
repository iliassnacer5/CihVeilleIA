"""
Service de traduction automatique utilisant Google Gemini API.

Fonctionnalités:
  - Détection automatique de la langue
  - Traduction vers le français (langue par défaut)
  - Traduction vers l'anglais (à la demande)
"""

import logging
from typing import Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)


class TranslationService:
    """Service de traduction multi-langues avec Google Gemini."""

    def __init__(self):
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialise le client Google Gemini."""
        if not getattr(settings, "gemini_api_key", None):
            logger.error("GEMINI_API_KEY not configured. Translation service disabled.")
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=settings.gemini_api_key)
            logger.info("✅ Translation Service: Google Gemini initialized.")
        except ImportError:
            logger.error("google-genai package not installed. pip install google-genai")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini for translation: {e}")

    def detect_language(self, text: str) -> str:
        """
        Détecte la langue d'un texte.
        
        Args:
            text: Texte à analyser
            
        Returns:
            Code de langue ISO 639-1 (ex: 'fr', 'ar', 'en')
        """
        if not self._client:
            logger.warning("Translation client not initialized, defaulting to 'fr'")
            return "fr"

        if not text or len(text.strip()) < 10:
            return "fr"

        try:
            prompt = f"""Detect the language of the following text and respond with ONLY the ISO 639-1 language code (2 letters).
Examples: 'fr' for French, 'ar' for Arabic, 'en' for English, 'es' for Spanish.

Text:
{text[:500]}

Language code:"""

            response = self._client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            
            lang_code = response.text.strip().lower()[:2]
            logger.info(f"Detected language: {lang_code}")
            return lang_code

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "fr"

    def translate_to_french(self, text: str, source_lang: Optional[str] = None) -> str:
        """
        Traduit un texte vers le français.
        
        Args:
            text: Texte à traduire
            source_lang: Langue source (optionnel, détectée automatiquement si None)
            
        Returns:
            Texte traduit en français
        """
        if not self._client:
            logger.warning("Translation client not initialized, returning original text")
            return text

        if not text or len(text.strip()) < 10:
            return text

        # Détection automatique si langue source non fournie
        if not source_lang:
            source_lang = self.detect_language(text)

        # Si déjà en français, pas besoin de traduire
        if source_lang == "fr":
            logger.info("Text already in French, skipping translation")
            return text

        try:
            prompt = f"""Translate the following text from {source_lang} to French. 
Preserve the original meaning and tone. Return ONLY the translated text, without any explanations or metadata.

Text to translate:
{text}

French translation:"""

            response = self._client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            
            translated = response.text.strip()
            logger.info(f"Translated {len(text)} chars from {source_lang} to French")
            return translated

        except Exception as e:
            logger.error(f"Translation to French failed: {e}")
            return text

    def translate_to_english(self, text: str) -> str:
        """
        Traduit un texte vers l'anglais.
        
        Args:
            text: Texte à traduire (généralement en français)
            
        Returns:
            Texte traduit en anglais
        """
        if not self._client:
            logger.warning("Translation client not initialized, returning original text")
            return text

        if not text or len(text.strip()) < 10:
            return text

        try:
            prompt = f"""Translate the following text to English. 
Preserve the original meaning and tone. Return ONLY the translated text, without any explanations or metadata.

Text to translate:
{text}

English translation:"""

            response = self._client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            
            translated = response.text.strip()
            logger.info(f"Translated {len(text)} chars to English")
            return translated

        except Exception as e:
            logger.error(f"Translation to English failed: {e}")
            return text


# Singleton instance
_translation_service: Optional[TranslationService] = None


def get_translation_service() -> TranslationService:
    """Retourne l'instance singleton du service de traduction."""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service

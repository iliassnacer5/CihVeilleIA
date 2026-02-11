from __future__ import annotations

import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Iterable, List, Optional

from bs4 import BeautifulSoup
from langdetect import DetectorFactory, LangDetectException, detect
import dateparser

from app.nlp.preprocessing import normalize_text

# Rendre langdetect déterministe
DetectorFactory.seed = 0


@dataclass
class RawTextDocument:
    """Représente un document texte brut issu du scraping.

    Attributs:
        id: identifiant interne du document.
        title: titre éventuel.
        url: URL source (pour la traçabilité).
        raw_text: texte brut ou HTML.
        published_at: date brute (str ou datetime) si disponible.
    """

    id: str
    raw_text: str
    title: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[object] = None  # str | datetime | None


@dataclass
class CleanTextDocument:
    """Document nettoyé, prêt pour les traitements NLP / RAG."""

    id: str
    text: str
    lang: Optional[str]
    title: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None

    def to_json_dict(self) -> dict:
        """Retourne une version JSON-sérialisable."""
        data = asdict(self)
        if self.published_at is not None:
            data["published_at"] = self.published_at.isoformat()
        return data


class TextCleaner:
    """Module de nettoyage textuel pour pipeline IA bancaire.

    Fonctionnalités:
    - suppression du bruit HTML;
    - normalisation de dates hétérogènes;
    - détection de langue;
    - suppression de doublons (sur texte nettoyé + URL).
    """

    def strip_html(self, text: str) -> str:
        """Supprime le bruit HTML et retourne le texte brut."""
        # Certains textes peuvent déjà être "propres", BeautifulSoup reste robuste
        soup = BeautifulSoup(text or "", "html.parser")
        return soup.get_text(separator=" ", strip=True)

    def normalize_date(self, raw_date: object) -> Optional[datetime]:
        """Normalise une date (str ou datetime) en datetime standard.

        Utilise `dateparser` pour supporter plusieurs formats et langues.
        """
        if raw_date is None:
            return None
        if isinstance(raw_date, datetime):
            return raw_date

        if isinstance(raw_date, str) and raw_date.strip():
            dt = dateparser.parse(raw_date)
            return dt

        return None

    def detect_language(self, text: str) -> Optional[str]:
        """Détecte la langue principale du texte (code ISO, ex: 'fr', 'en')."""
        cleaned = (text or "").strip()
        if not cleaned:
            return None

        try:
            lang = detect(cleaned)
            return lang
        except LangDetectException:
            return None

    def _make_dedup_key(self, doc: CleanTextDocument) -> str:
        """Construit une clé de dédoublonnage basée sur texte + URL."""
        base = (doc.text or "").lower().strip()
        if doc.url:
            base += f"||{doc.url.lower().strip()}"
        # Hash pour éviter de garder de très longues clés en mémoire
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def deduplicate(self, docs: Iterable[CleanTextDocument]) -> List[CleanTextDocument]:
        """Supprime les doublons (même texte+URL) en conservant le premier."""
        seen: set[str] = set()
        unique_docs: List[CleanTextDocument] = []

        for doc in docs:
            key = self._make_dedup_key(doc)
            if key in seen:
                continue
            seen.add(key)
            unique_docs.append(doc)

        return unique_docs

    def clean_documents(self, raw_docs: Iterable[RawTextDocument]) -> List[CleanTextDocument]:
        """Pipeline complet de nettoyage pour une collection de documents.

        Étapes:
        1. suppression du HTML;
        2. normalisation textuelle (espaces, sauts de ligne);
        3. normalisation de la date;
        4. détection de langue;
        5. suppression des doublons.
        """
        cleaned_docs: List[CleanTextDocument] = []

        for raw in raw_docs:
            # 1) HTML -> texte
            stripped = self.strip_html(raw.raw_text)

            # 2) normalisation de base
            normalized_text = normalize_text(stripped)

            # skip documents vides
            if not normalized_text:
                continue

            # 3) date
            normalized_date = self.normalize_date(raw.published_at)

            # 4) langue
            lang = self.detect_language(normalized_text)

            cleaned_docs.append(
                CleanTextDocument(
                    id=raw.id,
                    text=normalized_text,
                    lang=lang,
                    title=raw.title,
                    url=raw.url,
                    published_at=normalized_date,
                )
            )

        # 5) suppression des doublons
        return self.deduplicate(cleaned_docs)


def clean_documents_to_json(raw_docs: Iterable[RawTextDocument]) -> List[dict]:
    """Helper pratique pour obtenir directement une liste de dictionnaires JSON.

    Exemple d'utilisation dans un pipeline:

    >>> from app.scraping.institutional_scraper import InstitutionalDocument
    >>> from app.nlp.cleaning import RawTextDocument, clean_documents_to_json
    >>>
    >>> scraped_docs: list[InstitutionalDocument] = ...
    >>> raw_docs = [
    ...     RawTextDocument(
    ...         id=doc.id,
    ...         raw_text=doc.raw_text,
    ...         title=doc.title,
    ...         url=doc.url,
    ...         published_at=doc.published_at,
    ...     )
    ...     for doc in scraped_docs
    ... ]
    >>> cleaned_json = clean_documents_to_json(raw_docs)
    """
    cleaner = TextCleaner()
    cleaned_docs = cleaner.clean_documents(raw_docs)
    return [doc.to_json_dict() for doc in cleaned_docs]


from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence
import logging

from transformers import pipeline

logger = logging.getLogger(__name__)


@dataclass
class BankingClassificationResult:
    """Résultat de classification thématique bancaire pour un document."""

    text: str
    label: str
    score: float
    all_labels: List[str]
    all_scores: List[float]


@dataclass
class BankingEntity:
    """Entité extraite d'un document (organismes, produits financiers, etc.)."""

    text: str
    label: str
    score: float
    start: int
    end: int


@dataclass
class BankingSummary:
    """Résumé court et fiable d'un document."""

    original_text: str
    summary: str


class BankingNlpService:
    """Service NLP bancaire haute performance pour CIH Veille IA.

    Fonctionnalités:
    - classification thématique zero-shot (XLM-RoBERTa Large);
    - extraction d'entités nommées (CamemBERT NER);
    - génération de résumés via Google Gemini (qualité professionnelle).

    Les modèles par défaut sont:
    - classification: XLM-RoBERTa Large XNLI (`joeddav/xlm-roberta-large-xnli`);
    - NER: CamemBERT NER (`Jean-Baptiste/camembert-ner`);
    - résumé: Google Gemini 2.0 Flash (via API).
    """

    def __init__(
        self,
        classifier_model: str = "joeddav/xlm-roberta-large-xnli",  # Meilleur zero-shot multilingue
        ner_model: str = "Jean-Baptiste/camembert-ner",  # Meilleur NER français
        summarizer_model: str = "Falconsai/text_summarization",  # Fallback local si pas de Gemini
        device: int | str | None = None,
    ) -> None:
        """Initialise les noms de modèles sans charger les pipelines immédiatement.

        Args:
            classifier_model: modèle zero-shot multilingue.
            ner_model: modèle NER français.
            summarizer_model: modèle de summarization local (fallback).
            device: index GPU (0,1,...) ou -1 / None pour CPU.
        """
        self.model_names = {
            "classifier": classifier_model,
            "ner": ner_model,
            "summarizer": summarizer_model,
        }
        self.device = device if isinstance(device, int) else -1
        
        # Les pipelines seront chargés paresseusement (Lazy Loading)
        self._classifier_pipeline = None
        self._ner_pipeline = None
        self._summarizer_pipeline = None
        self._gemini_client = None
        self._gemini_available = None  # None = pas encore vérifié

        # Thématiques bancaires élargies pour CIH Bank
        self.default_topics: List[str] = [
            "réglementation bancaire",
            "lutte contre le blanchiment (LCB-FT)",
            "risque de crédit",
            "risque opérationnel",
            "risque de marché",
            "cybersécurité",
            "protection des données personnelles",
            "paiements et moyens de paiement",
            "banque de détail",
            "banque de financement et d'investissement",
            "innovation et fintech",
            "intelligence artificielle en banque",
            "durabilité et finance verte",
            "inclusion financière",
            "politique monétaire",
            "taux d'intérêt et marché obligataire",
            "immobilier et crédit hypothécaire",
            "transformation digitale",
            "gouvernance d'entreprise",
            "conformité et contrôle interne",
        ]

    def _get_gemini_client(self):
        """Initialise le client Gemini pour les résumés haute qualité."""
        if self._gemini_available is None:
            try:
                from google import genai
                from app.config.settings import settings
                if getattr(settings, "gemini_api_key", None):
                    self._gemini_client = genai.Client(api_key=settings.gemini_api_key)
                    self._gemini_available = True
                    logger.info("✅ Gemini available for high-quality summarization")
                else:
                    self._gemini_available = False
            except Exception as e:
                logger.warning(f"Gemini not available for summarization: {e}")
                self._gemini_available = False
        return self._gemini_client

    @property
    def _classifier(self):
        if self._classifier_pipeline is None:
            logger.info(f"Loading classifier: {self.model_names['classifier']}...")
            self._classifier_pipeline = pipeline(
                "zero-shot-classification",
                model=self.model_names["classifier"],
                device=self.device,
            )
            logger.info("✅ Classifier loaded.")
        return self._classifier_pipeline

    @property
    def _ner(self):
        if self._ner_pipeline is None:
            logger.info(f"Loading NER: {self.model_names['ner']}...")
            self._ner_pipeline = pipeline(
                "token-classification",
                model=self.model_names["ner"],
                aggregation_strategy="simple",
                device=self.device,
            )
            logger.info("✅ NER loaded.")
        return self._ner_pipeline

    @property
    def _summarizer(self):
        if self._summarizer_pipeline is None:
            logger.info(f"Loading local summarizer: {self.model_names['summarizer']}...")
            self._summarizer_pipeline = pipeline(
                "summarization",
                model=self.model_names["summarizer"],
                device=self.device,
                truncation=True,
            )
            logger.info("✅ Local summarizer loaded.")
        return self._summarizer_pipeline

    # ---------------------------------------------------------------------
    # Classification thématique (XLM-RoBERTa Large)
    # ---------------------------------------------------------------------
    def classify_documents(
        self,
        texts: Sequence[str],
        candidate_labels: Optional[Sequence[str]] = None,
        multi_label: bool = True,
    ) -> List[BankingClassificationResult]:
        """Classe les documents selon des thématiques bancaires.

        Args:
            texts: liste de textes à classer.
            candidate_labels: thématiques candidates. Si None, on utilise
                un set de thématiques bancaires par défaut.
            multi_label: autoriser plusieurs labels pertinents par document.
        """
        if candidate_labels is None:
            candidate_labels = self.default_topics

        results: List[BankingClassificationResult] = []

        for text in texts:
            if not text or not text.strip():
                results.append(
                    BankingClassificationResult(
                        text=text,
                        label="inconnu",
                        score=0.0,
                        all_labels=[],
                        all_scores=[],
                    )
                )
                continue

            # Tronquer pour éviter les problèmes de mémoire sur les gros docs
            truncated = text[:1500] if len(text) > 1500 else text

            output = self._classifier(
                truncated,
                candidate_labels=list(candidate_labels),
                multi_label=multi_label,
            )

            labels = list(output["labels"])
            scores = [float(s) for s in output["scores"]]

            top_label = labels[0] if labels else "inconnu"
            top_score = scores[0] if scores else 0.0

            results.append(
                BankingClassificationResult(
                    text=text,
                    label=top_label,
                    score=top_score,
                    all_labels=labels,
                    all_scores=scores,
                )
            )

        return results

    # ---------------------------------------------------------------------
    # Extraction d'entités bancaires (CamemBERT NER)
    # ---------------------------------------------------------------------
    def extract_entities(
        self,
        texts: Sequence[str],
        score_threshold: float = 0.6,
    ) -> List[List[BankingEntity]]:
        """Extrait les entités clés dans chaque document.

        Args:
            texts: liste de textes.
            score_threshold: score minimum pour conserver une entité.
        """
        all_entities: List[List[BankingEntity]] = []

        for text in texts:
            if not text or not text.strip():
                all_entities.append([])
                continue

            # Tronquer pour les gros documents
            truncated = text[:2000] if len(text) > 2000 else text
            raw_entities = self._ner(truncated)

            entities: List[BankingEntity] = []
            seen = set()  # Déduplications des entités
            for ent in raw_entities:
                score = float(ent.get("score", 0.0))
                if score < score_threshold:
                    continue

                word = ent.get("word", "").strip()
                if not word or word in seen or len(word) < 2:
                    continue
                seen.add(word)

                entities.append(
                    BankingEntity(
                        text=word,
                        label=ent.get("entity_group") or ent.get("entity") or "ENT",
                        score=score,
                        start=int(ent.get("start", 0)),
                        end=int(ent.get("end", 0)),
                    )
                )

            all_entities.append(entities)

        return all_entities

    # ---------------------------------------------------------------------
    # Résumé de documents (Gemini prioritaire, fallback local)
    # ---------------------------------------------------------------------
    def summarize_documents(
        self,
        texts: Sequence[str],
        max_length: int = 120,
        min_length: int = 30,
    ) -> List[BankingSummary]:
        """Génère des résumés courts de documents bancaires.

        Utilise Gemini pour des résumés FR de haute qualité.
        Fallback sur le modèle local si Gemini n'est pas disponible.
        """
        summaries: List[BankingSummary] = []

        for text in texts:
            if not text or not text.strip():
                summaries.append(BankingSummary(original_text=text, summary=""))
                continue

            # Essayer Gemini d'abord (meilleure qualité)
            gemini = self._get_gemini_client()
            if gemini:
                try:
                    summary = self._summarize_with_gemini(text)
                    summaries.append(BankingSummary(original_text=text, summary=summary))
                    continue
                except Exception as e:
                    logger.warning(f"Gemini summarization failed, falling back: {e}")

            # Fallback: modèle local
            truncated_text = text[:2048] if len(text) > 2048 else text
            output = self._summarizer(
                truncated_text,
                max_length=max_length,
                min_length=min(min_length, max_length - 1),
                do_sample=False,
                truncation=True,
            )
            summary_text = output[0]["summary_text"]
            summaries.append(BankingSummary(original_text=text, summary=summary_text.strip()))

        return summaries

    def _summarize_with_gemini(self, text: str) -> str:
        """Génère un résumé professionnel via Gemini."""
        # Tronquer si nécessaire (Gemini peut gérer beaucoup mais on est prudent)
        truncated = text[:8000] if len(text) > 8000 else text

        prompt = f"""Tu es un analyste de veille réglementaire et bancaire pour CIH Bank (Maroc).
Génère un résumé professionnel et structuré du document suivant.

Règles :
1. Le résumé doit faire entre 3 et 5 phrases.
2. Mentionne les points clés, chiffres importants et implications pour le secteur bancaire.
3. Réponds UNIQUEMENT en français.
4. Ne commence pas par "Ce document" ou "Cet article", commence directement par le contenu.

Document :
{truncated}

Résumé professionnel :"""

        response = self._gemini_client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=prompt,
        )
        return response.text.strip()

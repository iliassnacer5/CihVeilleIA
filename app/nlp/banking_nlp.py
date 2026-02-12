from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from transformers import pipeline


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
    """Service NLP bancaire basé sur Transformers.

    Fonctionnalités:
    - classification thématique des documents;
    - extraction d'entités nommées (organismes, produits, etc.);
    - génération de résumés courts.

    Les modèles par défaut sont:
    - classification: DeBERTa multilingue (`MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`);
    - NER: CamemBERT NER (`Jean-Baptiste/camembert-ner`);
    - résumé: mT5 multilingue (`csebuetnlp/mT5_multilingual_XLSum`).

    Tu peux surcharger les noms de modèles via le constructeur.
    """

    def __init__(
        self,
        classifier_model: str = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli", # Multilingue robuste
        ner_model: str = "Jean-Baptiste/camembert-ner", # Excellent pour le Français
        summarizer_model: str = "csebuetnlp/mT5_multilingual_XLSum", # Spécialisé multilingue (XLSum)
        device: int | str | None = None,
    ) -> None:
        """Initialise les noms de modèles sans charger les pipelines immédiatement.

        Args:
            classifier_model: modèle zero-shot multilingue.
            ner_model: modèle NER multilingue.
            summarizer_model: modèle de summarization.
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

        # Thématiques bancaires par défaut
        self.default_topics: List[str] = [
            "réglementation bancaire",
            "lutte contre le blanchiment (LCB-FT)",
            "risque de crédit",
            "risque opérationnel",
            "cybersécurité",
            "paiements et moyens de paiement",
            "banque de détail",
            "banque de financement et d'investissement",
            "innovation et fintech",
            "intelligence artificielle en banque",
            "durabilité et finance verte",
        ]

    @property
    def _classifier(self):
        if self._classifier_pipeline is None:
            self._classifier_pipeline = pipeline(
                "zero-shot-classification",
                model=self.model_names["classifier"],
                device=self.device,
            )
        return self._classifier_pipeline

    @property
    def _ner(self):
        if self._ner_pipeline is None:
            self._ner_pipeline = pipeline(
                "token-classification",
                model=self.model_names["ner"],
                aggregation_strategy="simple",
                device=self.device,
            )
        return self._ner_pipeline

    @property
    def _summarizer(self):
        if self._summarizer_pipeline is None:
            self._summarizer_pipeline = pipeline(
                "summarization",
                model=self.model_names["summarizer"],
                device=self.device,
            )
        return self._summarizer_pipeline

    # ---------------------------------------------------------------------
    # Classification thématique
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

            output = self._classifier(
                text,
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
    # Extraction d'entités bancaires
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

            raw_entities = self._ner(text)

            entities: List[BankingEntity] = []
            for ent in raw_entities:
                score = float(ent.get("score", 0.0))
                if score < score_threshold:
                    continue

                entities.append(
                    BankingEntity(
                        text=ent.get("word", ""),
                        label=ent.get("entity_group") or ent.get("entity") or "ENT",
                        score=score,
                        start=int(ent.get("start", 0)),
                        end=int(ent.get("end", 0)),
                    )
                )

            all_entities.append(entities)

        return all_entities

    # ---------------------------------------------------------------------
    # Résumé de documents
    # ---------------------------------------------------------------------
    def summarize_documents(
        self,
        texts: Sequence[str],
        max_length: int = 120,
        min_length: int = 30,
    ) -> List[BankingSummary]:
        """Génère des résumés courts de documents bancaires.

        Args:
            texts: liste de documents.
            max_length: longueur max du résumé (tokens du modèle).
            min_length: longueur min du résumé.
        """
        summaries: List[BankingSummary] = []

        for text in texts:
            if not text or not text.strip():
                summaries.append(
                    BankingSummary(
                        original_text=text,
                        summary="",
                    )
                )
                continue

            # Certains modèles sont sensibles à la longueur; on tronque si besoin
            # La gestion fine des longueurs peut être adaptée pour un PFE.
            output = self._summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
            )

            summary_text = output[0]["summary_text"]

            summaries.append(
                BankingSummary(
                    original_text=text,
                    summary=summary_text.strip(),
                )
            )

        return summaries


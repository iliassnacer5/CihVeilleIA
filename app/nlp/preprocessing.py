from typing import List

import spacy

_nlp = spacy.blank("fr")
_nlp.add_pipe("sentencizer")


def normalize_text(text: str) -> str:
    """Nettoie et normalise un texte brut en français."""
    text = text.replace("\n", " ").strip()
    text = " ".join(text.split())
    return text


def split_sentences(text: str) -> List[str]:
    """Découpe un texte en phrases."""
    doc = _nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


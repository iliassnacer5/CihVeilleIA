from abc import ABC, abstractmethod
from typing import Iterable, Protocol


class ScrapedItem(Protocol):
    """Représente un document brut récupéré par le scraping."""

    id: str
    title: str
    url: str
    raw_text: str
    source: str


class BaseScraper(ABC):
    """Classe de base pour tous les scrapers de la plateforme."""

    source_name: str

    @abstractmethod
    def fetch(self) -> Iterable[ScrapedItem]:
        """Récupère les documents bruts depuis la source cible."""
        raise NotImplementedError


from dataclasses import dataclass
from typing import Iterable

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedItem


@dataclass
class NewsItem:
    id: str
    title: str
    url: str
    raw_text: str
    source: str = "generic_news"


class NewsScraper(BaseScraper):
    """Scraper d'actualités génériques sur l'IA pour le secteur bancaire.

    Cette implémentation est volontairement simple et devra être adaptée
    à des sources spécifiques (flux RSS, APIs, etc.) pour un PFE.
    """

    source_name = "generic_news"

    def __init__(self, base_url: str = "https://example.com"):
        self.base_url = base_url

    def fetch(self) -> Iterable[ScrapedItem]:
        response = httpx.get(self.base_url, timeout=10.0)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        articles = []

        for idx, article in enumerate(soup.find_all("article")[:10]):
            title_tag = article.find("h2") or article.find("h1")
            link_tag = article.find("a")

            title = title_tag.get_text(strip=True) if title_tag else "Untitled"
            url = link_tag["href"] if link_tag and link_tag.has_attr("href") else self.base_url
            raw_text = article.get_text(separator=" ", strip=True)

            articles.append(
                NewsItem(
                    id=f"{self.source_name}-{idx}",
                    title=title,
                    url=url,
                    raw_text=raw_text,
                    source=self.source_name,
                )
            )

        return articles


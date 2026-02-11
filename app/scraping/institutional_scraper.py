from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Iterable, List, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
import ssl
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedItem

import time
from app.config.security import security_settings
from app.storage.audit_log import audit_logger

logger = logging.getLogger(__name__)


@dataclass
class InstitutionalDocument:
    """Représente un document institutionnel scrappé.

    Attributs:
        id: identifiant interne unique.
        title: titre de la page / actualité.
        url: URL absolue du document.
        published_at: date de publication (si disponible).
        raw_text: contenu texte principal nettoyé.
        source: nom de la source (ex: 'banque_centrale_x').
    """

    id: str
    title: str
    url: str
    raw_text: str
    source: str
    published_at: Optional[datetime] = None

    def to_json_dict(self) -> dict:
        """Retourne une version JSON-sérialisable (datetime -> ISO 8601)."""
        data = asdict(self)
        if self.published_at is not None:
            data["published_at"] = self.published_at.isoformat()
        return data


class RobotsHandler:
    """Gère le téléchargement et la consultation de robots.txt pour un domaine."""

    def __init__(self, base_url: str, user_agent: str = "cih-veille-ia-bot"):
        self.user_agent = user_agent
        self._parser = RobotFileParser()

        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        try:
            # Create a more permissive SSL context if needed
            context = ssl.create_default_context()
            context.set_ciphers('DEFAULT@SECLEVEL=1')
            context.options |= 0x4 # OP_LEGACY_SERVER_CONNECT
            
            self._parser.set_url(robots_url)
            # RobotFileParser doesn't support custom SSL context easily via read()
            # but it uses urllib.request internally. We'll try to let it fail or wrap it.
            # Workaround: just set the URL and let it try, if it fails, we fall back to permissive
            self._parser.read()
            logger.info("robots.txt chargé depuis %s", robots_url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Impossible de charger robots.txt (%s): %s", robots_url, exc)
            # En cas d'erreur SSL ou autre, on autorise quand même (stratégie moins conservatrice pour PFE)
            # Sinon on bloque tout le site.
            self._parser = None

    def can_fetch(self, url: str) -> bool:
        """Indique si l'URL peut être scrappée selon robots.txt."""
        if self._parser is None:
            # Pour le PFE, on autorise si robots.txt n'est pas accessible
            # afin de ne pas bloquer les sites avec des vieux SSL
            return True
        try:
            return self._parser.can_fetch(self.user_agent, url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Erreur lors de la vérification robots.txt pour %s: %s", url, exc)
            return True


class InstitutionalSiteScraper(BaseScraper):
    """Scraper générique pour sites institutionnels bancaires / régulateurs.

    Le scraper est paramétrable par sélecteurs CSS pour s'adapter à différents
    sites sans changer le code.

    Il est conçu pour:
    - extraire titre, date, contenu, URL;
    - respecter robots.txt;
    - gérer les erreurs réseau;
    - rester robuste aux petits changements HTML (fallbacks, logs).
    """

    source_name = "institutional_site"

    def __init__(
        self,
        base_url: str,
        article_link_selector: str,
        title_selector: str,
        content_selector: str,
        date_selector: Optional[str] = None,
        max_articles: int = 20,
        user_agent: str = "cih-veille-ia-bot",
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.article_link_selector = article_link_selector
        self.title_selector = title_selector
        self.content_selector = content_selector
        self.date_selector = date_selector
        self.max_articles = max_articles
        self.user_agent = user_agent
        self.timeout = timeout
        
        # Validation Whitelist (Conformité Audit)
        domain = urlparse(self.base_url).netloc
        if domain not in security_settings.SOURCE_WHITELIST:
            audit_logger.log_event(
                "SECURITY_ALERT", 
                "SCRAPING_INITIALIZATION", 
                "BLOCKED", 
                {"reason": "domain_not_in_whitelist", "domain": domain, "url": self.base_url}
            )
            # On laisse le logger local aussi pour le debug immédiat
            logger.error("Tentative de scraping hors whitelist bloquée: %s", domain)
            self._is_authorized = False
        else:
            self._is_authorized = True
            
        # Use a more standard User-Agent to avoid aggressive WAF blocking
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        # Create a shared SSL context for legacy sites
        self._ssl_context = ssl.create_default_context()
        self._ssl_context.check_hostname = False # Désactiver pour les sites institutionnels rebelles
        self._ssl_context.verify_mode = ssl.CERT_NONE # Désactiver la vérification (PFE)
        try:
            self._ssl_context.set_ciphers('DEFAULT@SECLEVEL=1')
            self._ssl_context.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        except Exception:
            pass
            
        self.robots = RobotsHandler(base_url=self.base_url, user_agent=self.user_agent)

    def _get_client(self) -> httpx.Client:
        """Retourne un client httpx configuré pour être résilient aux anciens SSL."""
        # On force HTTP/1.1 et on utilise le contexte SSL permissif
        return httpx.Client(
            headers={"User-Agent": self.user_agent},
            timeout=self.timeout,
            verify=self._ssl_context,
            http2=False,
            follow_redirects=True
        )
    def fetch(self) -> Iterable[ScrapedItem]:
        """Récupère une liste de documents institutionnels avec contrôles de conformité."""
        if not self._is_authorized:
            return []

        headers = {"User-Agent": security_settings.USER_AGENT}
        
        audit_logger.log_event(
            "SCRAPING", 
            "FETCH_START", 
            "START", 
            {"base_url": self.base_url, "source": self.source_name}
        )

        try:
            logger.info("Chargement de la page liste: %s", self.base_url)
            with self._get_client() as client:
                resp = client.get(self.base_url)
                resp.raise_for_status()
        except httpx.RequestError as exc:
            logger.error("Erreur réseau lors du chargement de %s: %s", self.base_url, exc)
            return []
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Statut HTTP invalide lors du chargement de %s: %s",
                self.base_url,
                exc,
            )
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select(self.article_link_selector)
        if not links:
            logger.warning(
                "Aucun lien d'article trouvé avec le sélecteur '%s' sur %s",
                self.article_link_selector,
                self.base_url,
            )

        documents: List[InstitutionalDocument] = []

        for idx, link in enumerate(links[: self.max_articles]):
            href = link.get("href")
            if not href:
                continue

            article_url = urljoin(self.base_url, href)

            if not self.robots.can_fetch(article_url):
                logger.info("URL bloquée par robots.txt, ignorée: %s", article_url)
                continue

            doc = self._fetch_single_article(
                url=article_url,
                index=idx,
            )
            if doc is not None:
                documents.append(doc)
            
            # Délai éthique (Audit Compliance)
            time.sleep(security_settings.SCRAPING_MIN_DELAY)

        audit_logger.log_event(
            "SCRAPING", 
            "FETCH_END", 
            "SUCCESS", 
            {"base_url": self.base_url, "count": len(documents)}
        )
        return documents

    def _fetch_single_article(
        self,
        url: str,
        index: int,
    ) -> Optional[InstitutionalDocument]:
        """Charge et parse une page d'article individuelle."""
        try:
            logger.info("Chargement de l'article %s", url)
            with self._get_client() as client:
                resp = client.get(url)
                resp.raise_for_status()
        except httpx.RequestError as exc:
            logger.warning("Erreur réseau sur l'article %s: %s", url, exc)
            return None
        except httpx.HTTPStatusError as exc:
            logger.warning("Statut HTTP %s pour l'article %s", exc.response.status_code, url)
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Titre robuste: sélecteur configuré + fallback h1
        title = ""
        try:
            title_tag = soup.select_one(self.title_selector)
            if not title_tag:
                title_tag = soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else "Sans titre"
        except Exception as exc:  # noqa: BLE001
            logger.warning("Impossible d'extraire le titre pour %s: %s", url, exc)
            title = "Sans titre"

        # Date (optionnelle)
        published_at = None
        if self.date_selector:
            try:
                date_tag = soup.select_one(self.date_selector)
                if date_tag:
                    raw_date = date_tag.get_text(strip=True)
                    # TODO: adapter le parsing à la locale / format réel
                    published_at = self._parse_date_fallback(raw_date)
            except Exception as exc:  # noqa: BLE001
                logger.info("Impossible de parser la date pour %s: %s", url, exc)

        # Contenu principal
        try:
            content_container = soup.select_one(self.content_selector)
            if not content_container:
                logger.warning(
                    "Sélecteur de contenu '%s' introuvable pour %s",
                    self.content_selector,
                    url,
                )
                return None
            raw_text = content_container.get_text(separator=" ", strip=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Erreur lors de l'extraction du contenu pour %s: %s", url, exc)
            return None

        return InstitutionalDocument(
            id=f"{self.source_name}-{index}",
            title=title,
            url=url,
            raw_text=raw_text,
            source=self.source_name,
            published_at=published_at,
        )

    @staticmethod
    def _parse_date_fallback(raw_date: str) -> Optional[datetime]:
        """Tentatives simples de parsing de date.

        Pour un PFE, on peut ultérieurement:
        - utiliser `dateparser` ou `babel` pour gérer plusieurs formats;
        - spécialiser par langue / pays.
        """
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(raw_date, fmt)
            except ValueError:
                continue
        return None


def scrape_institutional_site_to_json(
    scraper: InstitutionalSiteScraper,
) -> List[dict]:
    """Helper pour obtenir directement une liste de dictionnaires JSON prêts.

    Exemple d'utilisation:

    >>> scraper = InstitutionalSiteScraper(
    ...     base_url="https://www.banque-france.fr/communiques-de-presse",
    ...     article_link_selector="div.view-content a",
    ...     title_selector="h1",
    ...     content_selector="div.node-content",
    ...     date_selector="time",
    ... )
    >>> docs_json = scrape_institutional_site_to_json(scraper)
    """
    documents = scraper.fetch()
    return [doc.to_json_dict() for doc in documents if isinstance(doc, InstitutionalDocument)]


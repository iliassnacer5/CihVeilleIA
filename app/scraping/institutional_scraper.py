from __future__ import annotations

import logging
import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Iterable, List, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
import ssl
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedItem
from app.config.security import security_settings
from app.storage.audit_log import audit_logger

logger = logging.getLogger(__name__)


@dataclass
class InstitutionalDocument:
    """Représente un document institutionnel scrappé."""

    id: str
    title: str
    url: str
    raw_text: str
    source: str
    category: str
    doc_type: str
    published_at: Optional[datetime] = None

    def to_json_dict(self) -> dict:
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
            self._parser.set_url(robots_url)
            self._parser.read()
            logger.info("robots.txt chargé depuis %s", robots_url)
        except Exception as exc:
            logger.warning("Impossible de charger robots.txt (%s): %s", robots_url, exc)
            self._parser = None

    def can_fetch(self, url: str) -> bool:
        if self._parser is None:
            return True
        try:
            return self._parser.can_fetch(self.user_agent, url)
        except Exception:
            return True


class InstitutionalSiteScraper(BaseScraper):
    """Scraper générique pour sites institutionnels bancaires / régulateurs.

    Paramétrable par sélecteurs CSS. Inclut:
    - Auto-découverte si les sélecteurs échouent
    - Extraction multi-stratégie (titre, contenu)
    - Respect de robots.txt
    - Requêtes 100% asynchrones (pas de blocking)
    """

    source_name = "institutional_site"

    def __init__(
        self,
        base_url: str,
        article_link_selector: str,
        title_selector: str,
        content_selector: str,
        category: str = "Général",
        doc_type: str = "News",
        date_selector: Optional[str] = None,
        max_articles: int = 10,
        user_agent: str = "cih-veille-ia-bot",
        timeout: float = 15.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.article_link_selector = article_link_selector
        self.title_selector = title_selector
        self.content_selector = content_selector
        self.category = category
        self.doc_type = doc_type
        self.date_selector = date_selector
        self.max_articles = max_articles
        self.timeout = timeout
        
        # Domain whitelist check
        domain = urlparse(self.base_url).netloc
        self._domain = domain
        if domain not in security_settings.SOURCE_WHITELIST:
            logger.error("Tentative de scraping hors whitelist bloquée: %s", domain)
            self._is_authorized = False
        else:
            self._is_authorized = True
            
        # Standard User-Agent (avoid WAF blocking)
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        # Permissive SSL context for legacy institutional sites
        self._ssl_context = ssl.create_default_context()
        self._ssl_context.check_hostname = False
        self._ssl_context.verify_mode = ssl.CERT_NONE
        try:
            self._ssl_context.set_ciphers('DEFAULT@SECLEVEL=1')
            self._ssl_context.options |= 0x4
        except Exception:
            pass
            
        self.robots = RobotsHandler(base_url=self.base_url, user_agent=self.user_agent)

    def _get_async_client(self) -> httpx.AsyncClient:
        """Retourne un client httpx ASYNC configuré pour être résilient aux anciens SSL."""
        return httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            timeout=httpx.Timeout(self.timeout, connect=10.0),
            verify=self._ssl_context,
            http2=False,
            follow_redirects=True
        )

    def _auto_discover_links(self, soup: BeautifulSoup) -> List[str]:
        """
        Fallback: auto-découverte de liens d'articles quand les sélecteurs CSS échouent.
        """
        base_domain = urlparse(self.base_url).netloc
        base_path = urlparse(self.base_url).path.rstrip("/")
        
        exclude_patterns = [
            '#', 'javascript:', 'mailto:', '.pdf', '.doc', '.xls',
            '/login', '/contact', '/search', '/rss', '/feed',
            'twitter.com', 'facebook.com', 'linkedin.com', 'youtube.com',
            'instagram.com', '/sitemap', '/terms', '/privacy', '/cookie',
        ]
        
        discovered = []
        all_links = soup.find_all("a", href=True)
        
        for link in all_links:
            href = link.get("href", "")
            if not href:
                continue
                
            if any(pat in href.lower() for pat in exclude_patterns):
                continue
            
            full_url = urljoin(self.base_url, href)
            parsed = urlparse(full_url)
            
            # Same domain only
            if parsed.netloc != base_domain:
                continue
                
            link_path = parsed.path.rstrip("/")
            if link_path == base_path:
                continue
                
            # Must be deeper or have at least 2 path segments
            if base_path and not link_path.startswith(base_path):
                segments = [s for s in link_path.split("/") if s]
                if len(segments) < 2:
                    continue
            
            text = link.get_text(strip=True)
            if len(text) < 5:
                continue
            
            if full_url not in discovered:
                discovered.append(full_url)
        
        return discovered

    async def fetch(self) -> List[ScrapedItem]:
        """Récupère une liste de documents institutionnels — 100% ASYNC."""
        if not self._is_authorized:
            return []

        await audit_logger.log_event(
            "SCRAPING", 
            "FETCH_START", 
            "START", 
            {"base_url": self.base_url, "source": self.source_name}
        )

        try:
            logger.info("Chargement de la page liste: %s", self.base_url)
            async with self._get_async_client() as client:
                resp = await client.get(self.base_url)
                resp.raise_for_status()
        except httpx.RequestError as exc:
            logger.error("Erreur réseau lors du chargement de %s: %s", self.base_url, exc)
            return []
        except httpx.HTTPStatusError as exc:
            logger.error("Statut HTTP %s lors du chargement de %s", exc.response.status_code, self.base_url)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        
        # --- Strategy 1: Try configured selector(s) ---
        article_urls = []
        selectors = [s.strip() for s in self.article_link_selector.split(",")]
        
        for selector in selectors:
            try:
                links = soup.select(selector)
                for link in links:
                    href = link.get("href")
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if full_url not in article_urls:
                            article_urls.append(full_url)
            except Exception as e:
                logger.warning(f"Selector '{selector}' failed: {e}")
        
        logger.info(f"Primary selector found {len(article_urls)} links on {self.base_url}")
        
        # --- Strategy 2: Auto-discovery fallback ---
        if not article_urls:
            logger.warning("Primary selector found 0 articles, trying auto-discovery...")
            article_urls = self._auto_discover_links(soup)
            logger.info(f"Auto-discovery found {len(article_urls)} potential articles")

        # Deduplicate and limit
        seen = set()
        unique_urls = []
        for url in article_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        article_urls = unique_urls[:self.max_articles]

        documents: List[InstitutionalDocument] = []

        for idx, article_url in enumerate(article_urls):
            if not self.robots.can_fetch(article_url):
                logger.info("URL bloquée par robots.txt: %s", article_url)
                continue

            doc = await self._fetch_single_article(article_url, idx)
            if doc is not None:
                documents.append(doc)
            
            # Ethical delay — ASYNC (non-blocking)
            await asyncio.sleep(security_settings.SCRAPING_MIN_DELAY)

        await audit_logger.log_event(
            "SCRAPING", 
            "FETCH_END", 
            "SUCCESS", 
            {"base_url": self.base_url, "count": len(documents)}
        )
        return documents

    async def _fetch_single_article(
        self,
        url: str,
        index: int,
    ) -> Optional[InstitutionalDocument]:
        """Charge et parse une page d'article individuelle — ASYNC."""
        try:
            logger.info("Chargement de l'article [%d]: %s", index, url)
            async with self._get_async_client() as client:
                resp = await client.get(url)
                resp.raise_for_status()
        except httpx.RequestError as exc:
            logger.warning("Erreur réseau sur l'article %s: %s", url, exc)
            return None
        except httpx.HTTPStatusError as exc:
            logger.warning("Statut HTTP %s pour l'article %s", exc.response.status_code, url)
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # ── Title extraction (multi-strategy) ──
        title = None
        for sel in [s.strip() for s in self.title_selector.split(",")]:
            try:
                tag = soup.select_one(sel)
                if tag:
                    title = tag.get_text(strip=True)
                    if title:
                        break
            except:
                continue
        if not title:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)
        if not title:
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)
        if not title:
            title = "Sans titre"

        # ── Date (optional) ──
        published_at = None
        if self.date_selector:
            try:
                date_tag = soup.select_one(self.date_selector)
                if date_tag:
                    raw_date = date_tag.get_text(strip=True)
                    published_at = self._parse_date_fallback(raw_date)
            except Exception:
                pass

        # ── Content extraction (multi-strategy) ──
        raw_text = None
        for sel in [s.strip() for s in self.content_selector.split(",")]:
            try:
                container = soup.select_one(sel)
                if container:
                    text = container.get_text(separator=" ", strip=True)
                    if len(text) > 100:
                        raw_text = text
                        break
            except:
                continue
        
        # Fallback: common content containers
        if not raw_text:
            fallbacks = [
                "article", "main", "div.content", "div.article-content",
                "div.body-copy", "div.post-content", "div.entry-content",
                "div.field-items", "div.node-content", "div.text-content",
            ]
            for f in fallbacks:
                try:
                    container = soup.select_one(f)
                    if container:
                        text = container.get_text(separator=" ", strip=True)
                        if len(text) > 100:
                            raw_text = text
                            break
                except:
                    continue
        
        # Last resort: all <p> tags
        if not raw_text:
            paragraphs = soup.find_all("p")
            combined = " ".join(p.get_text(strip=True) for p in paragraphs)
            if len(combined) > 50:
                raw_text = combined
        
        if not raw_text:
            logger.warning("No content found for %s", url)
            return None

        # Truncate very long texts
        if len(raw_text) > 10000:
            raw_text = raw_text[:10000]

        return InstitutionalDocument(
            id=f"{self.source_name}-{index}",
            title=title,
            url=url,
            raw_text=raw_text,
            source=self.source_name,
            category=self.category,
            doc_type=self.doc_type,
            published_at=published_at,
        )

    @staticmethod
    def _parse_date_fallback(raw_date: str) -> Optional[datetime]:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %B %Y", "%d %b %Y"):
            try:
                return datetime.strptime(raw_date, fmt)
            except ValueError:
                continue
        return None

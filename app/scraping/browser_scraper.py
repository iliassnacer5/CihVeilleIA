import asyncio
import logging
from typing import Iterable, List, Optional
from playwright.async_api import async_playwright
from .base import BaseScraper, ScrapedItem
from .institutional_scraper import InstitutionalDocument
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from app.config.security import security_settings
from app.storage.audit_log import audit_logger

logger = logging.getLogger(__name__)

class BrowserScraper(BaseScraper):
    """
    Scraper basé sur un navigateur (Playwright) pour contourner les blocages 
    SSL, JavaScript ou WAF agressif.
    """
    source_name = "browser_site"

    def __init__(
        self,
        base_url: str,
        article_link_selector: str,
        title_selector: str,
        content_selector: str,
        category: str = "Général",
        doc_type: str = "News",
        date_selector: Optional[str] = None,
        max_articles: int = 5,
        timeout: float = 60000, # ms
        engine: str = "chromium"
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
        self.engine = engine
        
        domain = urlparse(self.base_url).netloc
        self._is_authorized = domain in security_settings.SOURCE_WHITELIST

    async def fetch(self) -> Iterable[ScrapedItem]:
        """Exécution asynchrone pour Playwright sur Windows avec ProactorLoop isolé."""
        if not self._is_authorized:
            return []
        
        # Sur Windows, Playwright nécessite ProactorEventLoop pour les sous-processus.
        # Si la boucle principale n'est pas compatible (ex: SelectorLoop), on exécute 
        # le travail dans un thread séparé avec sa propre boucle Proactor.
        import sys
        import threading
        from concurrent.futures import Future

        if sys.platform == "win32":
            def _run_async_work(future):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # Forcer le policy dans ce thread
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                    # Recréer la boucle avec le nouveau policy
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    result = loop.run_until_complete(self._async_fetch())
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
                finally:
                    loop.close()

            f = Future()
            t = threading.Thread(target=_run_async_work, args=(f,))
            t.start()
            # On attend le résultat asynchronement dans le thread principal (FastAPI)
            return await asyncio.wrap_future(f)
        else:
            return await self._async_fetch()

    async def _async_fetch(self) -> List[ScrapedItem]:
        documents = []
        async with async_playwright() as p:
            # Sélection de l'engine
            if self.engine == "firefox":
                browser_type = p.firefox
            elif self.engine == "webkit":
                browser_type = p.webkit
            else:
                browser_type = p.chromium
                
            browser = await browser_type.launch(headless=True)
            # On ignore les erreurs SSL au niveau du navigateur
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()
            
            try:
                logger.info(f"Navigate to {self.base_url} with Playwright")
                await page.goto(self.base_url, timeout=self.timeout, wait_until="domcontentloaded")
                
                # Attendre un peu pour le JS si nécessaire
                await page.wait_for_timeout(2000)
                
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                links = soup.select(self.article_link_selector)
                
                article_urls = []
                for link in links[:self.max_articles]:
                    href = link.get("href")
                    if href:
                        article_urls.append(urljoin(self.base_url, href))
                
                logger.info(f"Found {len(article_urls)} potential articles")
                
                for idx, url in enumerate(article_urls):
                    try:
                        doc = await self._scrape_article(page, url, idx)
                        if doc:
                            documents.append(doc)
                    except Exception as e:
                        logger.error(f"Error scraping {url}: {e}")
            
            finally:
                await browser.close()
                
        return documents

    async def _scrape_article(self, page, url: str, index: int) -> Optional[ScrapedItem]:
        logger.info(f"Scraping article: {url}")
        await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        
        # Titre
        title_tag = soup.select_one(self.title_selector)
        if not title_tag:
            title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Sans titre"
        
        # Contenu
        content_container = soup.select_one(self.content_selector)
        if not content_container:
            # Fallbacks pour plus de robustesse (PFE)
            fallbacks = ["article", "main", "div.content", "div.article-content", "div.body-copy"]
            for f in fallbacks:
                content_container = soup.select_one(f)
                if content_container:
                    break
        
        if not content_container:
            logger.warning(f"No content container found for {url}")
            return None
        
        raw_text = content_container.get_text(separator=" ", strip=True)
        
        return InstitutionalDocument(
            id=f"{self.source_name}-{index}", # Plus simple pour éviter les collisions
            title=title,
            url=url,
            raw_text=raw_text,
            source=self.source_name,
            category=self.category,
            doc_type=self.doc_type
        )

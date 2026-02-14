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
    Inclut un mécanisme d'auto-découverte si le sélecteur principal échoue.
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
        timeout: float = 60000,  # ms
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
        self._domain = domain

    async def fetch(self) -> Iterable[ScrapedItem]:
        """Exécution asynchrone pour Playwright sur Windows."""
        if not self._is_authorized:
            logger.warning(f"Domain {self._domain} not in whitelist, skipping")
            return []
        
        import sys

        if sys.platform == "win32":
            # Playwright needs ProactorEventLoop on Windows — run in a separate thread
            def _run_in_thread():
                import asyncio
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._async_fetch())
                finally:
                    loop.close()
            
            return await asyncio.to_thread(_run_in_thread)
        else:
            return await self._async_fetch()

    def _auto_discover_links(self, soup: BeautifulSoup) -> List[str]:
        """
        Fallback: auto-découverte de liens d'articles quand le sélecteur CSS échoue.
        Cherche tous les <a href> internes qui pointent vers du contenu (pas navigation).
        """
        base_domain = urlparse(self.base_url).netloc
        base_path = urlparse(self.base_url).path.rstrip("/")
        
        # Patterns to exclude (navigation, scripts, images, anchors)
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
                
            # Skip excluded patterns
            if any(pat in href.lower() for pat in exclude_patterns):
                continue
            
            full_url = urljoin(self.base_url, href)
            parsed = urlparse(full_url)
            
            # Must be same domain
            if parsed.netloc != base_domain:
                continue
                
            # Must be a sub-path of the base URL or deeper content
            link_path = parsed.path.rstrip("/")
            
            # Skip if it's the exact same page
            if link_path == base_path:
                continue
                
            # Must be deeper than the listing page (more path segments)
            if base_path and not link_path.startswith(base_path):
                # Also accept if path is at least 3 segments deep (likely an article)
                segments = [s for s in link_path.split("/") if s]
                if len(segments) < 2:
                    continue
            
            # Has meaningful link text (not just icons or empty)
            text = link.get_text(strip=True)
            if len(text) < 5:
                continue
            
            # Deduplicate
            if full_url not in discovered:
                discovered.append(full_url)
        
        return discovered

    async def _async_fetch(self) -> List[ScrapedItem]:
        documents = []
        async with async_playwright() as p:
            if self.engine == "firefox":
                browser_type = p.firefox
            elif self.engine == "webkit":
                browser_type = p.webkit
            else:
                browser_type = p.chromium
                
            browser = await browser_type.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            
            context = await browser.new_context(
                ignore_https_errors=True,
                user_agent=security_settings.USER_AGENT
            )
            page = await context.new_page()
            
            try:
                logger.info(f"Navigate to {self.base_url} with Playwright")
                
                # Use domcontentloaded instead of networkidle (which hangs on gov sites)
                try:
                    await page.goto(self.base_url, timeout=30000, wait_until="domcontentloaded")
                except Exception as nav_err:
                    logger.warning(f"First navigation attempt failed: {nav_err}, retrying with 'commit'...")
                    try:
                        await page.goto(self.base_url, timeout=30000, wait_until="commit")
                    except Exception as nav_err2:
                        logger.error(f"Navigation failed completely: {nav_err2}")
                        await browser.close()
                        return documents
                
                # Wait for JS to render content (replaces networkidle)
                await page.wait_for_timeout(3000)
                
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                
                # --- Strategy 1: Try main selector ---
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
                
                logger.info(f"Primary selector found {len(article_urls)} links")
                
                # --- Strategy 2: Auto-discovery fallback ---
                if not article_urls:
                    logger.warning(f"Primary selector found 0 articles, trying auto-discovery...")
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
                logger.info(f"Scraping {len(article_urls)} articles from {self.base_url}")
                
                for idx, url in enumerate(article_urls):
                    try:
                        doc = await self._scrape_article(page, url, idx)
                        if doc:
                            documents.append(doc)
                    except Exception as e:
                        logger.error(f"Error scraping {url}: {e}")
            
            except Exception as e:
                logger.error(f"Browser scraping failed for {self.base_url}: {e}")
            finally:
                await browser.close()
                
        return documents

    async def _scrape_article(self, page, url: str, index: int) -> Optional[ScrapedItem]:
        logger.info(f"Scraping article [{index}]: {url}")
        try:
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            # Wait for main content
            try:
                await page.wait_for_timeout(1500)
            except:
                pass
        except Exception as e:
            logger.warning(f"Failed to load {url}: {e}")
            return None
        
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        
        # ── Title extraction (multi-strategy) ──
        title = None
        # Try configured selectors
        for sel in [s.strip() for s in self.title_selector.split(",")]:
            try:
                tag = soup.select_one(sel)
                if tag:
                    title = tag.get_text(strip=True)
                    if title:
                        break
            except:
                continue
        # Fallback: any h1
        if not title:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)
        # Fallback: page title
        if not title:
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)
        if not title:
            title = "Sans titre"
        
        # ── Content extraction (multi-strategy) ──
        raw_text = None
        # Try configured selectors
        for sel in [s.strip() for s in self.content_selector.split(",")]:
            try:
                container = soup.select_one(sel)
                if container:
                    text = container.get_text(separator=" ", strip=True)
                    if len(text) > 100:  # Must be substantial content
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
        
        # Last resort: extract all paragraph text
        if not raw_text:
            paragraphs = soup.find_all("p")
            combined = " ".join(p.get_text(strip=True) for p in paragraphs)
            if len(combined) > 50:
                raw_text = combined
        
        if not raw_text:
            logger.warning(f"No content found for {url}")
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
            doc_type=self.doc_type
        )

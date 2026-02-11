"""
Registre centralisé des sources de veille pour CIH Bank.
Contient uniquement les sources stables et fonctionnelles (Audit 2026).
"""

SOURCES_REGISTRY = {
    "imf_news": {
        "name": "International Monetary Fund",
        "base_url": "https://www.imf.org/en/news",
        "article_link_selector": "a[href*='/en/news/articles/']",
        "title_selector": "h1",
        "content_selector": "div.news-content",
        "use_browser": True,
    },
    "bis_press": {
        "name": "Bank for International Settlements",
        "base_url": "https://www.bis.org/press/index.htm",
        "article_link_selector": "a[href*='/press/p']",
        "title_selector": "h1.title",
        "content_selector": "div#cms-content",
    },
    "ecb_press": {
        "name": "European Central Bank",
        "base_url": "https://www.ecb.europa.eu/press/html/index.en.html",
        "article_link_selector": "dt a",
        "title_selector": "h1",
        "content_selector": "div.section",
    },
    "fed_press": {
        "name": "Federal Reserve (2025)",
        "base_url": "https://www.federalreserve.gov/newsevents/pressreleases/2025-press.htm",
        "article_link_selector": "div.eventlist__item a",
        "title_selector": "h1",
        "content_selector": "div#article",
        "use_browser": True,
    },
    "world_bank_news": {
        "name": "World Bank",
        "base_url": "https://www.worldbank.org/en/news/all",
        "article_link_selector": "a[href*='/en/news/press-release/']",
        "title_selector": "h1",
        "content_selector": "div.body-copy",
    },
}

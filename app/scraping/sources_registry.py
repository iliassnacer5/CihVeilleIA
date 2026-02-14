"""
Registre centralisé des sources de veille pour CIH Bank.
Périmètre PFE 2026: Régulateurs, Institutions, Presse Éco et Secteur Bancaire.

La whitelist de sécurité est générée automatiquement à partir de ce registre
dans security.py — chaque domaine listé ici est automatiquement autorisé.
"""

SOURCES_REGISTRY = {
    # ──────────────────────────────────────────────────────────
    # 1. RÉGULATEURS & INSTITUTIONS OFFICIELLES (MAROC)
    # ──────────────────────────────────────────────────────────

    "bam_news": {
        "name": "Bank Al-Maghrib - Communiqués",
        "base_url": "https://www.bkam.ma/fr/Communiques",
        "category": "Régulateurs & Institutions Officielles",
        "doc_type": "Communiqué",
        "article_link_selector": "a[href*='/fr/Communiques/']",
        "title_selector": "h1, h2.title",
        "content_selector": "div.content-block, div.field-items, article, main",
        "use_browser": True,
    },
    "bam_circulaires": {
        "name": "Bank Al-Maghrib - Circulaires",
        "base_url": "https://www.bkam.ma/fr/Supervision-bancaire/Reglementation-et-conformite/Circulaires",
        "category": "Régulateurs & Institutions Officielles",
        "doc_type": "Circulaire",
        "article_link_selector": "a[href*='/Circulaires/']",
        "title_selector": "h1, h2.title",
        "content_selector": "div.content-block, div.field-items, article, main",
        "use_browser": True,
    },
    "ammc_news": {
        "name": "AMMC - Communiqués",
        "base_url": "https://www.ammc.ma/fr/actualites",
        "category": "Régulateurs & Institutions Officielles",
        "doc_type": "Communiqué",
        "article_link_selector": "a[href*='/fr/actualites/']",
        "title_selector": "h1.page-header, h1",
        "content_selector": "div.field-items, div.content, article, main",
    },
    "me_news": {
        "name": "Ministère de l'Économie et des Finances",
        "base_url": "https://www.finances.gov.ma/fr/Pages/Actualites.aspx",
        "category": "Régulateurs & Institutions Officielles",
        "doc_type": "News",
        "article_link_selector": "a[href*='/Pages/'], a[href*='/actualites/'], h2 a, h3 a",
        "title_selector": "h1, h2",
        "content_selector": "div.content, article, main, div.ms-rtestate-field",
        "use_browser": True,
    },
    "cndp_news": {
        "name": "CNDP - Actualités",
        "base_url": "https://www.cndp.ma/",
        "category": "Régulateurs & Institutions Officielles",
        "doc_type": "News",
        "article_link_selector": "a[href*='cndp.ma/'][href*='-'], div.elementor-post a, h2 a, h3 a",
        "title_selector": "h1.entry-title, h1, h2",
        "content_selector": "div.entry-content, article, main, div.elementor-widget-theme-post-content",
    },
    "sgg_news": {
        "name": "Secrétariat Général du Gouvernement",
        "base_url": "https://www.sgg.gov.ma/",
        "category": "Régulateurs & Institutions Officielles",
        "doc_type": "News",
        "article_link_selector": "a[href*='LinkClick.aspx'], a[href*='fileticket'], div.news-item a, h2 a, h3 a",
        "title_selector": "h1, h2, .title",
        "content_selector": "div.content, article, main, div.Normal, div.dnnFormItem",
        "use_browser": True,
    },

    # ──────────────────────────────────────────────────────────
    # 2. RÉGLEMENTATION INTERNATIONALE
    # ──────────────────────────────────────────────────────────

    "bis_press": {
        "name": "Bank for International Settlements (BIS)",
        "base_url": "https://www.bis.org/press/index.htm",
        "category": "Réglementation Internationale",
        "doc_type": "Press Release",
        "article_link_selector": "a[href*='/press/p']",
        "title_selector": "h1.title, h1",
        "content_selector": "div#cmsContent, div.cmsContent, article, main",
        "use_browser": True,
    },
    "imf_news": {
        "name": "International Monetary Fund (IMF)",
        "base_url": "https://www.imf.org/en/news",
        "category": "Réglementation Internationale",
        "doc_type": "News",
        "article_link_selector": "a[href*='/en/news/articles/'], h2 a, h3 a",
        "title_selector": "h1, h2",
        "content_selector": "div.news-content, article, main, div.content",
        "use_browser": True,
    },
    "world_bank_news": {
        "name": "World Bank",
        "base_url": "https://www.worldbank.org/en/news/all",
        "category": "Réglementation Internationale",
        "doc_type": "News",
        "article_link_selector": "a[href*='/en/news/press-release/'], a[href*='/en/news/feature/'], h2 a, h3 a",
        "title_selector": "h1, h2",
        "content_selector": "div.body-copy, article, main, div.content",
        "use_browser": True,
    },
    "eba_news": {
        "name": "European Banking Authority (EBA)",
        "base_url": "https://www.eba.europa.eu/news-press/news",
        "category": "Réglementation Internationale",
        "doc_type": "News",
        "article_link_selector": "div.news-item a, a[href*='/news-press/'], h2 a, h3 a",
        "title_selector": "h1, h2",
        "content_selector": "div.node__content, article, main, div.content",
        "use_browser": True,
    },

    # ──────────────────────────────────────────────────────────
    # 3. PRESSE ÉCONOMIQUE & FINANCIÈRE
    # ──────────────────────────────────────────────────────────

    "leconomiste": {
        "name": "L'Economiste",
        "base_url": "https://www.leconomiste.com/",
        "category": "Presse Économique & Financière",
        "doc_type": "Articles",
        "article_link_selector": "h2 a[href*='leconomiste.com'], h3 a[href*='leconomiste.com']",
        "title_selector": "h1.entry-title, h1",
        "content_selector": "div.entry-content, div.node-content, article, main",
    },
    "medias24_eco": {
        "name": "Medias24 - Économie",
        "base_url": "https://www.medias24.com/economie/",
        "category": "Presse Économique & Financière",
        "doc_type": "Articles",
        "article_link_selector": "h2.entry-title a, h3 a, a[href*='/economie/']",
        "title_selector": "h1.entry-title, h1",
        "content_selector": "div.entry-content, article, main, div.content",
        "use_browser": True,
    },
    "challenge_ma": {
        "name": "Challenge.ma",
        "base_url": "https://www.challenge.ma/category/economie/",
        "category": "Presse Économique & Financière",
        "doc_type": "Articles",
        "article_link_selector": "h2.entry-title a, h3.entry-title a, h2 a, h3 a",
        "title_selector": "h1.entry-title, h1",
        "content_selector": "div.entry-content, article, main",
    },
    "reuters_finance": {
        "name": "Reuters Financials",
        "base_url": "https://www.reuters.com/business/finance/",
        "category": "Presse Économique & Financière",
        "doc_type": "News",
        "article_link_selector": "a[data-testid='Heading'], a[href*='/business/finance/'], h2 a, h3 a",
        "title_selector": "h1, h2",
        "content_selector": "div.article-body__content, article, main, div.content",
        "use_browser": True,
    },

    # ──────────────────────────────────────────────────────────
    # 4. SECTEUR BANCAIRE MAROC
    # ──────────────────────────────────────────────────────────

    "cih_bank_news": {
        "name": "CIH Bank - Communiqués",
        "base_url": "https://www.cihbank.ma/actualite/banque",
        "category": "Secteur Bancaire Maroc",
        "doc_type": "Communiqué",
        "article_link_selector": "a[href*='/actualite/'], div.card a, h2 a, h3 a",
        "title_selector": "h1, h2",
        "content_selector": "div.content, article, main",
        "use_browser": True,
    },
    "gpbm_news": {
        "name": "GPBM (Banques du Maroc)",
        "base_url": "https://www.gpbm.ma/actualites",
        "category": "Secteur Bancaire Maroc",
        "doc_type": "News",
        "article_link_selector": "a[href*='/actualites/'], h2 a, h3 a",
        "title_selector": "h1, h2",
        "content_selector": "div.content, article, main",
        "use_browser": True,
    },
    "stock_exchange_news": {
        "name": "Bourse de Casablanca",
        "base_url": "https://www.casablanca-bourse.com/bourseweb/Actualites.aspx",
        "category": "Secteur Bancaire Maroc",
        "doc_type": "Market News",
        "article_link_selector": "a[href*='Actualites'], h2 a, h3 a",
        "title_selector": "h1, h2",
        "content_selector": "div.content, article, main",
        "use_browser": True,
    },
    "acaps_news": {
        "name": "ACAPS - Actualités",
        "base_url": "https://www.acaps.ma/fr/actualites",
        "category": "Secteur Bancaire Maroc",
        "doc_type": "News",
        "article_link_selector": "a[href*='/actualites/'], a[href*='/actualite/'], h2 a, h3 a",
        "title_selector": "h1, h2",
        "content_selector": "div.field-items, div.content, article, main",
    },
}

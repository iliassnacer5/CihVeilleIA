"""
Service de notifications pour CIH Veille IA.

Orchestre l'envoi d'alertes e-mail via Outlook SMTP,
avec dé-duplication, retry, et journalisation.
"""

import logging
import hashlib
import time
from typing import Dict, Any
from datetime import datetime

from app.notifications.connectors import OutlookSMTPConnector
from app.notifications.templates import get_alert_email_template
from app.config.settings import settings
from app.storage.notification_store import MongoNotificationStore

logger = logging.getLogger(__name__)


class NotificationService:
    """Service d'orchestration des notifications d'entreprise (Outlook SMTP)."""

    def __init__(self):
        self.store = MongoNotificationStore()
        self._sent_cache: Dict[str, float] = {}

    def _generate_content_hash(self, data: Dict[str, Any]) -> str:
        """Génère un hash unique pour le contenu afin d'éviter les doublons."""
        content = f"{data.get('title')}-{data.get('source')}-{data.get('url')}"
        return hashlib.md5(content.encode()).hexdigest()

    async def should_notify(self, data: Dict[str, Any]) -> bool:
        """Vérifie si une notification doit être envoyée selon les règles métier."""

        score = data.get("score", 0.0)
        priority = data.get("priority", "NORMAL").lower()

        is_high_priority = priority in ["critical", "important"]
        meets_threshold = score >= settings.notification_rag_threshold

        if not (is_high_priority or meets_threshold):
            return False

        # Dé-duplication
        content_hash = self._generate_content_hash(data)
        now = time.time()

        if content_hash in self._sent_cache:
            if now - self._sent_cache[content_hash] < settings.notification_deduplication_window:
                logger.info(f"Notification ignorée (doublon cache) : {data.get('title')}")
                return False

        already_sent = await self.store.was_sent_recently(
            content_hash, settings.notification_deduplication_window
        )
        if already_sent:
            logger.info(f"Notification ignorée (doublon DB) : {data.get('title')}")
            return False

        return True

    async def send_regulatory_alert(self, to_email: str, data: Dict[str, Any]) -> bool:
        """Envoie une alerte réglementaire via le compte Outlook SMTP configuré."""

        if not await self.should_notify(data):
            return False

        # 1. Récupérer le compte e-mail actif depuis la base
        from app.storage.email_repository import EmailRepository
        from app.services.crypto_utils import decrypt_password

        repo = EmailRepository()
        account = await repo.get_default()

        if not account:
            logger.error("Aucun compte e-mail actif configuré ! Notification annulée.")
            return False

        password = decrypt_password(account.get("encrypted_password", ""))

        # 2. Créer un connecteur Outlook SMTP avec les paramètres du compte
        connector = OutlookSMTPConnector(
            host=account.get("smtp_host", "smtp.office365.com"),
            port=int(account.get("smtp_port", 587)),
            user=account.get("username"),
            password=password,
        )

        subject = f"🚨 Nouvelle information réglementaire : {data.get('title', 'Alerte')}"
        html_content = get_alert_email_template(data)

        # 3. Envoi avec retry
        success = False
        for attempt in range(settings.notification_retry_attempts):
            try:
                success = await connector.send_email(to_email, subject, html_content)
                if success:
                    break
                logger.warning(f"Tentative {attempt + 1} échouée pour {to_email}")
            except Exception as e:
                logger.error(f"Erreur tentative {attempt + 1} : {e}")

        # 4. Journalisation
        content_hash = self._generate_content_hash(data)
        await self.store.log_notification(
            {
                "to_email": to_email,
                "subject": subject,
                "content_hash": content_hash,
                "status": "SUCCESS" if success else "FAILED",
                "timestamp": datetime.now(),
                "metadata": {
                    "doc_id": data.get("doc_id"),
                    "priority": data.get("priority"),
                    "score": data.get("score"),
                },
            }
        )

        if success:
            self._sent_cache[content_hash] = time.time()

        return success

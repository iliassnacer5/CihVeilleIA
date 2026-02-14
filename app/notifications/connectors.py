"""
Connecteurs e-mail pour CIH Veille IA.

Architecture :
  - OutlookSMTPConnector : Envoi via SMTP Outlook/Office 365 (recommandé)
    Utilise directement smtp.office365.com avec les identifiants de l'utilisateur.
    Pas besoin d'App Registration Azure ni de Microsoft Graph.

Usage :
  1. Configurer SMTP_USER + SMTP_PASSWORD dans le .env
  2. Le service de notifications utilise automatiquement ce connecteur.
"""

import logging
import smtplib
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config.settings import settings

logger = logging.getLogger(__name__)


class BaseEmailConnector(ABC):
    """Interface de base pour les connecteurs d'e-mail."""

    @abstractmethod
    async def send_email(self, to_email: str, subject: str, content_html: str) -> bool:
        pass


class OutlookSMTPConnector(BaseEmailConnector):
    """Envoi d'e-mails via Outlook / Office 365 SMTP.

    Configuration requise dans .env :
      SMTP_HOST=smtp.office365.com   (ou smtp-mail.outlook.com)
      SMTP_PORT=587
      SMTP_USER=votre.email@outlook.com
      SMTP_PASSWORD=votre_mot_de_passe
      SMTP_USE_TLS=True

    Pour les comptes avec 2FA activée, utilisez un "App Password"
    généré depuis https://account.live.com/proofs/AppPassword
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
    ):
        self.host = host or getattr(settings, "smtp_host", "smtp.office365.com")
        self.port = port or int(getattr(settings, "smtp_port", 587))
        self.user = user or getattr(settings, "smtp_user", "")
        self.password = password or getattr(settings, "smtp_password", "")
        self.use_tls = use_tls

    async def send_email(self, to_email: str, subject: str, content_html: str) -> bool:
        if not self.user or not self.password:
            logger.warning("SMTP identifiants manquants → e-mail non envoyé.")
            return False

        msg = MIMEMultipart("alternative")
        msg["From"] = self.user
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(content_html, "html", "utf-8"))

        try:
            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                server.ehlo()
                if self.use_tls:
                    server.starttls()
                    server.ehlo()
                server.login(self.user, self.password)
                server.send_message(msg)
            logger.info(f"✅ E-mail envoyé à {to_email} via {self.host}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(
                f"❌ Authentification SMTP échouée pour {self.user}. "
                f"Si la 2FA est activée, utilisez un App Password. Erreur: {e}"
            )
            return False
        except Exception as e:
            logger.error(f"❌ Erreur SMTP: {e}")
            return False


# Alias pour compatibilité avec le code existant
SMTPEmailConnector = OutlookSMTPConnector

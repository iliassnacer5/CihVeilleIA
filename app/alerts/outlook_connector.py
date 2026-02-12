import logging
import httpx
from typing import List, Dict, Optional
from msal import ConfidentialClientApplication
from app.config.settings import settings

logger = logging.getLogger(__name__)

class OutlookConnector:
    """Connecteur pour l'API Microsoft Graph (Outlook).
    
    Permet l'envoi d'e-mails d'alerte et de rapports de veille (Daily Digest)
    en utilisant le protocole OAuth2.
    """

    def __init__(self):
        self.client_id = settings.azure_client_id
        self.client_secret = settings.azure_client_secret
        self.tenant_id = settings.azure_tenant_id
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/.default"]
        
        self._app: Optional[ConfidentialClientApplication] = None
        if self.client_id and self.client_secret:
            self._app = ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=self.client_secret
            )

    async def get_access_token(self) -> Optional[str]:
        """Récupère un token d'accès via MSAL."""
        if not self._app:
            logger.warning("Azure Client ID ou Secret manquant. Impossible d'obtenir un token.")
            return None
            
        result = self._app.acquire_token_for_client(scopes=self.scopes)
        if "access_token" in result:
            return result["access_token"]
        else:
            logger.error(f"Erreur d'acquisition de token MSAL: {result.get('error_description')}")
            return None

    async def send_alert_email(self, to_email: str, subject: str, content_html: str):
        """Envoie un e-mail d'alerte utilisateur via Graph API."""
        token = await self.get_access_token()
        if not token:
            return False
            
        sender = settings.azure_sender_email
        endpoint = f"https://graph.microsoft.com/v1.0/users/{sender}/sendMail"
        
        email_body = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": content_html
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_email
                        }
                    }
                ]
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                json=email_body,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 202:
                logger.info(f"E-mail d'alerte envoyé avec succès à {to_email}")
                return True
            else:
                logger.error(f"Échec de l'envoi d'e-mail ({response.status_code}): {response.text}")
                return False

    async def generate_daily_digest_html(self, alerts: List[Dict]) -> str:
        """Génère le contenu HTML pour le rapport quotidien (Daily Digest)."""
        if not alerts:
            return "<p>Aucune nouvelle alerte pour aujourd'hui.</p>"
            
        items_html = ""
        for alert in alerts:
            items_html += f"""
            <div style="border-bottom: 1px solid #ddd; padding: 10px 0;">
                <h3 style="color: #004a99; margin-bottom: 5px;">{alert.get('title')}</h3>
                <p style="margin-top: 0;">{alert.get('message')}</p>
                <span style="background: #eee; padding: 2px 5px; font-size: 0.8em;">
                    {alert.get('metadata', {}).get('topics', ['Général'])[0]} | Priorité: {alert.get('priority')}
                </span>
            </div>
            """
            
        full_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h1 style="color: #c41230;">Rapport de Veille IA - CIH Bank</h1>
                <p>Voici le récapitulatif de vos alertes de veille pour les dernières 24 heures.</p>
                {items_html}
                <br/>
                <p style="font-size: 0.9em; color: #666;">
                    Cet e-mail est généré automatiquement par la plateforme CIH-Veille-IA.
                </p>
            </body>
        </html>
        """
        return full_html

    async def generate_alert_html(self, alert: Dict) -> str:
        """Génère le contenu HTML pour une alerte individuelle détaillée."""
        metadata = alert.get("metadata", {})
        full_html = f"""
        <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                    <div style="background-color: #c41230; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">🚨 Alerte Veille CIH Bank</h1>
                    </div>
                    <div style="padding: 20px;">
                        <h2 style="color: #004a99; border-bottom: 2px solid #004a99; padding-bottom: 10px;">{alert.get('title')}</h2>
                        <p><strong>Message:</strong> {alert.get('message')}</p>
                        
                        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin-top: 20px;">
                            <h3 style="margin-top: 0; color: #555;">Détails du document :</h3>
                            <ul style="list-style: none; padding-left: 0;">
                                <li><strong>Source:</strong> {metadata.get('source')}</li>
                                <li><strong>Catégorie:</strong> {metadata.get('category')}</li>
                                <li><strong>Type:</strong> {metadata.get('doc_type')}</li>
                                <li><strong>Date d'ajout:</strong> {metadata.get('added_at')}</li>
                                <li><strong>Thématiques:</strong> {', '.join(metadata.get('topics', []))}</li>
                            </ul>
                        </div>
                        
                        <div style="margin-top: 30px; text-align: center;">
                            <a href="{metadata.get('url', '#')}" style="background-color: #004a99; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                                📖 Consulter le document complet
                            </a>
                        </div>
                    </div>
                    <div style="background-color: #f0f0f0; color: #666; padding: 15px; text-align: center; font-size: 12px;">
                        <p>Cet e-mail est une notification automatique de votre plateforme CIH-Veille-IA.</p>
                        <p>© 2026 CIH Bank - PFE Excellence Projet</p>
                    </div>
                </div>
            </body>
        </html>
        """
        return full_html

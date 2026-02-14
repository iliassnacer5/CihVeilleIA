import logging
import smtplib
from typing import Dict, Optional, Any
from app.storage.email_repository import EmailRepository
from app.services.crypto_utils import encrypt_password, decrypt_password

logger = logging.getLogger(__name__)

class EmailConfigurationService:
    """Service pour gérer la configuration et le test des comptes email."""
    
    def __init__(self, repository: Optional[EmailRepository] = None):
        self.repository = repository or EmailRepository()

    async def test_smtp_connection(self, account_data: Dict[str, Any]) -> tuple[bool, str]:
        """Teste la connexion SMTP avec les paramètres fournis."""
        host = account_data.get("smtp_host")
        port = int(account_data.get("smtp_port", 587))
        user = account_data.get("username")
        
        # Le mot de passe peut être en clair (pour un test avant création) 
        # ou déjà chiffré (pour un test depuis la liste)
        password = account_data.get("password")
        if not password and "encrypted_password" in account_data:
            password = decrypt_password(account_data["encrypted_password"])
            
        if not all([host, port, user, password]):
            return False, "Paramètres SMTP incomplets."
            
        try:
            # Note: smtplib is blocking but for a limited admin test it's acceptable.
            # In a very high concurrency scenario, this should be offloaded.
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.starttls()
                server.login(user, password)
            return True, "Connexion réussie !"
        except Exception as e:
            logger.error(f"Échec du test SMTP pour {user}: {e}")
            return False, f"Erreur de connexion : {str(e)}"

    async def add_account(self, data: Dict[str, Any], creator_username: str) -> str:
        """Ajoute un compte email avec chiffrement du mot de passe."""
        password = data.pop("password", "")
        data["encrypted_password"] = encrypt_password(password)
        data["created_by"] = creator_username
        return await self.repository.create_account(data)

    async def update_account(self, account_id: str, data: Dict[str, Any]) -> bool:
        """Met à jour un compte, avec chiffrement optionnel du mot de passe."""
        if "password" in data:
            password = data.pop("password")
            if password: # Uniquement si un nouveau mot de passe est fourni
                data["encrypted_password"] = encrypt_password(password)
        
        return await self.repository.update_account(account_id, data)

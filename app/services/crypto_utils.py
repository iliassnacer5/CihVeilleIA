import base64
import logging
from cryptography.fernet import Fernet
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Note: In a real bank environment, the key would be in a HSM or Key Vault.
# Here we use a key derived from settings or a default one for the PFE.
_KEY = settings.api_secret_key[:32].encode().rjust(32, b'0')
_FERNET_KEY = base64.urlsafe_b64encode(_KEY)
_CIPHER = Fernet(_FERNET_KEY)

def encrypt_password(password: str) -> str:
    """Chiffre un mot de passe en AES-256."""
    if not password:
        return ""
    return _CIPHER.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    """Déchiffre un mot de passe AES-256."""
    if not encrypted_password:
        return ""
    try:
        return _CIPHER.decrypt(encrypted_password.encode()).decode()
    except Exception as e:
        logger.error(f"Erreur de déchiffrement: {e}")
        return ""

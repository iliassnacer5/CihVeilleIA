import logging
import httpx
import pdfplumber
import io
from typing import Optional

logger = logging.getLogger(__name__)

class PdfExtractionService:
    """Service d'extraction de texte pour les documents PDF réglementaires."""

    @staticmethod
    async def extract_text_from_url(url: str, timeout: int = 30) -> Optional[str]:
        """Télécharge un PDF et extrait son texte."""
        logger.info(f"📥 Téléchargement du PDF: {url}")
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(url, timeout=timeout)
                response.raise_for_status()
                
                pdf_data = io.BytesIO(response.content)
                text_parts = []
                
                with pdfplumber.open(pdf_data) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                
                full_text = "\n".join(text_parts)
                logger.info(f"✓ Extraction PDF réussie ({len(full_text)} caractères)")
                return full_text
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'extraction du PDF {url}: {e}")
            return None

pdf_service = PdfExtractionService()

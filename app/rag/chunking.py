import logging
from typing import List, Dict
import spacy

logger = logging.getLogger(__name__)

class ChunkingService:
    """Service de découpage sémantique des documents pour le RAG.
    
    Découpe le contenu en segments de taille contrôlée tout en préservant
    la cohérence des phrases (utilise spaCy).
    """

    def __init__(self, model: str = "fr_core_news_md", chunk_size: int = 500, chunk_overlap: int = 50):
        try:
            self.nlp = spacy.load(model)
        except Exception:
            logger.warning(f"Modèle spaCy {model} non trouvé, utilisation de en_core_web_sm comme fallback.")
            self.nlp = spacy.load("en_core_web_sm")
            
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """Découpe un texte en morceaux sémantiquement cohérents."""
        if not text or len(text) < self.chunk_size:
            return [text] if text else []

        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        
        chunks = []
        current_chunk = ""
        
        for sent in sentences:
            if len(current_chunk) + len(sent) <= self.chunk_size:
                current_chunk += " " + sent if current_chunk else sent
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Gestion de l'overlap simple : on reprend la fin du morceau précédent 
                # (ou on garde juste la phrase actuelle si elle est trop longue)
                if len(sent) > self.chunk_size:
                    # Cas rare d'une phrase extrêmement longue
                    chunks.append(sent[:self.chunk_size])
                    current_chunk = ""
                else:
                    current_chunk = sent
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    def create_chunks_with_metadata(self, text: str, base_metadata: Dict) -> List[Dict]:
        """Découpe un texte et retourne une liste de dicts {text, metadata}."""
        chunks = self.chunk_text(text)
        chunked_data = []
        
        for idx, chunk in enumerate(chunks):
            meta = base_metadata.copy()
            meta["chunk_id"] = idx
            meta["text"] = chunk # On injecte le texte du chunk dans la metadata pour VectorStore
            chunked_data.append({
                "text": chunk,
                "metadata": meta
            })
            
        return chunked_data

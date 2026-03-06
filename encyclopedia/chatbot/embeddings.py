"""
Embeddings for chatbot retrieval using sentence-transformers.

Requires: pip install sentence-transformers
"""

from typing import List

# Default model: small, fast, good for semantic similarity
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class SentenceTransformerEmbedder:
    """
    Embed text using sentence-transformers. Lazy-loads the model on first use.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers is required for embeddings. "
                    "Install with: pip install sentence-transformers"
                ) from e
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts; returns list of vectors."""
        if not texts:
            return []
        model = self._get_model()
        return model.encode(texts, convert_to_numpy=True).tolist()

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string."""
        if not query or not query.strip():
            return []
        model = self._get_model()
        return model.encode([query.strip()], convert_to_numpy=True)[0].tolist()

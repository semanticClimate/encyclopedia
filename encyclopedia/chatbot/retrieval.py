"""
Retrieval: search chunks by query.
- InMemoryRetriever: keyword-based, no deps (TDD and small corpora).
- VectorRetriever: sentence-transformers + ChromaDB for semantic search.
"""

from typing import List, Dict, Any, Tuple, Optional


class InMemoryRetriever:
    """
    Simple retriever that scores by keyword overlap (no embeddings).
    Suitable for TDD and small corpora; replace with vector search later.
    """

    def __init__(self, chunks: List[Dict[str, Any]]):
        self.chunks = list(chunks)

    def search(self, query: str, k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Return top-k chunks with scores in [0, 1].
        Score = number of query words found in chunk text / number of query words.
        """
        if not query or not self.chunks:
            return []
        qwords = set(query.lower().split())
        if not qwords:
            return []
        scored = []
        for ch in self.chunks:
            text = (ch.get("text") or "") + " " + (ch.get("term") or "")
            text_lower = text.lower()
            hits = sum(1 for w in qwords if w in text_lower)
            score = hits / len(qwords) if qwords else 0.0
            scored.append((ch, score))
        scored.sort(key=lambda x: -x[1])
        return scored[:k]


class VectorRetriever:
    """
    Retriever that embeds chunks and queries with sentence-transformers
    and searches via ChromaDB. Use for semantic similarity over larger corpora.
    """

    def __init__(
        self,
        chunks: List[Dict[str, Any]],
        persist_directory: Optional[str] = None,
        collection_name: str = "climate_encyclopedia",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        """
        Build the index from chunks. Requires sentence-transformers and chromadb.

        Args:
            chunks: List of chunk dicts (section_label, text, entry_id, term).
            persist_directory: If set, Chroma persists the collection here.
            collection_name: Chroma collection name.
            model_name: sentence-transformers model for embeddings.
        """
        from encyclopedia.chatbot.embeddings import SentenceTransformerEmbedder

        self.chunks = list(chunks)
        self.embedder = SentenceTransformerEmbedder(model_name=model_name)
        self._collection = None
        self._persist_directory = persist_directory
        self._collection_name = collection_name
        self._indexed = False

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError as e:
            raise ImportError(
                "chromadb is required for VectorRetriever. "
                "Install with: pip install chromadb"
            ) from e

        if self._persist_directory:
            client = chromadb.PersistentClient(path=self._persist_directory)
        else:
            client = chromadb.Client(Settings(anonymized_telemetry=False))

        # Chroma embedding function: we embed ourselves and pass embeddings
        # So we create collection without embedding_function and add with embeddings=
        self._collection = client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        return self._collection

    def _build_index(self):
        if self._indexed or not self.chunks:
            return
        texts = [c.get("text") or "" for c in self.chunks]
        embeddings = self.embedder.embed_documents(texts)
        ids = [f"chunk_{i}" for i in range(len(self.chunks))]
        metadatas = [
            {
                "section_label": (c.get("section_label") or ""),
                "entry_id": str(c.get("entry_id") or ""),
                "term": (c.get("term") or ""),
            }
            for c in self.chunks
        ]
        collection = self._get_collection()
        collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        self._indexed = True

    def search(self, query: str, k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Return top-k chunks by semantic similarity. Scores in [0, 1] (cosine similarity).
        """
        if not query or not query.strip():
            return []
        self._build_index()
        if not self.chunks:
            return []

        q_embedding = self.embedder.embed_query(query)
        if not q_embedding:
            return []

        collection = self._get_collection()
        results = collection.query(
            query_embeddings=[q_embedding],
            n_results=min(k, len(self.chunks)),
            include=["documents", "metadatas", "distances"],
        )

        # Chroma returns distances (cosine: 0 = same, 2 = opposite). Convert to similarity.
        # For cosine in Chroma, distance = 1 - cosine_sim, so similarity = 1 - distance.
        out = []
        for i, doc_id in enumerate(results["ids"][0]):
            idx = int(doc_id.replace("chunk_", "")) if doc_id.startswith("chunk_") else i
            dist = results["distances"][0][i] if results["distances"] else 0.0
            # cosine distance in [0,2]; similarity = 1 - distance (clamp to [0,1])
            similarity = max(0.0, min(1.0, 1.0 - dist))
            meta = (results["metadatas"][0][i] or {}) if results["metadatas"] else {}
            doc_text = (results["documents"][0][i] or "") if results["documents"] else ""
            chunk = {
                "section_label": meta.get("section_label", ""),
                "text": doc_text,
                "entry_id": meta.get("entry_id", ""),
                "term": meta.get("term", ""),
            }
            out.append((chunk, similarity))
        return out

from typing import List, Optional
import httpx
import structlog
from fastembed import SparseEmbedding, SparseTextEmbedding, TextEmbedding

from app.core.config import settings

logger = structlog.get_logger(__name__)


class DenseEmbeddingEngine:
    """
    High-performance 384-dimensional Dense Vector Embedding Engine.
    Uses Google Gemini Cloud Embeddings API (models/gemini-embedding-001 with outputDimensionality=384)
    for zero-RAM, ultra-fast vectorization (<150ms).
    Falls back to local FastEmbed (threads=1) if no LLM_API_KEY is configured.
    """

    def __init__(self, model_name: str = "models/gemini-embedding-001") -> None:
        self.model_name = model_name
        gemini_key = getattr(settings, "GEMINI_API_KEY", None)
        if gemini_key:
            self.api_key = gemini_key
        elif settings.LLM_API_KEY and not settings.LLM_API_KEY.startswith("gsk_"):
            self.api_key = settings.LLM_API_KEY
        else:
            self.api_key = ""

        self._fastembed_model: Optional[TextEmbedding] = None

        if self.api_key:
            logger.info("dense_embedding_engine_using_cloud_api", provider="gemini", model=self.model_name)
        else:
            logger.info("dense_embedding_engine_using_fastembed_fallback", model="BAAI/bge-small-en-v1.5")

    def _get_fastembed(self) -> TextEmbedding:
        if self._fastembed_model is None:
            logger.info("initializing_fallback_fastembed_model", model_name="BAAI/bge-small-en-v1.5")
            self._fastembed_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", threads=1)
        return self._fastembed_model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of document strings into 384-dimensional float vectors.
        """
        if not texts:
            return []

        # 1. Cloud API Path (Zero RAM, GPU-accelerated on Google Cloud)
        if self.api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents?key={self.api_key}"
                # Batch in groups of 50 to stay within request limits
                all_vectors: list[list[float]] = []
                batch_size = 50

                with httpx.Client(timeout=30.0) as client:
                    for i in range(0, len(texts), batch_size):
                        batch = texts[i : i + batch_size]
                        payload = {
                            "requests": [
                                {
                                    "model": "models/gemini-embedding-001",
                                    "content": {"parts": [{"text": t}]},
                                    "outputDimensionality": 384,
                                }
                                for t in batch
                            ]
                        }
                        res = client.post(url, json=payload)
                        if res.status_code == 200:
                            data = res.json()
                            batch_embeddings = [item["values"] for item in data.get("embeddings", [])]
                            all_vectors.extend(batch_embeddings)
                        else:
                            logger.warning(
                                "gemini_batch_embed_failed_status",
                                status=res.status_code,
                                response=res.text[:200],
                            )
                            raise RuntimeError(f"Gemini embedding API returned {res.status_code}")

                logger.debug("documents_cloud_embedded_successfully", count=len(all_vectors))
                return all_vectors

            except Exception as e:
                logger.warning("cloud_embedding_failed_falling_back_to_fastembed", error=str(e))

        # 2. FastEmbed Fallback (Local ONNX, threads=1)
        fastembed = self._get_fastembed()
        embeddings_generator = fastembed.embed(texts, batch_size=16)
        vectors = [vec.tolist() for vec in embeddings_generator]
        logger.debug("documents_fastembed_embedded_successfully", count=len(vectors))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        """
        Embed a single query string into a 384-dimensional float vector.
        """
        if not text or not text.strip():
            raise ValueError("Query text cannot be empty or whitespace only.")

        # 1. Cloud API Path
        if self.api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={self.api_key}"
                payload = {
                    "model": "models/gemini-embedding-001",
                    "content": {"parts": [{"text": text}]},
                    "outputDimensionality": 384,
                }
                with httpx.Client(timeout=15.0) as client:
                    res = client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        values = data.get("embedding", {}).get("values", [])
                        if len(values) == 384:
                            return values

                logger.warning("gemini_single_embed_failed", status=res.status_code)
            except Exception as e:
                logger.warning("cloud_query_embed_failed_falling_back_to_fastembed", error=str(e))

        # 2. FastEmbed Fallback
        vectors = self.embed_documents([text])
        return vectors[0]


class SparseEmbeddingEngine:
    """
    Wrapper for FastEmbed BM25 sparse vectorization.
    Converts text inputs into sparse vector representations (indices and values) using Qdrant/bm25.
    """

    def __init__(self, model_name: str = "Qdrant/bm25") -> None:
        """
        Initialize the FastEmbed SparseTextEmbedding model.

        Args:
            model_name: Sparse embedding model identifier. Defaults to 'Qdrant/bm25'.
        """
        self.model_name = model_name
        logger.info("initializing_sparse_embedding_engine", model_name=self.model_name)
        # threads=1 keeps memory footprint minimal
        self._model = SparseTextEmbedding(model_name=self.model_name, threads=1)
        logger.info("sparse_embedding_engine_initialized", model_name=self.model_name)

    def embed_documents(self, texts: list[str]) -> list[SparseEmbedding]:
        """
        Embed a batch of document strings into a list of SparseEmbedding objects.

        Args:
            texts: List of text chunk strings to vectorize.

        Returns:
            List of SparseEmbedding objects containing indices and values.
        """
        if not texts:
            return []

        logger.debug("embedding_documents_sparse", count=len(texts))
        embeddings_generator = self._model.embed(texts, batch_size=16)
        vectors = list(embeddings_generator)
        logger.debug("documents_sparse_embedded_successfully", count=len(vectors))
        return vectors

    def embed_query(self, text: str) -> SparseEmbedding:
        """
        Embed a single query string into a SparseEmbedding object.

        Args:
            text: Query text string.

        Returns:
            SparseEmbedding object.
        """
        if not text or not text.strip():
            raise ValueError("Query text cannot be empty or whitespace only.")

        logger.debug("embedding_query_sparse", text_length=len(text))
        vectors = self.embed_documents([text])
        return vectors[0]


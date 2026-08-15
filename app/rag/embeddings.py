"""
Dense Vector Embedding Engine using FastEmbed BAAI/bge-small-en-v1.5.
"""

from fastembed import TextEmbedding
import structlog

logger = structlog.get_logger(__name__)


class DenseEmbeddingEngine:
    """
    Wrapper for FastEmbed dense vectorization.
    Converts text inputs into 384-dimensional dense vectors using BAAI/bge-small-en-v1.5.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        """
        Initialize the FastEmbed TextEmbedding model.

        Args:
            model_name: ONNX model identifier. Defaults to 'BAAI/bge-small-en-v1.5'.
        """
        self.model_name = model_name
        logger.info("initializing_dense_embedding_engine", model_name=self.model_name)
        self._model = TextEmbedding(model_name=self.model_name)
        logger.info("dense_embedding_engine_initialized", model_name=self.model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of document strings into a list of 384-dimensional float vectors.

        Args:
            texts: List of text chunk strings to vectorize.

        Returns:
            List of 384-dimensional float vectors.
        """
        if not texts:
            return []

        logger.debug("embedding_documents", count=len(texts))
        embeddings_generator = self._model.embed(texts)
        vectors = [vec.tolist() for vec in embeddings_generator]
        logger.debug("documents_embedded_successfully", count=len(vectors))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        """
        Embed a single query string into a 384-dimensional float vector.

        Args:
            text: Query text string.

        Returns:
            384-dimensional float vector.
        """
        if not text or not text.strip():
            raise ValueError("Query text cannot be empty or whitespace only.")

        logger.debug("embedding_query", text_length=len(text))
        vectors = self.embed_documents([text])
        return vectors[0]

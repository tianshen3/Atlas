"""
Reciprocal Rank Fusion (RRF) and Cross-Encoder Neural Reranking Engine.
"""

from typing import Dict, List, Tuple
from qdrant_client.models import ScoredPoint
import structlog

logger = structlog.get_logger(__name__)


def compute_rrf(
    dense_hits: List[ScoredPoint],
    sparse_hits: List[ScoredPoint],
    k: int = 60,
) -> List[Tuple[ScoredPoint, float]]:
    """
    Combine dense and sparse search rankings using Reciprocal Rank Fusion (RRF).

    Formula:
        RRF_Score(doc) = 1.0 / (k + rank_dense) + 1.0 / (k + rank_sparse)

    Args:
        dense_hits: Ranked list of ScoredPoints from dense vector search.
        sparse_hits: Ranked list of ScoredPoints from sparse vector search.
        k: Smoothing constant parameter (default: 60).

    Returns:
        List of (ScoredPoint, rrf_score) sorted by descending rrf_score.
    """
    scores: Dict[str, float] = {}
    point_map: Dict[str, ScoredPoint] = {}

    for rank, point in enumerate(dense_hits, start=1):
        point_id = str(point.id)
        scores[point_id] = scores.get(point_id, 0.0) + (1.0 / (k + rank))
        point_map[point_id] = point

    for rank, point in enumerate(sparse_hits, start=1):
        point_id = str(point.id)
        scores[point_id] = scores.get(point_id, 0.0) + (1.0 / (k + rank))
        if point_id not in point_map:
            point_map[point_id] = point

    sorted_points = sorted(
        [(point_map[pid], score) for pid, score in scores.items()],
        key=lambda x: x[1],
        reverse=True,
    )

    logger.debug("computed_rrf_fusion", candidate_count=len(sorted_points))
    return sorted_points


class CrossEncoderReranker:
    """
    Neural Reranker using SentenceTransformers CrossEncoder (e.g. cross-encoder/ms-marco-MiniLM-L-6-v2).
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        """
        Initialize CrossEncoder model.

        Args:
            model_name: HuggingFace model identifier.
        """
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            logger.info("loading_cross_encoder_model", model_name=self.model_name)
            self._model = CrossEncoder(self.model_name)
            logger.info("cross_encoder_model_loaded", model_name=self.model_name)
        return self._model

    def rerank(
        self,
        query: str,
        candidates: List[ScoredPoint],
        top_k: int = 5,
    ) -> List[Tuple[ScoredPoint, float]]:
        """
        Compute neural relevance scores for (query, document) pairs and return top_k candidates.

        Args:
            query: Search query text.
            candidates: List of ScoredPoint candidate chunks.
            top_k: Number of top candidate chunks to return.

        Returns:
            List of (ScoredPoint, relevance_score) sorted by score descending.
        """
        if not candidates:
            return []

        pairs = []
        for point in candidates:
            payload = point.payload or {}
            content = str(payload.get("content", ""))
            pairs.append((query, content))

        model = self._get_model()
        scores = model.predict(pairs)

        scored_candidates = []
        for point, score in zip(candidates, scores):
            scored_candidates.append((point, float(score)))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        result = scored_candidates[:top_k]

        logger.debug("cross_encoder_rerank_completed", candidate_count=len(candidates), top_k=len(result))
        return result

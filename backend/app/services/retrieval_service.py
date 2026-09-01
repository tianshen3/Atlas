from typing import List, Optional
from uuid import UUID

from qdrant_client.http.models import SparseVector

from app.core.logging import logger
from app.rag.embeddings import DenseEmbeddingEngine, SparseEmbeddingEngine
from app.rag.qdrant import QdrantVectorService
from app.rag.reranker import CrossEncoderReranker, compute_rrf
from app.schemas.retrieval import SearchRequest, SearchResponse, SearchResultChunk


class RetrievalService:
    """Service handling dense/hybrid vector retrieval, RRF fusion, neural reranking, and search response assembly."""

    def __init__(
        self,
        embedding_engine: Optional[DenseEmbeddingEngine] = None,
        sparse_embedding_engine: Optional[SparseEmbeddingEngine] = None,
        qdrant_service: Optional[QdrantVectorService] = None,
        reranker: Optional[CrossEncoderReranker] = None,
    ) -> None:
        self.embedding_engine = embedding_engine or DenseEmbeddingEngine()
        self.sparse_embedding_engine = sparse_embedding_engine or SparseEmbeddingEngine()
        self.qdrant_service = qdrant_service or QdrantVectorService()
        self.reranker = reranker

    async def search(
        self,
        request: SearchRequest,
        collection_name: str = "atlas_chunks_v1",
        enable_hybrid: bool = False,
        enable_rerank: bool = False,
    ) -> SearchResponse:
        """
        Execute vector similarity search in Qdrant based on natural language query.

        Args:
            request: Validated SearchRequest DTO containing query and filter criteria.
            collection_name: Target Qdrant collection name.
            enable_hybrid: Whether to perform BM25 sparse + dense RRF hybrid search.
            enable_rerank: Whether to execute Cross-Encoder reranking.

        Returns:
            SearchResponse containing retrieved matching text chunks and similarity scores.
        """
        if not request.tenant_id:
            raise ValueError("tenant_id is required for isolated vector retrieval.")

        logger.info(
            "Executing vector search request",
            query=request.query,
            tenant_id=request.tenant_id,
            document_id=str(request.document_id) if request.document_id else None,
            top_k=request.top_k,
        )

        document_id_str = str(request.document_id) if request.document_id else None

        if not enable_hybrid and not enable_rerank:
            # 1. Generate query vector using FastEmbed BAAI/bge-small-en-v1.5
            query_vector = self.embedding_engine.embed_query(request.query)

            # 2. Query Qdrant for nearest neighbor vectors matching filters
            scored_points = await self.qdrant_service.search_vectors(
                collection_name=collection_name,
                query_vector=query_vector,
                tenant_id=request.tenant_id,
                document_id=document_id_str,
                limit=request.top_k,
            )
            final_points = [(p, float(p.score)) for p in scored_points]
        else:
            # Hybrid / Rerank pipeline
            query_vector = self.embedding_engine.embed_query(request.query)
            try:
                dense_points = await self.qdrant_service.search_vectors(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    tenant_id=request.tenant_id,
                    document_id=document_id_str,
                    limit=request.top_k * 2,
                    using="dense",
                )
            except Exception:
                dense_points = await self.qdrant_service.search_vectors(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    tenant_id=request.tenant_id,
                    document_id=document_id_str,
                    limit=request.top_k * 2,
                )

            scored_candidates: List[tuple] = []
            try:
                sparse_vector = self.sparse_embedding_engine.embed_query(request.query)
                sparse_qdrant_vec = SparseVector(
                    indices=sparse_vector.indices.tolist() if hasattr(sparse_vector.indices, "tolist") else list(sparse_vector.indices),
                    values=sparse_vector.values.tolist() if hasattr(sparse_vector.values, "tolist") else list(sparse_vector.values),
                )
                sparse_points = await self.qdrant_service.search_vectors(
                    collection_name=collection_name,
                    query_vector=sparse_qdrant_vec,
                    tenant_id=request.tenant_id,
                    document_id=document_id_str,
                    limit=request.top_k * 2,
                    using="sparse",
                )
                scored_candidates = compute_rrf(dense_points, sparse_points)
            except Exception as e:
                logger.debug("sparse_vector_search_skipped", reason=str(e))
                scored_candidates = [(p, float(p.score)) for p in dense_points]

            if enable_rerank and self.reranker and scored_candidates:
                raw_candidates = [p for p, _ in scored_candidates]
                final_points = self.reranker.rerank(request.query, raw_candidates, top_k=request.top_k)
            else:
                final_points = scored_candidates[: request.top_k]

        # 3. Transform ScoredPoint objects into SearchResultChunk domain models
        results: List[SearchResultChunk] = []
        for point, score in final_points:
            payload = point.payload or {}
            chunk_result = SearchResultChunk(
                chunk_id=UUID(str(point.id)),
                document_id=UUID(str(payload.get("document_id"))),
                chunk_index=int(payload.get("chunk_index", 0)),
                content=str(payload.get("content", "")),
                score=float(score),
                metadata=payload.get("metadata"),
            )
            results.append(chunk_result)

        logger.info(
            "Vector search completed successfully",
            retrieved_count=len(results),
        )

        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
        )



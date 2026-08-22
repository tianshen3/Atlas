from typing import List, Optional
from uuid import UUID

from app.core.logging import logger
from app.rag.embeddings import DenseEmbeddingEngine
from app.rag.qdrant import QdrantVectorService
from app.schemas.retrieval import SearchRequest, SearchResponse, SearchResultChunk


class RetrievalService:
    """Service handling dense vector retrieval and search response assembly."""

    def __init__(
        self,
        embedding_engine: Optional[DenseEmbeddingEngine] = None,
        qdrant_service: Optional[QdrantVectorService] = None,
    ) -> None:
        self.embedding_engine = embedding_engine or DenseEmbeddingEngine()
        self.qdrant_service = qdrant_service or QdrantVectorService()

    async def search(
        self,
        request: SearchRequest,
        collection_name: str = "atlas_chunks_v1",
    ) -> SearchResponse:
        """
        Execute dense vector similarity search in Qdrant based on natural language query.

        Args:
            request: Validated SearchRequest DTO containing query and filter criteria.
            collection_name: Target Qdrant collection name.

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

        # 1. Generate query vector using FastEmbed BAAI/bge-small-en-v1.5
        query_vector = self.embedding_engine.embed_query(request.query)

        # 2. Query Qdrant for nearest neighbor vectors matching filters
        document_id_str = str(request.document_id) if request.document_id else None
        scored_points = await self.qdrant_service.search_vectors(
            collection_name=collection_name,
            query_vector=query_vector,
            tenant_id=request.tenant_id,
            document_id=document_id_str,
            limit=request.top_k,
        )

        # 3. Transform raw Qdrant ScoredPoint objects into SearchResultChunk domain models
        results: List[SearchResultChunk] = []
        for point in scored_points:
            payload = point.payload or {}
            chunk_result = SearchResultChunk(
                chunk_id=UUID(str(point.id)),
                document_id=UUID(str(payload.get("document_id"))),
                chunk_index=int(payload.get("chunk_index", 0)),
                content=str(payload.get("content", "")),
                score=float(point.score),
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

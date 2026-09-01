from typing import Any, Dict, List, Optional, Union
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
    PointStruct,
    PayloadSchemaType,
    Filter,
    FieldCondition,
    MatchValue,
    ScoredPoint,
)
from app.core.config import settings
from app.core.logging import logger


class QdrantVectorService:
    """Async wrapper for Qdrant Vector Database operations."""

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        host: str | None = None,
        port: int | None = None,
        grpc_port: int | None = None,
        prefer_grpc: bool = False,
    ) -> None:
        self.url = url or settings.QDRANT_URL
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.grpc_port = grpc_port
        self.prefer_grpc = prefer_grpc

        if self.url:
            self.client = AsyncQdrantClient(
                url=self.url,
                api_key=self.api_key,
            )
        else:
            init_kwargs = {
                "host": self.host,
                "port": self.port,
            }
            if self.grpc_port is not None:
                init_kwargs["grpc_port"] = self.grpc_port
                init_kwargs["prefer_grpc"] = self.prefer_grpc

            self.client = AsyncQdrantClient(**init_kwargs)

    async def init_collection(
        self,
        collection_name: str = "atlas_chunks_v1",
        vector_size: int = 384,
        sparse: bool = False,
    ) -> None:
        """Create Qdrant collection if not existing, and build payload indexes."""
        exists = await self.client.collection_exists(collection_name)
        if not exists:
            logger.info("Creating Qdrant collection", collection_name=collection_name, vector_size=vector_size, sparse=sparse)
            if sparse:
                await self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config={"dense": VectorParams(size=vector_size, distance=Distance.COSINE)},
                    sparse_vectors_config={"sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False))},
                )
            else:
                await self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )

            # Create payload keyword indexes for fast tenant and document filtering
            await self.client.create_payload_index(
                collection_name=collection_name,
                field_name="tenant_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            await self.client.create_payload_index(
                collection_name=collection_name,
                field_name="document_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            logger.info("Qdrant collection and payload indexes initialized", collection_name=collection_name)
        else:
            logger.info("Qdrant collection already exists", collection_name=collection_name)

    async def upsert_chunk_vectors(
        self,
        collection_name: str,
        points: list[PointStruct],
    ) -> None:
        """Upsert a list of PointStruct vectors and payloads into Qdrant."""
        if not points:
            return
        await self.client.upsert(
            collection_name=collection_name,
            points=points,
        )
        logger.info("Upserted points into Qdrant", collection_name=collection_name, count=len(points))

    async def search_vectors(
        self,
        collection_name: str,
        query_vector: Any,
        tenant_id: str,
        document_id: str | None = None,
        limit: int = 5,
        score_threshold: float | None = None,
        using: str | None = None,
    ) -> list[ScoredPoint]:
        """Search Qdrant collection for nearest vectors matching tenant_id and optional document_id."""
        must_conditions = [
            FieldCondition(
                key="tenant_id",
                match=MatchValue(value=tenant_id),
            )
        ]
        if document_id is not None:
            must_conditions.append(
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            )

        query_filter = Filter(must=must_conditions)

        search_kwargs: Dict[str, Any] = {
            "collection_name": collection_name,
            "query_vector": query_vector,
            "query_filter": query_filter,
            "limit": limit,
            "score_threshold": score_threshold,
            "with_payload": True,
        }
        if using is not None:
            search_kwargs["using"] = using

        if hasattr(self.client, "search"):
            results = await self.client.search(**search_kwargs)
        else:
            search_kwargs["query"] = query_vector
            del search_kwargs["query_vector"]
            res = await self.client.query_points(**search_kwargs)
            results = res.points

        logger.info(
            "Vector search completed",
            collection_name=collection_name,
            tenant_id=tenant_id,
            document_id=document_id,
            result_count=len(results),
            using=using,
        )
        return results

    async def close(self) -> None:
        """Close underlying AsyncQdrantClient connection."""
        await self.client.close()


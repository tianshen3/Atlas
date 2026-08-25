from typing import Optional, List
from app.core.config import settings
from app.core.logging import logger
from app.rag.generator import LLMGeneratorEngine
from app.rag.prompts import build_grounded_messages
from app.schemas.chat import ChatRequest, ChatResponse, CitationSource
from app.schemas.retrieval import SearchRequest
from app.services.retrieval_service import RetrievalService


class ChatService:
    """Orchestrator combining Vector Retrieval, Grounded Prompting, and LLM Generation."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        generator_engine: Optional[LLMGeneratorEngine] = None,
    ) -> None:
        self.retrieval_service = retrieval_service or RetrievalService()
        self.generator_engine = generator_engine or LLMGeneratorEngine()

    async def generate_chat_response(
        self,
        request: ChatRequest,
    ) -> ChatResponse:
        """
        Execute end-to-end grounded chat generation workflow.

        Args:
            request: Validated ChatRequest DTO containing query, tenant_id, and filters.

        Returns:
            ChatResponse DTO with natural language answer and source citations.
        """
        logger.info(
            "Executing ChatService grounded generation",
            query=request.query,
            tenant_id=request.tenant_id,
            top_k=request.top_k,
        )

        # 1. Execute vector search via RetrievalService
        search_req = SearchRequest(
            query=request.query,
            tenant_id=request.tenant_id,
            document_id=request.document_id,
            top_k=request.top_k,
        )
        search_res = await self.retrieval_service.search(search_req)
        chunks = search_res.results

        # 2. Empty Retrieval Guard: Short-circuit if no relevant context found
        if not chunks:
            logger.info("Empty retrieval context for query. Short-circuiting LLM call.", query=request.query)
            fallback_answer = (
                "I cannot find sufficient information in the provided enterprise documents "
                "to answer this question."
            )
            return ChatResponse(
                query=request.query,
                answer=fallback_answer,
                sources=[],
                model_used=request.model or self.generator_engine.default_model,
                provider_used=self.generator_engine.provider,
                total_sources=0,
            )

        # 3. Build grounded ChatCompletion prompt messages with <context> XML tags
        messages = build_grounded_messages(query=request.query, chunks=chunks)

        # 4. Generate answer via OpenAI-compatible LLMGeneratorEngine
        answer = await self.generator_engine.generate_answer(
            messages=messages,
            model=request.model,
        )

        # 5. Extract verified citation sources
        sources: List[CitationSource] = []
        for idx, chunk in enumerate(chunks, start=1):
            meta = chunk.metadata or {}
            source = CitationSource(
                source_index=idx,
                document_id=chunk.document_id,
                chunk_id=chunk.chunk_id,
                file_name=meta.get("file_name", "Unknown"),
                page_number=meta.get("page_number", "N/A"),
                score=chunk.score,
            )
            sources.append(source)

        logger.info(
            "ChatResponse generated successfully",
            query=request.query,
            sources_count=len(sources),
        )

        return ChatResponse(
            query=request.query,
            answer=answer,
            sources=sources,
            model_used=request.model or self.generator_engine.default_model,
            provider_used=self.generator_engine.provider,
            total_sources=len(sources),
        )

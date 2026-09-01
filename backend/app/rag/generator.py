import asyncio
from typing import AsyncGenerator, Optional, List, Dict, Any
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError, APIConnectionError

from app.core.config import settings
from app.core.logging import logger


class LLMGeneratorEngine:
    """Async engine for OpenAI-compatible LLM inference (OpenRouter, Groq, OpenAI)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.LLM_API_KEY
        self.base_url = base_url or settings.LLM_BASE_URL
        self.default_model = default_model or settings.LLM_MODEL
        self.temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        self.max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS
        self.timeout = timeout if timeout is not None else settings.LLM_TIMEOUT_SECONDS
        self.max_retries = max_retries if max_retries is not None else settings.LLM_MAX_RETRIES
        self.provider = settings.LLM_PROVIDER

        # Fallback placeholder key for offline/mock testing if key is empty
        effective_key = self.api_key if self.api_key else "placeholder_dev_key"

        init_kwargs: Dict[str, Any] = {
            "api_key": effective_key,
            "timeout": self.timeout,
        }
        if self.base_url:
            init_kwargs["base_url"] = self.base_url

        self.client = AsyncOpenAI(**init_kwargs)

    def _get_candidate_models(self, requested_model: Optional[str] = None) -> List[str]:
        primary = requested_model or self.default_model
        candidates = [primary]
        if self.provider == "gemini":
            fallbacks = [
                "gemini-3.5-flash-lite",
                "gemini-3.5-flash",
                "gemini-flash-lite-latest",
                "gemini-flash-latest",
            ]
            for fb in fallbacks:
                if fb not in candidates:
                    candidates.append(fb)
        return candidates

    async def generate_answer(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate grounded answer completion with model fallback cascade and retries.
        """
        candidates = self._get_candidate_models(model)
        tokens_limit = max_tokens or self.max_tokens

        logger.info(
            "Executing LLM generation request",
            provider=self.provider,
            primary_model=candidates[0],
            candidates_count=len(candidates),
            message_count=len(messages),
        )

        last_exception = None

        for target_model in candidates:
            attempt = 0
            while attempt <= self.max_retries:
                try:
                    response = await self.client.chat.completions.create(
                        model=target_model,
                        messages=messages,  # type: ignore
                        temperature=self.temperature,
                        max_tokens=tokens_limit,
                    )
                    content = response.choices[0].message.content or ""
                    logger.info(
                        "LLM generation completed successfully",
                        model=target_model,
                        content_length=len(content),
                    )
                    return content

                except (RateLimitError, APITimeoutError, APIConnectionError, APIError) as e:
                    last_exception = e
                    status_code = getattr(e, "status_code", None)
                    # For 503 (High Demand) or 429 (Quota), break inner retry to cascade immediately to next model
                    if status_code in (503, 429, 500, 502, 504):
                        logger.warning(
                            "Transient provider status code, cascading to next model candidate...",
                            model=target_model,
                            status_code=status_code,
                            error=str(e),
                        )
                        break

                    attempt += 1
                    if attempt > self.max_retries:
                        break

                    backoff_seconds = 2.0 ** attempt
                    logger.warning(
                        "Transient LLM provider failure, retrying...",
                        model=target_model,
                        attempt=attempt,
                        backoff_seconds=backoff_seconds,
                        error=str(e),
                    )
                    await asyncio.sleep(backoff_seconds)

        raise RuntimeError(f"LLM generation failed across all model candidates: {str(last_exception)}")

    async def generate_answer_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Yield completion tokens incrementally with automatic model fallback cascading.
        """
        candidates = self._get_candidate_models(model)
        tokens_limit = max_tokens or self.max_tokens

        logger.info(
            "Starting streaming LLM request",
            provider=self.provider,
            primary_model=candidates[0],
            candidates_count=len(candidates),
        )

        last_exception = None

        for target_model in candidates:
            try:
                response_stream = await self.client.chat.completions.create(
                    model=target_model,
                    messages=messages,  # type: ignore
                    temperature=self.temperature,
                    max_tokens=tokens_limit,
                    stream=True,
                )

                async for chunk in response_stream:  # type: ignore
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return

            except (RateLimitError, APITimeoutError, APIConnectionError, APIError, Exception) as e:
                last_exception = e
                logger.warning(
                    "Streaming connection failed on candidate model, cascading to fallback...",
                    model=target_model,
                    error=str(e),
                )
                continue

        logger.error("All streaming model candidates failed", error=str(last_exception))
        raise RuntimeError(f"LLM streaming failed across all candidates: {str(last_exception)}")

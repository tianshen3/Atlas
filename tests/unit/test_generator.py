import pytest
from unittest.mock import AsyncMock, MagicMock
from openai import RateLimitError
from app.rag.generator import LLMGeneratorEngine


@pytest.mark.asyncio
async def test_llm_generator_generate_answer_success():
    generator = LLMGeneratorEngine(api_key="test_key", base_url="https://openrouter.ai/api/v1")
    
    mock_choice = MagicMock()
    mock_choice.message.content = "ATLAS is an enterprise RAG system [Source 1]."
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    
    generator.client.chat.completions.create = AsyncMock(return_value=mock_response)

    messages = [
        {"role": "system", "content": "Grounded system prompt"},
        {"role": "user", "content": "What is ATLAS?"},
    ]

    answer = await generator.generate_answer(messages)

    assert answer == "ATLAS is an enterprise RAG system [Source 1]."
    generator.client.chat.completions.create.assert_called_once_with(
        model="meta-llama/llama-3.3-70b-instruct:free",
        messages=messages,
        temperature=0.2,
        max_tokens=1000,
    )


@pytest.mark.asyncio
async def test_llm_generator_retry_on_rate_limit():
    generator = LLMGeneratorEngine(
        api_key="test_key",
        max_retries=1,
    )
    
    mock_choice = MagicMock()
    mock_choice.message.content = "Success answer after retry."
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    # First call raises RateLimitError, second call succeeds
    rate_limit_err = RateLimitError(
        message="Rate limit exceeded",
        response=MagicMock(status_code=429, headers={}),
        body=None,
    )
    
    generator.client.chat.completions.create = AsyncMock(side_effect=[rate_limit_err, mock_response])

    messages = [{"role": "user", "content": "Test prompt"}]
    answer = await generator.generate_answer(messages)

    assert answer == "Success answer after retry."
    assert generator.client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_llm_generator_stream_tokens():
    generator = LLMGeneratorEngine(api_key="test_key")

    chunk1 = MagicMock()
    chunk1.choices = [MagicMock(delta=MagicMock(content="ATLAS "))]
    chunk2 = MagicMock()
    chunk2.choices = [MagicMock(delta=MagicMock(content="RAG."))]

    async def mock_stream_generator():
        for c in [chunk1, chunk2]:
            yield c

    generator.client.chat.completions.create = AsyncMock(return_value=mock_stream_generator())

    tokens = []
    async for token in generator.generate_answer_stream([{"role": "user", "content": "hi"}]):
        tokens.append(token)

    assert tokens == ["ATLAS ", "RAG."]

import os
import asyncio

import pytest

from app.services.openai_service import OpenAIService


@pytest.mark.asyncio
@pytest.mark.skipif(not (os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")), reason="OPENAI_API_KEY not set")
async def test_openai_service_responsive():
    """Skip unless OPENAI_API_KEY is set. Ensures chat_completion returns non-empty content and usage."""
    svc = OpenAIService()

    class Req:
        user_prompt = "Hello from test - please respond with a short message and the model name"
        model = "gpt-4o-mini"
        # Use model-default friendly temperature to avoid unsupported_value errors
        temperature = 1.0
        max_tokens = 64
        max_completion_tokens = 64

    content, usage = await svc.chat_completion(Req())

    assert content is not None
    assert isinstance(content, str)
    # Allow short content but ensure it's not empty
    assert content.strip() != ""
    # Usage may be None for some clients, but if present it should be a dict-like
    if usage is not None:
        assert isinstance(usage, dict)

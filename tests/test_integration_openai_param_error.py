import pytest
from fastapi.testclient import TestClient

from app.main import app


class DummyAIError:
    async def chat_completion(self, request):
        # Simulate OpenAI returning an unsupported parameter error
        from app.services.openai_service import OpenAIParameterError

        raise OpenAIParameterError(param="max_tokens", message="Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.")


@pytest.fixture(autouse=True)
def patch_openai(monkeypatch):
    # Patch OpenAIService so the endpoint uses our dummy that raises the error
    from app.services import openai_service

    monkeypatch.setattr(openai_service, "OpenAIService", lambda: DummyAIError())
    # Also patch the reference imported by the ai endpoint module
    import app.api.api_v1.endpoints.ai as ai_module
    monkeypatch.setattr(ai_module, "OpenAIService", lambda: DummyAIError())


def test_api_returns_400_on_openai_param_error():
    client = TestClient(app)

    payload = {"user_prompt": "Say hi", "max_tokens": 64}
    resp = client.post("/api/v1/ai/chat", json=payload)

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data
    detail = data["detail"]
    assert detail.get("error") == "invalid_request"
    assert detail.get("param") == "max_tokens"
    assert "max_completion_tokens" in resp.text or "max_tokens" in resp.text

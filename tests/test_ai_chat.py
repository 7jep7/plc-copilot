import pytest
from fastapi.testclient import TestClient

from app.main import app


class DummyAI:
    async def chat_completion(self, request):
        return ("Hello from dummy model", {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8})


@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    # Patch OpenAIService to avoid real API calls
    from app.services import openai_service

    # Patch the class in the service module
    monkeypatch.setattr(openai_service, "OpenAIService", lambda: DummyAI())

    # Also patch the reference imported by the ai endpoint module so it uses DummyAI
    import app.api.api_v1.endpoints.ai as ai_module
    monkeypatch.setattr(ai_module, "OpenAIService", lambda: DummyAI())

    # Patch DB dependency to avoid real DB connections
    def fake_get_db():
        class DummySession:
            def close(self):
                pass
        yield DummySession()

    from app.core import database
    monkeypatch.setattr(database, "get_db", fake_get_db)


def test_ai_chat_endpoint():
    client = TestClient(app)

    payload = {"user_prompt": "Say hi"}
    resp = client.post("/api/v1/ai/chat", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "Hello from dummy model"
    assert data["model"] == "gpt-5-nano"
    assert "usage" in data

import asyncio

from app.services.openai_service import OpenAIService


class DummyClient:
    def __init__(self):
        self.captured = None

    class Chat:
        def __init__(self, parent):
            self._parent = parent

        class Completions:
            def __init__(self, parent):
                self._parent = parent

            def create(self, **kwargs):
                # Store the kwargs so test can inspect them
                # Completions._parent is the DummyClient instance
                self._parent.captured = kwargs
                # Return a dummy response structure with nested attributes used by the service
                class DummyUsage:
                    prompt_tokens = 1
                    completion_tokens = 1
                    total_tokens = 2

                class DummyChoice:
                    class Message:
                        content = "dummy"

                    message = Message()

                class DummyResponse:
                    choices = [DummyChoice()]
                    usage = DummyUsage()

                return DummyResponse()

    @property
    def chat(self):
        # Provide names matching service expectations: client.chat.completions.create
        ch = self.Chat(self)
        ch.completions = self.Chat.Completions(self)
        return ch


def test_service_uses_max_completion_tokens():
    svc = OpenAIService()
    dummy = DummyClient()
    svc.client = dummy

    class Req:
        user_prompt = "hi"
        model = "gpt-4o-mini"
        temperature = 0.5
        max_tokens = 123

    # Run the async method
    content, usage = asyncio.get_event_loop().run_until_complete(svc.chat_completion(Req()))

    captured = dummy.captured
    assert captured is not None, "No call captured"
    # It should have max_completion_tokens and not max_tokens
    assert "max_completion_tokens" in captured, f"max_completion_tokens not in {captured}"
    assert "max_tokens" not in captured, f"max_tokens should not be sent to API: {captured}"

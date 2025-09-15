from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ChatRequest(BaseModel):
    user_prompt: str
    model: Optional[str] = "gpt-5-nano"
    temperature: float = 0.7
    # Accept both legacy `max_tokens` and new `max_completion_tokens`.
    max_tokens: Optional[int] = Field(default=512, description="Legacy alias for max_completion_tokens")
    max_completion_tokens: Optional[int] = Field(default=None, description="Preferred field for completion token limit")

    def get_effective_max_completion_tokens(self) -> int:
        """Return the token limit to pass to OpenAI: prefer explicit max_completion_tokens, fall back to max_tokens."""
        return int(self.max_completion_tokens or self.max_tokens or 512)


class ChatResponse(BaseModel):
    model: str
    content: str
    usage: Optional[Dict[str, Any]] = None

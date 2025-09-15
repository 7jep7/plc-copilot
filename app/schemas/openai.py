from pydantic import BaseModel
from typing import Optional, Dict, Any


class ChatRequest(BaseModel):
    user_prompt: str
    model: Optional[str] = "gpt-5-nano"
    temperature: float = 0.7
    max_tokens: int = 512


class ChatResponse(BaseModel):
    model: str
    content: str
    usage: Optional[Dict[str, Any]] = None

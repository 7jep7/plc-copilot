from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, Union


class ChatRequest(BaseModel):
    user_prompt: str
    model: Optional[str] = "gpt-5-nano"
    temperature: float = 1.0
    max_completion_tokens: Optional[int] = Field(
        default=512, 
        description="Maximum number of completion tokens to generate",
        example=512,
        ge=1  # Ensure it's at least 1 if provided
    )


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    model: str
    content: str
    usage: Optional[Dict[str, Any]] = None

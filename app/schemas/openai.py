from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, Union
from app.core.models import ModelConfig


class ChatRequest(BaseModel):
    user_prompt: str
    model: Optional[str] = ModelConfig.CONVERSATION_MODEL
    temperature: float = 1.0
    max_completion_tokens: Optional[int] = Field(
        default=512, 
        description="Maximum number of completion tokens to generate",
        example=512,
        ge=1  # Ensure it's at least 1 if provided
    )
    stage: Optional[str] = Field(
        default=None,
        description="Optional conversation stage for stage-specific prompts (project_kickoff, gather_requirements, code_generation, refinement_testing)"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation ID to include conversation context in the request"
    )


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    model: str
    content: str
    usage: Optional[Dict[str, Any]] = None

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
import structlog

from app.schemas.openai import ChatRequest, ChatResponse
from app.services.openai_service import OpenAIService
from app.core.database import get_db

router = APIRouter()
logger = structlog.get_logger()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Simple chat endpoint that relays a user prompt to an OpenAI model and returns the text response."""
    logger.info("AI chat request", model=request.model)

    ai = OpenAIService()

    try:
        content, usage = await ai.chat_completion(request)
        return ChatResponse(model=request.model or "gpt-5-nano", content=content, usage=usage)

    except Exception as e:
        logger.error("AI chat failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

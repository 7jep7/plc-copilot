from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
import structlog

from app.schemas.openai import ChatRequest, ChatResponse
from app.services.openai_service import OpenAIService, OpenAIParameterError
from app.core.database import get_db

router = APIRouter()
logger = structlog.get_logger()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Simple chat endpoint that relays a user prompt to an OpenAI model and returns the text response.
    
    For full context-aware workflows, use /api/v1/context/update endpoint instead.
    """
    logger.info("AI chat request", model=request.model)

    ai = OpenAIService()

    try:
        # Simple chat without conversation dependencies
        content, usage = await ai.chat_completion(request)
            
        return ChatResponse(model=request.model or "gpt-4o-mini", content=content, usage=usage)
        
    except OpenAIParameterError as e:
        # Surface parameter/value issues from OpenAI as client errors (400)
        logger.warning("OpenAI parameter error", param=e.param, error=e.message)
        detail = {"error": "invalid_request", "param": e.param, "message": e.message}
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    except Exception as e:
        logger.error("AI chat failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

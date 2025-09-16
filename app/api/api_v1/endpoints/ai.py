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
    
    Supports optional stage-specific prompts for backwards compatibility with conversation system.
    For full conversation workflows, prefer using /api/v1/conversations/ endpoints.
    """
    logger.info("AI chat request", model=request.model, stage=request.stage)

    ai = OpenAIService()

    try:
        # If stage is specified, use stage-specific system prompts
        if request.stage:
            from app.schemas.conversation import ConversationStage, ConversationState
            from app.services.prompt_templates import PromptTemplateFactory
            
            try:
                stage = ConversationStage(request.stage)
                template = PromptTemplateFactory.get_template(stage)
                
                # Create minimal conversation state for template
                conversation_state = ConversationState(
                    conversation_id=request.conversation_id or "temp",
                    current_stage=stage
                )
                
                # Build stage-specific prompts
                system_prompt = template.build_system_prompt(conversation_state)
                user_prompt = template.build_user_prompt(request.user_prompt, conversation_state)
                
                # Use structured messages
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                
                content, usage = await ai.chat_completion(request, messages=messages)
                
            except ValueError:
                # Invalid stage, fall back to simple chat
                logger.warning("Invalid stage provided, falling back to simple chat", stage=request.stage)
                content, usage = await ai.chat_completion(request)
        else:
            # Simple chat without stage-specific prompts
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

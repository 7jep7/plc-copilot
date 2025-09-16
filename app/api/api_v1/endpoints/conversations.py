"""API endpoints for multi-stage PLC-Copilot conversations."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.schemas.conversation import (
    ConversationRequest,
    ConversationResponse,
    ConversationState,
    ConversationStage,
    StageTransitionRequest
)
from app.services.conversation_orchestrator import ConversationOrchestrator

router = APIRouter()

# Global orchestrator instance
# TODO: Replace with dependency injection in production
orchestrator = ConversationOrchestrator()


@router.post("/", response_model=ConversationResponse)
async def start_conversation(request: ConversationRequest):
    """
    Start a new conversation or continue an existing one.
    
    This is the main endpoint for interacting with the PLC-Copilot conversation system.
    """
    try:
        response = await orchestrator.process_message(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process conversation: {str(e)}")


@router.get("/{conversation_id}", response_model=ConversationState)
async def get_conversation(conversation_id: str):
    """Get conversation state and history."""
    conversation = orchestrator.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """Get conversation message history."""
    messages = orchestrator.get_conversation_history(conversation_id)
    if not messages and not orchestrator.get_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, "messages": messages}


@router.post("/{conversation_id}/stage")
async def transition_stage(conversation_id: str, request: StageTransitionRequest):
    """
    Manually transition conversation to a different stage.
    
    Useful for testing or when automatic stage detection needs override.
    """
    conversation = orchestrator.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    try:
        # Force transition by setting target stage
        await orchestrator._transition_to_stage(conversation, request.target_stage)
        return {"status": "success", "new_stage": request.target_stage}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Stage transition failed: {str(e)}")


@router.get("/{conversation_id}/stage/suggestions")
async def get_stage_suggestions(conversation_id: str):
    """Get suggested next stages based on current conversation state."""
    conversation = orchestrator.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    from app.services.stage_detection_service import StageTransitionRules
    
    valid_transitions = StageTransitionRules.get_valid_transitions(conversation.current_stage)
    next_suggestion = await orchestrator._suggest_next_stage(conversation)
    
    return {
        "current_stage": conversation.current_stage,
        "valid_transitions": valid_transitions,
        "suggested_next": next_suggestion,
        "stage_progress": orchestrator._get_stage_progress(conversation),
        "suggested_actions": orchestrator._get_suggested_actions(conversation)
    }


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation and its history."""
    if conversation_id in orchestrator.conversations:
        del orchestrator.conversations[conversation_id]
        return {"status": "deleted", "conversation_id": conversation_id}
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.get("/")
async def list_conversations():
    """List all active conversations (for development/debugging)."""
    conversations = []
    for conv_id, conv_state in orchestrator.conversations.items():
        conversations.append({
            "conversation_id": conv_id,
            "current_stage": conv_state.current_stage,
            "created_at": conv_state.created_at,
            "updated_at": conv_state.updated_at,
            "message_count": len(conv_state.messages)
        })
    return {"conversations": conversations}


@router.post("/{conversation_id}/reset")
async def reset_conversation(conversation_id: str, target_stage: Optional[ConversationStage] = None):
    """
    Reset conversation to a specific stage or back to requirements gathering.
    
    Useful for restarting the conversation flow.
    """
    conversation = orchestrator.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    reset_stage = target_stage or ConversationStage.PROJECT_KICKOFF
    
    try:
        # Reset to target stage
        await orchestrator._transition_to_stage(conversation, reset_stage)
        
        # Clear stage-specific state
        if reset_stage == ConversationStage.PROJECT_KICKOFF:
            conversation.requirements = None
            conversation.qa = None
            conversation.generation = None
            conversation.refinement = None
        elif reset_stage == ConversationStage.GATHER_REQUIREMENTS:
            conversation.qa = None
            conversation.generation = None
            conversation.refinement = None
        elif reset_stage == ConversationStage.CODE_GENERATION:
            conversation.generation = None
            conversation.refinement = None
        elif reset_stage == ConversationStage.REFINEMENT_TESTING:
            conversation.refinement = None
        
        return {
            "status": "reset",
            "conversation_id": conversation_id,
            "new_stage": reset_stage
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Reset failed: {str(e)}")


# Health check and status endpoints
@router.get("/health")
async def health_check():
    """Health check for conversation system."""
    return {
        "status": "healthy",
        "active_conversations": len(orchestrator.conversations),
        "available_stages": [stage.value for stage in ConversationStage]
    }
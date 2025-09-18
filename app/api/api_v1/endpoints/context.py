"""
Context API endpoints for the simplified OpenAI Assistant approach.

This module provides:
- POST /api/v1/context/update - Main endpoint for all interactions using OpenAI Assistant
- File upload support with RAG processing
- Three core interaction cases handling
- MCQ handling and progress tracking
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from io import BytesIO

from app.schemas.context import (
    ContextUpdateRequest,
    ContextUpdateResponse, 
    ProjectContext,
    Stage,
    StageTransitionRequest,
    StageTransitionResponse
)
from app.services.simplified_context_service import SimplifiedContextService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/update", response_model=ContextUpdateResponse)
async def update_context(
    # JSON fields
    message: Optional[str] = Form(None),
    mcq_responses: Optional[str] = Form(None),  # JSON string of list
    previous_copilot_message: Optional[str] = Form(None),
    current_context: str = Form(...),  # JSON string of ProjectContext
    current_stage: Stage = Form(Stage.GATHERING_REQUIREMENTS),
    # File uploads
    files: List[UploadFile] = File(default=[])
) -> ContextUpdateResponse:
    """
    Update project context using the simplified OpenAI Assistant approach.
    
    Handles three core interaction cases:
    1. Project kickoff (no context, no file) → start gathering info
    2. Context update (context exists, no file) → update with assistant  
    3. File upload (file + optional context) → extract + embed + merge → assistant call
    
    Args:
        message: User message or response
        mcq_responses: JSON string of selected MCQ options
        previous_copilot_message: Previous message from copilot for conversation continuity
        current_context: JSON string of current ProjectContext
        current_stage: Current workflow stage
        files: List of uploaded files to process with RAG
        
    Returns:
        Complete context update response with updated context and UI state
    """
    try:
        logger.info(f"Context update request for stage: {current_stage}")
        
        # Parse JSON inputs
        import json
        
        try:
            context_data = json.loads(current_context)
            context = ProjectContext(**context_data)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid current_context JSON: {str(e)}"
            )
        
        mcq_list = []
        if mcq_responses:
            try:
                mcq_list = json.loads(mcq_responses)
                if not isinstance(mcq_list, list):
                    raise ValueError("mcq_responses must be a list")
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid mcq_responses JSON: {str(e)}"
                )
        
        # Create request object
        request = ContextUpdateRequest(
            message=message,
            mcq_responses=mcq_list,
            previous_copilot_message=previous_copilot_message,
            current_context=context,
            current_stage=current_stage
        )
        
        # Process uploaded files
        file_data_list = []
        if files and any(file.filename for file in files):
            for file in files:
                if file.filename and file.size and file.size > 0:
                    content = await file.read()
                    file_data_list.append(BytesIO(content))
                    logger.info(f"Processing uploaded file: {file.filename} ({file.size} bytes)")
        
        # Process context update with simplified service
        context_service = SimplifiedContextService()
        response = await context_service.process_context_update(
            request, 
            uploaded_files=file_data_list if file_data_list else None,
            session_id=getattr(context, 'session_id', None)
        )
        
        logger.info(f"Context update completed, new stage: {response.current_stage}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing context update: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/transition", response_model=StageTransitionResponse)
async def transition_stage(
    request: StageTransitionRequest
) -> StageTransitionResponse:
    """
    Manually transition to a specific workflow stage.
    
    This endpoint allows explicit stage control, bypassing AI recommendations.
    
    Args:
        request: Stage transition request with target stage and force flag
        
    Returns:
        Stage transition result
    """
    try:
        logger.info(f"Manual stage transition requested: {request.target_stage}")
        
        # Validate transition (basic rules)
        if request.target_stage == Stage.GATHERING_REQUIREMENTS:
            # Can't go back to requirements gathering
            return StageTransitionResponse(
                new_stage=request.target_stage,
                transition_message="Cannot return to requirements gathering stage",
                success=False
            )
        
        # Allow other transitions
        return StageTransitionResponse(
            new_stage=request.target_stage,
            transition_message=f"Successfully transitioned to {request.target_stage.value}",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error in stage transition: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Stage transition failed: {str(e)}"
        )


@router.get("/health")
async def context_health():
    """Health check endpoint for context API."""
    return {"status": "healthy", "service": "context-api"}
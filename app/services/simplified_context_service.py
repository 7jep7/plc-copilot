"""
Simplified Context Service using OpenAI Assistant with Vector Store integration.

This service handles the three core interaction cases:
1. Project kickoff (no context, no file) → start gathering info
2. Context update (context exists, no file) → update with assistant
3. File upload (file + optional context) → upload to vector store → assistant call

Uses the AssistantService and VectorStoreService for streamlined processing.
The assistant automatically accesses files from vector store vs_68cba48e219c8191acc9d25d32cf8130.
"""

import uuid
import logging
from typing import Dict, List, Optional, Any
from io import BytesIO

from app.schemas.context import (
    ProjectContext, ContextUpdateRequest, ContextUpdateResponse, Stage
)
from app.services.assistant_service import AssistantService
from app.services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)


class SimplifiedContextService:
    """Simplified context service using OpenAI Assistant API with Vector Store."""
    
    def __init__(self):
        self.assistant_service = AssistantService()
        self.vector_store_service = VectorStoreService()
        self._active_sessions: Dict[str, List[str]] = {}  # Track uploaded file IDs per session
    
    async def process_context_update(
        self,
        request: ContextUpdateRequest,
        uploaded_files: Optional[List[BytesIO]] = None,
        session_id: Optional[str] = None
    ) -> ContextUpdateResponse:
        """
        Process context update with the three core cases.
        
        Args:
            request: Context update request
            uploaded_files: Optional uploaded files
            session_id: Session ID for RAG (generated if not provided)
            
        Returns:
            Context update response with new state
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Determine which case we're handling
            has_context = bool(
                request.current_context and 
                (request.current_context.device_constants or request.current_context.information)
            )
            has_files = bool(uploaded_files)
            
            logger.info(f"Processing context update: has_context={has_context}, has_files={has_files}, stage={request.current_stage}, session_id={session_id}")
            
            if has_files:
                # Case 3: File upload with optional context
                return await self._handle_file_upload_case(
                    request, uploaded_files, session_id
                )
            elif has_context:
                # Case 2: Context exists, update with assistant
                return await self._handle_context_update_case(request, session_id)
            else:
                # Case 1: Project kickoff
                return await self._handle_project_kickoff_case(request, session_id)
                
        except Exception as e:
            logger.error(f"Error processing context update: {e}")
            return self._create_error_response(str(e), request)
    
    async def _handle_project_kickoff_case(
        self, 
        request: ContextUpdateRequest, 
        session_id: str
    ) -> ContextUpdateResponse:
        """Handle Case 1: Project kickoff with no context or files."""
        
        logger.info("Handling project kickoff case")
        
        # Check if this is an off-topic start
        user_message = request.message or ""
        if not self._is_plc_related(user_message):
            # Offer sample projects via MCQ
            return self._create_sample_projects_response(session_id)
        
        # Start gathering requirements with assistant
        assistant_response = await self.assistant_service.process_message(
            user_message=user_message,
            current_context=None,
            file_ids=None
        )
        
        return self._convert_assistant_to_context_response(
            assistant_response, session_id, Stage.GATHERING_REQUIREMENTS
        )
    
    async def _handle_context_update_case(
        self, 
        request: ContextUpdateRequest, 
        session_id: str
    ) -> ContextUpdateResponse:
        """Handle Case 2: Context exists, update with assistant."""
        
        logger.info("Handling context update case")
        
        # Build user message with MCQ responses if available
        user_message = self._build_user_message_with_mcq(request)
        
        # Prepare current context for assistant
        current_context = {
            "device_constants": request.current_context.device_constants or {},
            "information": request.current_context.information or ""
        }
        
        # Get file IDs if session has uploaded files
        file_ids = self._active_sessions.get(session_id, [])
        
        # Process with assistant (it will automatically search vector store if needed)
        assistant_response = await self.assistant_service.process_message(
            user_message=user_message,
            current_context=current_context,
            file_ids=file_ids
        )
        
        # Determine stage based on progress
        new_stage = self._determine_stage_from_progress(
            assistant_response.get("gathering_requirements_estimated_progress", 0)
        )
        
        return self._convert_assistant_to_context_response(
            assistant_response, session_id, new_stage
        )
    
    async def _handle_file_upload_case(
        self, 
        request: ContextUpdateRequest,
        uploaded_files: List[BytesIO], 
        session_id: str
    ) -> ContextUpdateResponse:
        """Handle Case 3: File upload with optional context."""
        
        logger.info(f"Handling file upload case with {len(uploaded_files)} files")
        
        # Generate filenames for uploaded files
        filenames = [f"uploaded_file_{i+1}.pdf" for i in range(len(uploaded_files))]
        
        # Upload files to OpenAI vector store
        file_metadata = await self.vector_store_service.upload_files_to_vector_store(
            uploaded_files, filenames, session_id
        )
        
        # Track uploaded file IDs for this session
        file_ids = [meta["file_id"] for meta in file_metadata if "file_id" in meta]
        if session_id not in self._active_sessions:
            self._active_sessions[session_id] = []
        self._active_sessions[session_id].extend(file_ids)
        
        # Build user message
        user_message = request.message or f"I've uploaded {len(uploaded_files)} file(s) for analysis."
        user_message = self._build_user_message_with_mcq(request, user_message)
        
        # Prepare current context
        current_context = None
        if request.current_context:
            current_context = {
                "device_constants": request.current_context.device_constants or {},
                "information": request.current_context.information or ""
            }
        
        # Process with assistant (it will automatically search vector store for uploaded files)
        assistant_response = await self.assistant_service.process_message(
            user_message=user_message,
            current_context=current_context,
            file_ids=file_ids
        )
        
        # Add file processing metadata to response
        assistant_response["file_processing"] = {
            "files_processed": len(uploaded_files),
            "files_uploaded": len(file_metadata),
            "session_id": session_id,
            "vector_store_id": "vs_68cba48e219c8191acc9d25d32cf8130"
        }
        
        # Determine stage
        new_stage = self._determine_stage_from_progress(
            assistant_response.get("gathering_requirements_estimated_progress", 0)
        )
        
        return self._convert_assistant_to_context_response(
            assistant_response, session_id, new_stage
        )
    
    def _is_plc_related(self, message: str) -> bool:
        """Check if the message is related to PLC programming."""
        plc_keywords = [
            "plc", "programmable logic", "structured text", "ladder logic",
            "automation", "industrial", "control", "scada", "hmi",
            "motor", "sensor", "actuator", "conveyor", "process control",
            "safety", "interlock", "tag", "variable", "function block"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in plc_keywords)
    
    def _create_sample_projects_response(self, session_id: str) -> ContextUpdateResponse:
        """Create response with sample project options."""
        
        return ContextUpdateResponse(
            updated_context=ProjectContext(
                device_constants={},
                information=""
            ),
            chat_message="I'd be happy to help you with PLC programming! Here are some sample projects to get started:",
            is_mcq=True,
            mcq_question="Which type of project would you like to work on?",
            mcq_options=[
                "Conveyor Belt Control System with Safety Interlocks",
                "Motor Speed Control with VFD Integration", 
                "Process Control with PID Temperature Regulation"
            ],
            is_multiselect=False,
            generated_code=None,
            current_stage=Stage.GATHERING_REQUIREMENTS,
            gathering_requirements_estimated_progress=0.1
        )
    
    def _build_user_message_with_mcq(
        self, 
        request: ContextUpdateRequest, 
        base_message: Optional[str] = None
    ) -> str:
        """Build user message including MCQ responses if available."""
        
        parts = []
        
        if base_message:
            parts.append(base_message)
        elif request.message:
            parts.append(request.message)
        
        # Add MCQ responses
        if request.mcq_responses:
            parts.append("Selected options:")
            for i, response in enumerate(request.mcq_responses, 1):
                parts.append(f"{i}. {response}")
        
        # Add conversation continuity
        if request.previous_copilot_message:
            parts.insert(0, f"Previous assistant message: {request.previous_copilot_message}")
        
        return "\n\n".join(parts) if parts else "Continue with the project."
    
    def _determine_stage_from_progress(self, progress: float) -> Stage:
        """Determine stage based on progress value."""
        if progress >= 1.0:
            return Stage.CODE_GENERATION
        elif progress >= 0.8:
            return Stage.GATHERING_REQUIREMENTS  # Still gathering but close
        else:
            return Stage.GATHERING_REQUIREMENTS
    
    def _convert_assistant_to_context_response(
        self, 
        assistant_response: Dict[str, Any], 
        session_id: str,
        stage: Stage
    ) -> ContextUpdateResponse:
        """Convert assistant response to ContextUpdateResponse."""
        
        updated_context = assistant_response.get("updated_context", {})
        
        return ContextUpdateResponse(
            updated_context=ProjectContext(
                device_constants=updated_context.get("device_constants", {}),
                information=updated_context.get("information", "")
            ),
            chat_message=assistant_response.get("chat_message", ""),
            is_mcq=assistant_response.get("is_mcq", False),
            mcq_question=assistant_response.get("mcq_question"),
            mcq_options=assistant_response.get("mcq_options", []),
            is_multiselect=assistant_response.get("is_multiselect", False),
            generated_code=assistant_response.get("generated_code"),
            current_stage=stage,
            gathering_requirements_estimated_progress=assistant_response.get(
                "gathering_requirements_estimated_progress", 0.0
            )
        )
    
    def _create_error_response(
        self, 
        error_message: str, 
        request: ContextUpdateRequest
    ) -> ContextUpdateResponse:
        """Create error response."""
        
        return ContextUpdateResponse(
            updated_context=request.current_context or ProjectContext(
                device_constants={},
                information=f"Error: {error_message}"
            ),
            chat_message="I apologize, but I encountered an error processing your request. Please try again.",
            is_mcq=False,
            mcq_question=None,
            mcq_options=[],
            is_multiselect=False,
            generated_code=None,
            current_stage=Stage.GATHERING_REQUIREMENTS,
            gathering_requirements_estimated_progress=0.0
        )
    
    def cleanup_session(self, session_id: str) -> None:
        """Clean up vector store files for session."""
        if session_id in self._active_sessions:
            # Clean up vector store files
            asyncio.create_task(self.vector_store_service.cleanup_session_files(session_id))
            del self._active_sessions[session_id]
            logger.info(f"Cleaned up session: {session_id}")

# Import asyncio for cleanup task
import asyncio
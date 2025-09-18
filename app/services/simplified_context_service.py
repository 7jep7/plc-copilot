"""
Simplified Context Service using OpenAI Assistant with Vector Store integration.

This service handles the three core interaction cases:
1. Project kickoff (no context, no file) → start gathering info
2. Context update (context exists, no file) → update with assistant
3. File upload (file + optional context) → upload to vector store → assistant call

Uses the AssistantService and VectorStoreService for streamlined processing.
The assistant automatically accesses files from the configured vector store.
"""

import uuid
import random
import logging
import asyncio
import time
from typing import Dict, List, Optional, Any
from io import BytesIO

from app.schemas.context import (
    ProjectContext, ContextUpdateRequest, ContextUpdateResponse, Stage
)
from app.services.assistant_service import AssistantService
from app.services.vector_store_service import VectorStoreService
from app.core.config import settings

logger = logging.getLogger(__name__)


class SimplifiedContextService:
    """Simplified context service using OpenAI Assistant API with Vector Store."""
    
    def __init__(self):
        self.assistant_service = AssistantService()
        self.vector_store_service = VectorStoreService()
        self._active_sessions: Dict[str, List[str]] = {}  # Track uploaded file IDs per session
        self._session_timestamps: Dict[str, float] = {}  # Track last access time per session
        self._session_timeout_minutes = 30  # Session timeout in minutes
    
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
            
            # Update session timestamp
            self._session_timestamps[session_id] = time.time()
            
            # Clean up expired sessions periodically
            await self._cleanup_expired_sessions()
            
            # Determine which case we're handling
            has_context = bool(
                request.current_context and 
                (request.current_context.device_constants or request.current_context.information)
            )
            has_files = bool(uploaded_files)
            has_mcq_responses = bool(request.mcq_responses)
            
            # If we have MCQ responses, treat as context update (user made progress)
            if has_mcq_responses:
                has_context = True
            
            logger.info(f"Processing context update: has_context={has_context}, has_files={has_files}, has_mcq_responses={has_mcq_responses}, stage={request.current_stage}, session_id={session_id}")
            
            if has_files:
                # Case 3: File upload with optional context
                return await self._handle_file_upload_case(
                    request, uploaded_files, session_id
                )
            elif has_context:
                # Case 2: Context exists, update with assistant (includes MCQ responses)
                return await self._handle_context_update_case(request, session_id)
            else:
                # Case 1: Project kickoff
                return await self._handle_project_kickoff_case(request, session_id)
                
        except Exception as e:
            logger.error(f"Error processing context update: {e}")
            return self._create_error_response(str(e), request, session_id or "error-session")
    
    async def _handle_project_kickoff_case(
        self, 
        request: ContextUpdateRequest, 
        session_id: str
    ) -> ContextUpdateResponse:
        """Handle Case 1: Project kickoff with no context or files."""
        
        logger.info("Handling project kickoff case")
        
        # Check if this is an off-topic start (but MCQ responses are always considered on-topic)
        user_message = request.message or ""
        has_mcq_response = bool(request.mcq_responses)
        
        if not has_mcq_response and not self._is_plc_related(user_message):
            # Offer sample projects via MCQ
            return self._create_sample_projects_response(session_id)
        
        # Build message with MCQ responses if available
        complete_message = self._build_user_message_with_mcq(request)
        
        # Start gathering requirements with assistant
        assistant_response = await self.assistant_service.process_message(
            user_message=complete_message,
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
            "vector_store_id": settings.OPENAI_VECTOR_STORE_ID
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
            # Core PLC terms
            "plc", "programmable logic", "structured text", "ladder logic",
            "automation", "industrial automation", "industrial control", "control system",
            "scada", "hmi", "process control", "safety interlock", "safety system",
            "motor control", "sensor", "actuator", "conveyor", "interlock", 
            "tag", "variable", "function block",
            
            # Manufacturing & Production
            "assembly line", "manufacturing", "factory automation", "production line",
            "robotic", "packaging line", "rfid tracking", "manufacturing process",
            "machine tool", "cnc", "metal cutting", "welding line", 
            "injection molding", "steel mill", "rolling process",
            
            # Building & Infrastructure Systems
            "hvac", "building management", "warehouse automation", "storage system", 
            "automated storage", "power distribution", "load management", 
            "elevator control", "baggage handling system",
            
            # Energy & Utilities
            "solar panel tracking", "solar panel control", "wind turbine control", 
            "power plant", "energy management system", "water treatment", 
            "pump station", "boiler control", "steam management",
            
            # Specialized Industries
            "semiconductor", "cleanroom management", "hospital system", 
            "patient bed management", "airport system", "baggage handling",
            "fish farm", "water quality management", "pharmaceutical",
            "food processing", "chemical reactor", "process safety",
            
            # General Industrial Terms (more specific)
            "management system", "environmental control system", "climate control system",
            "temperature control", "pressure control", "monitoring system",
            "distribution system", "crane control", "hoist control", "textile loom",
            "brewery fermentation", "mining conveyor", "paper mill", "automotive paint",
            "glass manufacturing", "oil refinery", "greenhouse control", 
            "irrigation system", "equipment monitoring", "factory equipment",
            
            # Additional essential terms
            "automate my factory", "factory", "plant", "industrial equipment"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in plc_keywords)
    
    def _create_sample_projects_response(self, session_id: str) -> ContextUpdateResponse:
        """Create response with sample project options (randomly selected from 40 projects)."""
        
        # Comprehensive list of 40 sample PLC projects
        all_sample_projects = [
            "Conveyor Belt Control System with Safety Interlocks",
            "Motor Speed Control with VFD Integration",
            "Process Control with PID Temperature Regulation",
            "Automated Packaging Line with RFID Tracking",
            "Water Treatment Plant Control System",
            "Assembly Line Robot Integration",
            "HVAC Building Management System",
            "Batch Mixing Process Control",
            "Parking Garage Access Control",
            "Traffic Light Control System",
            "Warehouse Automated Storage and Retrieval",
            "Chemical Reactor Temperature and Pressure Control",
            "Elevator Control System with Safety Features",
            "Food Processing Line with Quality Control",
            "Solar Panel Tracking System",
            "Pump Station Control with Redundancy",
            "Machine Tool CNC Integration",
            "Power Distribution and Load Management",
            "Irrigation System with Soil Moisture Sensors",
            "Pharmaceutical Tablet Press Control",
            "Paint Booth Ventilation and Safety System",
            "Boiler Control with Steam Management",
            "Crane and Hoist Safety Control",
            "Textile Loom Automation",
            "Metal Cutting and Welding Line",
            "Brewery Fermentation Process Control",
            "Wind Turbine Control and Monitoring",
            "Mining Conveyor and Crusher Control",
            "Paper Mill Process Automation",
            "Automotive Paint Line Control",
            "Glass Manufacturing Temperature Control",
            "Oil Refinery Process Safety System",
            "Airport Baggage Handling System",
            "Hospital Patient Bed Management",
            "Data Center Environmental Control",
            "Greenhouse Climate Control System",
            "Fish Farm Water Quality Management",
            "Plastic Injection Molding Control",
            "Steel Mill Rolling Process Control",
            "Semiconductor Cleanroom Management"
        ]
        
        # Randomly select 3 projects
        selected_projects = random.sample(all_sample_projects, 3)
        
        return ContextUpdateResponse(
            updated_context=ProjectContext(
                device_constants={},
                information=""
            ),
            chat_message="I'd be happy to help you with PLC programming! Here are some sample projects to get started:",
            session_id=session_id,
            is_mcq=True,
            mcq_question="Which type of project would you like to work on?",
            mcq_options=selected_projects,
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
            session_id=session_id,
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
        request: ContextUpdateRequest,
        session_id: str
    ) -> ContextUpdateResponse:
        """Create error response."""
        
        return ContextUpdateResponse(
            updated_context=request.current_context or ProjectContext(
                device_constants={},
                information=f"Error: {error_message}"
            ),
            chat_message="I apologize, but I encountered an error processing your request. Please try again.",
            session_id=session_id,
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
            if session_id in self._session_timestamps:
                del self._session_timestamps[session_id]
            logger.info(f"Cleaned up session: {session_id}")

    async def cleanup_session_async(self, session_id: str) -> Dict[str, Any]:
        """Async cleanup of session with detailed results."""
        result = {"files_cleaned": 0, "success": True}
        
        try:
            if session_id in self._active_sessions:
                file_count = len(self._active_sessions[session_id])
                
                # Clean up vector store files
                await self.vector_store_service.cleanup_session_files(session_id)
                
                # Remove from tracking
                del self._active_sessions[session_id]
                if session_id in self._session_timestamps:
                    del self._session_timestamps[session_id]
                
                result["files_cleaned"] = file_count
                logger.info(f"Cleaned up session {session_id}: {file_count} files removed")
            else:
                logger.info(f"Session {session_id} not found or already cleaned up")
                
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
            result["success"] = False
            result["error"] = str(e)
        
        return result

    async def _cleanup_expired_sessions(self) -> None:
        """Clean up sessions that have expired based on timeout."""
        try:
            current_time = time.time()
            timeout_seconds = self._session_timeout_minutes * 60
            expired_sessions = []
            
            for session_id, last_access in self._session_timestamps.items():
                if current_time - last_access > timeout_seconds:
                    expired_sessions.append(session_id)
            
            if expired_sessions:
                logger.info(f"Cleaning up {len(expired_sessions)} expired sessions")
                for session_id in expired_sessions:
                    await self.cleanup_session_async(session_id)
                    
        except Exception as e:
            logger.error(f"Error during expired session cleanup: {e}")

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions."""
        current_time = time.time()
        active_count = len(self._active_sessions)
        total_files = sum(len(files) for files in self._active_sessions.values())
        
        # Calculate session ages
        session_ages = []
        for session_id, timestamp in self._session_timestamps.items():
            age_minutes = (current_time - timestamp) / 60
            session_ages.append(age_minutes)
        
        return {
            "active_sessions": active_count,
            "total_files_tracked": total_files,
            "avg_session_age_minutes": sum(session_ages) / len(session_ages) if session_ages else 0,
            "oldest_session_age_minutes": max(session_ages) if session_ages else 0,
            "timeout_minutes": self._session_timeout_minutes
        }

# Import asyncio for cleanup task
import asyncio
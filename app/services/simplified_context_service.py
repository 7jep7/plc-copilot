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
        
        # Check if this is an off-topic start 
        # Only consider off-topic if: no files AND (single word OR common greeting)
        # MCQ responses are always considered on-topic
        user_message = request.message or ""
        has_mcq_response = bool(request.mcq_responses)
        has_files = bool(request.files and len(request.files) > 0)
        
        if not has_mcq_response and not has_files and not self._is_plc_related(user_message):
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
        
        file_metadata = []
        file_ids = []
        
        # Only upload to vector store if enabled
        if settings.USE_VECTOR_STORE:
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
        
        # If vector store is disabled, pass summarized file content directly
        if not settings.USE_VECTOR_STORE and uploaded_files:
            # Extract key specifications from file content instead of passing entire document
            extracted_specs = await self._extract_key_specifications_from_files(uploaded_files, filenames)
            if extracted_specs:
                user_message = f"Based on the following device specifications, extract device constants and technical details:\n\n{extracted_specs}\n\nUser request: {user_message}"
            file_ids = None
        # Process with assistant
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

    async def _extract_key_specifications_from_files(self, uploaded_files: List[BytesIO], filenames: List[str]) -> str:
        """Extract comprehensive technical specifications from uploaded files while staying below token limits."""
        try:
            # Import PDF extractor
            from app.services.pdf_extractor import PDFTextExtractor
            from pathlib import Path
            
            pdf_extractor = PDFTextExtractor()
            all_text = ""
            
            # Extract text from each file
            for file_content, filename in zip(uploaded_files, filenames):
                file_extension = Path(filename).suffix.lower()
                
                if file_extension == '.pdf' and pdf_extractor:
                    # Extract text using the same method as vector store service
                    file_content.seek(0)
                    try:
                        extracted_data = pdf_extractor.extract_text_from_pdf(file_content, filename)
                        if extracted_data and extracted_data.get('text'):
                            all_text += extracted_data['text'] + "\n\n"
                        else:
                            logger.warning(f"No text extracted from PDF {filename}")
                    except Exception as e:
                        logger.error(f"PDF extraction failed for {filename}: {e}")
                else:
                    # Handle text files
                    file_content.seek(0)
                    content = file_content.read().decode('utf-8', errors='replace')
                    all_text += content + "\n\n"
            
            if not all_text.strip():
                return ""
            
            # Extract comprehensive technical sections using smart patterns
            import re
            
            # Categorized patterns for better organization
            device_patterns = {
                'Basic Info': {
                    'Model': r'(?i)model\s*[:\-]?\s*([A-Z0-9\-\.]+)',
                    'Series': r'(?i)(?:series|family)[:\-]?\s*([A-Z0-9\-\s]+)',
                    'Type': r'(?i)(?:controller|plc|device)\s+type[:\-]?\s*([^;\n]+)',
                },
                'Power & Environment': {
                    'Power Voltage': r'(?i)power\s+voltage[:\-]?\s*([^;\n]+)',
                    'Current Consumption': r'(?i)current\s+consumption[:\-]?\s*([^;\n]+)',
                    'Operating Temperature': r'(?i)operating\s+(?:ambient\s+)?temperature[:\-]?\s*([^;\n]+)',
                    'Operating Humidity': r'(?i)operating\s+(?:ambient\s+)?humidity[:\-]?\s*([^;\n]+)',
                    'Storage Temperature': r'(?i)storage\s+(?:ambient\s+)?temperature[:\-]?\s*([^;\n]+)',
                },
                'Performance': {
                    'CPU Memory': r'(?i)cpu\s+memory\s*(?:capacity)?[:\-]?\s*([^;\n]+)',
                    'Program Capacity': r'(?i)program\s+capacity[:\-]?\s*([^;\n]+)',
                    'Instruction Speed': r'(?i)instruction\s+execution\s+speed[:\-]?\s*([^;\n]+)',
                    'Processing Mode': r'(?i)(?:arithmetic\s+)?control\s+mode[:\-]?\s*([^;\n]+)',
                },
                'I/O & Communication': {
                    'Max I/O Points': r'(?i)maximum.*i/?o\s+points[:\-]?\s*([^;\n]+)',
                    'Max Units': r'(?i)maximum\s+number\s+of\s+units[:\-]?\s*([^;\n]+)',
                    'Communication': r'(?i)communication[:\-]?\s*([^;\n]+)',
                },
                'Programming': {
                    'Programming Language': r'(?i)program(?:ming)?\s+language[:\-]?\s*([^;\n]+)',
                    'Instructions': r'(?i)(?:number\s+of\s+)?(?:basic\s+)?instructions[:\-]?\s*([^;\n]+)',
                    'Commands': r'(?i)(?:number\s+of\s+)?commands[:\-]?\s*([^;\n]+)',
                },
                'Physical': {
                    'Weight': r'(?i)weight[:\-]?\s*([^;\n]+)',
                    'Dimensions': r'(?i)dimensions?[:\-]?\s*([^;\n]+)',
                    'Mounting': r'(?i)mounting[:\-]?\s*([^;\n]+)',
                }
            }
            
            extracted_info = {}
            
            # Extract specifications by category
            for category, patterns in device_patterns.items():
                category_specs = {}
                for spec_name, pattern in patterns.items():
                    matches = re.findall(pattern, all_text, re.MULTILINE | re.DOTALL)
                    if matches:
                        # Clean up the matched text
                        clean_match = matches[0].strip()
                        # Remove excessive whitespace and limit length per field
                        clean_match = re.sub(r'\s+', ' ', clean_match)[:300]
                        if clean_match and len(clean_match) > 3:  # Avoid very short matches
                            category_specs[spec_name] = clean_match
                
                if category_specs:
                    extracted_info[category] = category_specs
            
            # Also extract any tables or structured data sections
            table_patterns = [
                r'(?i)specifications?\s*:?\s*\n((?:[^\n]*\n){1,15})',
                r'(?i)technical\s+data\s*:?\s*\n((?:[^\n]*\n){1,15})',
                r'(?i)performance\s+specifications?\s*:?\s*\n((?:[^\n]*\n){1,15})',
            ]
            
            for pattern in table_patterns:
                matches = re.findall(pattern, all_text, re.MULTILINE | re.DOTALL)
                if matches:
                    table_content = matches[0].strip()[:500]  # Limit table content
                    if 'Tables/Data' not in extracted_info:
                        extracted_info['Tables/Data'] = {}
                    extracted_info['Tables/Data'][f'Table_{len(extracted_info["Tables/Data"])+1}'] = table_content
            
            # Format the comprehensive output
            if extracted_info:
                output_lines = []
                total_chars = 0
                max_chars = 8000  # Stay well below token limit (~2000 tokens)
                
                for category, specs in extracted_info.items():
                    category_section = f"\n## {category}:\n"
                    if total_chars + len(category_section) > max_chars:
                        break
                    output_lines.append(category_section)
                    total_chars += len(category_section)
                    
                    for spec_name, value in specs.items():
                        spec_line = f"- {spec_name}: {value}\n"
                        if total_chars + len(spec_line) > max_chars:
                            break
                        output_lines.append(spec_line)
                        total_chars += len(spec_line)
                
                result = "# Device Technical Specifications\n" + "".join(output_lines)
                logger.info(f"Extracted {total_chars} characters of technical specifications")
                return result
            
            # Fallback: extract key sections of original text
            sections = all_text.split('\n\n')
            important_sections = []
            total_chars = 0
            max_chars = 6000
            
            for section in sections:
                if any(keyword in section.lower() for keyword in 
                      ['specification', 'performance', 'technical', 'model', 'memory', 'voltage', 'temperature']):
                    if total_chars + len(section) < max_chars:
                        important_sections.append(section.strip())
                        total_chars += len(section)
            
            if important_sections:
                return "# Device Information\n\n" + "\n\n".join(important_sections)
            
            # Last resort: first portion of text
            return f"# Device Information\n\n{all_text[:4000]}..."
            
        except Exception as e:
            logger.error(f"Error extracting specifications: {e}")
            return "Unable to extract device specifications from uploaded files."

    def _is_plc_related(self, message: str) -> bool:
        """
        Check if the message should be considered off-topic.
        
        Returns False (off-topic) only if the message is:
        1) A single word, OR
        2) A common greeting/small talk phrase
        
        This makes the filter very restrictive - almost all messages are considered on-topic
        unless they're clearly just greetings or single words.
        """
        message_stripped = message.strip()
        message_lower = message_stripped.lower()
        
        # Check if it's a single word (no spaces)
        if ' ' not in message_stripped and len(message_stripped) > 0:
            return False  # Single word = off-topic
        
        # Common greeting/small talk phrases that should be considered off-topic
        off_topic_phrases = [
            "how are you",
            "how are you?",
            "how is it going",
            "how is it going?",
            "what's up",
            "what's up?",
            "whats up",
            "whats up?",
            "how's it going",
            "how's it going?",
            "hows it going",
            "hows it going?",
            "good morning",
            "good afternoon", 
            "good evening",
            "good night",
            "hello there",
            "hi there",
            "hey there",
            "how do you do",
            "how do you do?",
            "nice to meet you",
            "pleased to meet you",
            "how have you been",
            "how have you been?",
            "long time no see",
            "what's new",
            "what's new?",
            "whats new",
            "whats new?",
            "how's everything",
            "how's everything?",
            "hows everything",
            "hows everything?",
            "how are things",
            "how are things?",
            ".",
            "?",
            "!",
            "...",
            "test",
            "testing",
        ]
        
        # Check if the message exactly matches any off-topic phrase
        if message_lower in off_topic_phrases:
            return False  # Common greeting/small talk = off-topic
        
        # Everything else is considered on-topic (PLC-related)
        return True
    
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
        
        # Clean the assistant response to remove any problematic field names
        cleaned_response = self._clean_response_data(assistant_response)
        updated_context = cleaned_response.get("updated_context", {})
        
        return ContextUpdateResponse(
            updated_context=ProjectContext(
                device_constants=updated_context.get("device_constants", {}),
                information=updated_context.get("information", "")
            ),
            chat_message=cleaned_response.get("chat_message", ""),
            session_id=session_id,
            is_mcq=cleaned_response.get("is_mcq", False),
            mcq_question=cleaned_response.get("mcq_question"),
            mcq_options=cleaned_response.get("mcq_options", []),
            is_multiselect=cleaned_response.get("is_multiselect", False),
            generated_code=cleaned_response.get("generated_code"),
            current_stage=stage,
            gathering_requirements_estimated_progress=cleaned_response.get(
                "gathering_requirements_estimated_progress", 0.0
            )
        )

    def _clean_response_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean response data to remove field names with leading underscores that Pydantic v2 doesn't allow."""
        if not isinstance(data, dict):
            return data
        
        cleaned = {}
        for key, value in data.items():
            # Skip fields that start with double underscores
            if key.startswith('__'):
                logger.warning(f"Skipping field with leading underscores: {key}")
                continue
            
            # Recursively clean nested dictionaries
            if isinstance(value, dict):
                cleaned[key] = self._clean_response_data(value)
            elif isinstance(value, list):
                cleaned[key] = [self._clean_response_data(item) if isinstance(item, dict) else item for item in value]
            else:
                cleaned[key] = value
        
        return cleaned
    
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
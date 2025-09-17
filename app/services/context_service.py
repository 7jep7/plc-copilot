"""
Context processing service for the unified context-centric API.

This service handles:
- Context updates and integration
- AI-driven progress calculation 
- File processing and extraction
- Context compression and optimization
- Stage-aware prompting and responses
- Structured Text generation
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from io import BytesIO

# PDF processing imports
try:
    import PyPDF2
    import pdfplumber
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from app.core.config import settings
from app.schemas.context import (
    ProjectContext, 
    ContextUpdateRequest, 
    ContextUpdateResponse,
    FileProcessingResult,
    Stage
)
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class ContextProcessingService:
    """Service for processing context updates and managing project state."""
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    async def process_context_update(
        self, 
        request: ContextUpdateRequest,
        uploaded_files: Optional[List[BytesIO]] = None
    ) -> ContextUpdateResponse:
        """
        Process a context update request with message, MCQ responses, and files.
        
        Args:
            request: Context update request with message, context, stage
            uploaded_files: Optional list of uploaded files to process
            
        Returns:
            Complete context update response with updated context, AI message, and UI state
        """
        logger.info(f"Processing context update for stage: {request.current_stage}")
        
        # Start with current context
        updated_context = request.current_context.model_copy(deep=True)
        
        # Process uploaded files first if any
        file_extractions = []
        if uploaded_files:
            for file_data in uploaded_files:
                extraction = await self._process_uploaded_file(file_data)
                file_extractions.append(extraction)
                
                # Integrate file extractions into context
                updated_context = self._integrate_file_extraction(updated_context, extraction)
        
        # Update context with user message and MCQ responses
        if request.message or request.mcq_responses:
            updated_context = await self._update_context_with_user_input(
                updated_context, 
                request.message, 
                request.mcq_responses
            )
        
        # Generate AI response based on stage
        if request.current_stage == Stage.CODE_GENERATION:
            return await self._handle_code_generation(updated_context, request.current_stage)
        elif request.current_stage == Stage.REFINEMENT_TESTING:
            return await self._handle_refinement_testing(updated_context, request)
        else:  # GATHERING_REQUIREMENTS
            return await self._handle_requirements_gathering(updated_context, request)
    
    async def _process_uploaded_file(self, file_data: BytesIO) -> FileProcessingResult:
        """
        Process an uploaded file and extract PLC-relevant information.
        
        Args:
            file_data: File data as BytesIO
            
        Returns:
            Extracted device specifications and information
        """
        logger.info("Processing uploaded file for PLC-relevant data")
        
        try:
            # Extract text from file using document service
            # Create a temporary document service instance without DB dependency
            file_bytes = file_data.getvalue()
            
            # Use direct extraction methods
            extracted_text = self._extract_text_from_bytes(file_bytes)
            
            # Use AI to extract structured device information
            extraction_prompt = self._build_file_extraction_prompt(extracted_text)
            
            response = await self.openai_service.chat_completion(
                messages=[{"role": "user", "content": extraction_prompt}],
                model="gpt-4o-mini",
                temperature=0.3,
                max_completion_tokens=1024
            )
            
            # Parse AI response into structured format
            try:
                extracted_data = json.loads(response.content)
                return FileProcessingResult(
                    extracted_devices=extracted_data.get("devices", {}),
                    extracted_information=extracted_data.get("information", ""),
                    processing_summary=extracted_data.get("summary", "Processed file successfully")
                )
            except json.JSONDecodeError:
                # Fallback if AI doesn't return valid JSON
                return FileProcessingResult(
                    extracted_devices={},
                    extracted_information=response.content[:500],  # Truncate for brevity
                    processing_summary="Extracted general information from file"
                )
                
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            return FileProcessingResult(
                extracted_devices={},
                extracted_information="",
                processing_summary=f"Error processing file: {str(e)}"
            )
    
    def _integrate_file_extraction(
        self, 
        context: ProjectContext, 
        extraction: FileProcessingResult
    ) -> ProjectContext:
        """
        Integrate file extraction results into project context.
        
        Args:
            context: Current project context
            extraction: File processing results
            
        Returns:
            Updated context with file data integrated
        """
        # Merge extracted devices into device_constants
        updated_devices = context.device_constants.copy()
        for device_name, device_data in extraction.extracted_devices.items():
            if device_name in updated_devices:
                # Merge existing device data
                if isinstance(updated_devices[device_name], dict) and isinstance(device_data, dict):
                    updated_devices[device_name].update(device_data)
                else:
                    updated_devices[device_name] = device_data
            else:
                updated_devices[device_name] = device_data
        
        # Append extracted information to context information
        updated_info = context.information
        if extraction.extracted_information.strip():
            if updated_info.strip():
                updated_info += f"\n\n## File Upload: {extraction.processing_summary}\n{extraction.extracted_information}"
            else:
                updated_info = f"## File Upload: {extraction.processing_summary}\n{extraction.extracted_information}"
        
        return ProjectContext(
            device_constants=updated_devices,
            information=updated_info
        )
    
    async def _update_context_with_user_input(
        self,
        context: ProjectContext,
        message: Optional[str],
        mcq_responses: List[str]
    ) -> ProjectContext:
        """
        Update context with user message and MCQ responses using AI.
        
        Args:
            context: Current project context
            message: User message
            mcq_responses: Selected MCQ options
            
        Returns:
            Updated context with user input integrated
        """
        if not message and not mcq_responses:
            return context
        
        # Build prompt to update context
        update_prompt = self._build_context_update_prompt(context, message, mcq_responses)
        
        response = await self.openai_service.chat_completion(
            messages=[{"role": "user", "content": update_prompt}],
            model="gpt-4o-mini", 
            temperature=0.3,
            max_completion_tokens=1024
        )
        
        try:
            updated_data = json.loads(response.content)
            return ProjectContext(
                device_constants=updated_data.get("device_constants", context.device_constants),
                information=updated_data.get("information", context.information)
            )
        except json.JSONDecodeError:
            logger.warning("AI didn't return valid JSON for context update, keeping original context")
            return context
    
    async def _handle_requirements_gathering(
        self,
        context: ProjectContext,
        request: ContextUpdateRequest
    ) -> ContextUpdateResponse:
        """
        Handle requirements gathering stage with progress calculation and MCQ generation.
        
        Args:
            context: Updated project context
            request: Original request for stage context
            
        Returns:
            Response with progress, MCQ, or transition suggestion
        """
        # Calculate progress based on context completeness
        progress = self._calculate_requirements_progress(context)
        
        # Generate next question or MCQ
        question_prompt = self._build_requirements_question_prompt(context, progress)
        
        response = await self.openai_service.chat_completion(
            messages=[{"role": "user", "content": question_prompt}],
            model="gpt-4o-mini",
            temperature=0.7,
            max_completion_tokens=512
        )
        
        # Parse AI response for MCQ or regular question
        try:
            ai_response = json.loads(response.content)
            return ContextUpdateResponse(
                updated_context=context,
                chat_message=ai_response.get("message", response.content),
                gathering_requirements_progress=progress,
                current_stage=Stage.GATHERING_REQUIREMENTS,
                is_mcq=ai_response.get("is_mcq", False),
                is_multiselect=ai_response.get("is_multiselect", False),
                mcq_question=ai_response.get("mcq_question"),
                mcq_options=ai_response.get("mcq_options", [])
            )
        except json.JSONDecodeError:
            # Fallback to regular message
            return ContextUpdateResponse(
                updated_context=context,
                chat_message=response.content,
                gathering_requirements_progress=progress,
                current_stage=Stage.GATHERING_REQUIREMENTS,
                is_mcq=False,
                is_multiselect=False,
                mcq_question=None,
                mcq_options=[]
            )
    
    async def _handle_code_generation(
        self,
        context: ProjectContext,
        current_stage: Stage
    ) -> ContextUpdateResponse:
        """
        Handle code generation stage - generate Structured Text.
        
        Args:
            context: Project context with requirements
            current_stage: Current stage (should be CODE_GENERATION)
            
        Returns:
            Response with generated Structured Text code
        """
        # Generate Structured Text based on context
        code_prompt = self._build_code_generation_prompt(context)
        
        response = await self.openai_service.chat_completion(
            messages=[{"role": "user", "content": code_prompt}],
            model="gpt-4o",  # Use more powerful model for code generation
            temperature=0.3,
            max_completion_tokens=2048
        )
        
        return ContextUpdateResponse(
            updated_context=context,
            chat_message="I've generated the Structured Text code based on your requirements. You can now review and refine it.",
            gathering_requirements_progress=None,
            current_stage=Stage.REFINEMENT_TESTING,  # Auto-transition to refinement
            is_mcq=False,
            is_multiselect=False,
            mcq_question=None,
            mcq_options=[],
            generated_code=response.content
        )
    
    async def _handle_refinement_testing(
        self,
        context: ProjectContext,
        request: ContextUpdateRequest
    ) -> ContextUpdateResponse:
        """
        Handle refinement and testing stage.
        
        Args:
            context: Project context
            request: Original request
            
        Returns:
            Response for refinement interactions
        """
        # Generate refinement response based on user input
        refinement_prompt = self._build_refinement_prompt(context, request.message)
        
        response = await self.openai_service.chat_completion(
            messages=[{"role": "user", "content": refinement_prompt}],
            model="gpt-4o-mini",
            temperature=0.7,
            max_completion_tokens=512
        )
        
        # Check if response should be MCQ
        try:
            ai_response = json.loads(response.content)
            return ContextUpdateResponse(
                updated_context=context,
                chat_message=ai_response.get("message", response.content),
                gathering_requirements_progress=None,
                current_stage=Stage.REFINEMENT_TESTING,
                is_mcq=ai_response.get("is_mcq", False),
                is_multiselect=ai_response.get("is_multiselect", False),
                mcq_question=ai_response.get("mcq_question"),
                mcq_options=ai_response.get("mcq_options", [])
            )
        except json.JSONDecodeError:
            return ContextUpdateResponse(
                updated_context=context,
                chat_message=response.content,
                gathering_requirements_progress=None,
                current_stage=Stage.REFINEMENT_TESTING,
                is_mcq=False,
                is_multiselect=False,
                mcq_question=None,
                mcq_options=[]
            )
    
    def _calculate_requirements_progress(self, context: ProjectContext) -> float:
        """
        Calculate requirements gathering progress based on context completeness.
        
        Args:
            context: Current project context
            
        Returns:
            Progress value between 0.0 and 1.0
        """
        # Essential elements for PLC code generation
        essential_items = [
            "device_constants",  # Has some device specifications
            "safety_requirements",  # Safety info in information or devices
            "io_specifications",  # I/O information
            "basic_sequence",  # Some process description
            "control_logic"  # Basic control requirements
        ]
        
        score = 0.0
        total_items = len(essential_items)
        
        # Check device_constants existence and depth
        if context.device_constants:
            score += 0.3  # Base score for having any devices
            # Bonus for nested structure complexity
            total_keys = len(self._flatten_dict(context.device_constants).keys())
            if total_keys > 5:
                score += 0.2
        
        # Check information content for key terms
        info_lower = context.information.lower()
        
        # Safety requirements
        if any(term in info_lower for term in ["safety", "emergency", "stop", "protection"]):
            score += 0.15
        
        # I/O specifications  
        if any(term in info_lower for term in ["input", "output", "sensor", "actuator", "i/o"]):
            score += 0.15
        
        # Process/sequence information
        if any(term in info_lower for term in ["sequence", "process", "step", "operation", "control"]):
            score += 0.1
        
        # Control logic details
        if any(term in info_lower for term in ["logic", "program", "algorithm", "function"]):
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_text_from_bytes(self, file_bytes: bytes) -> str:
        """
        Extract text from PDF file bytes.
        
        Args:
            file_bytes: PDF file content as bytes
            
        Returns:
            Extracted text content
        """
        if not PDF_AVAILABLE:
            return "PDF processing libraries not available"
        
        text_content = []
        
        try:
            # Method 1: pdfplumber
            with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
        except Exception as e:
            logger.warning(f"pdfplumber extraction from bytes failed: {e}")
        
        if not text_content:
            try:
                # Method 2: PyMuPDF
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page_num in range(doc.page_count):
                    page = doc[page_num]
                    text = page.get_text()
                    if text:
                        text_content.append(text)
                doc.close()
            except Exception as e:
                logger.warning(f"PyMuPDF extraction from bytes failed: {e}")
        
        if not text_content:
            try:
                # Method 3: PyPDF2
                pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            except Exception as e:
                logger.warning(f"PyPDF2 extraction from bytes failed: {e}")
        
        return "\n\n".join(text_content)
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '') -> Dict[str, Any]:
        """Flatten nested dictionary to count total keys."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _build_file_extraction_prompt(self, file_content: str) -> str:
        """Build prompt for extracting PLC-relevant data from files."""
        # Truncate content to avoid token limits
        max_content = 6000  # Keep well under token limits
        if len(file_content) > max_content:
            file_content = file_content[:max_content] + "...[truncated]"
        
        return f"""
Extract PLC-relevant device specifications and information from this document.

CRITICAL: Be extremely selective and concise. Only extract information directly relevant to PLC programming.

Document content:
{file_content}

Return a JSON object with this exact structure:
{{
    "devices": {{
        "DeviceName": {{
            "Type": "device type",
            "Model": "model number", 
            "Specifications": {{
                "key": "value"
            }}
        }}
    }},
    "information": "Brief markdown summary of PLC-relevant requirements and specifications",
    "summary": "One sentence describing what was extracted"
}}

Focus on:
- Device specifications (motors, sensors, PLCs, I/O modules)
- Electrical specifications (voltage, current, power)
- I/O requirements and configurations
- Safety requirements
- Control sequences and timing
- Communication protocols

Ignore:
- General documentation
- Installation procedures
- Non-technical content
- Marketing information
"""
    
    def _build_context_update_prompt(
        self, 
        context: ProjectContext, 
        message: Optional[str], 
        mcq_responses: List[str]
    ) -> str:
        """Build prompt for updating context with user input."""
        return f"""
Update the project context based on user input. Be extremely concise and only include essential PLC-relevant information.

Current context:
Device Constants: {json.dumps(context.device_constants, indent=2)}
Information: {context.information}

User input:
Message: {message or "None"}
MCQ Responses: {mcq_responses or "None"}

Return updated context in this exact JSON format:
{{
    "device_constants": {{
        // Updated nested JSON with device specs - keep concise
    }},
    "information": "Updated markdown summary - be very brief, only essential info"
}}

CRITICAL RULES:
- Only keep information directly relevant to PLC code generation
- Be extremely concise in information field
- Avoid redundancy and unnecessary details
- Focus on technical specifications and requirements
"""
    
    def _build_requirements_question_prompt(self, context: ProjectContext, progress: float) -> str:
        """Build prompt for generating next requirements question."""
        return f"""
You are a PLC programming expert gathering requirements. Current progress: {progress:.1%}

Current context:
Device Constants: {json.dumps(context.device_constants, indent=2)}
Information: {context.information}

Based on the context, generate the next focused question to gather essential PLC programming requirements.

Return JSON in this exact format:
{{
    "message": "Your question or response",
    "is_mcq": false,
    "mcq_question": null,
    "mcq_options": [],
    "is_multiselect": false
}}

OR for multiple choice questions:
{{
    "message": "Brief intro if needed",
    "is_mcq": true, 
    "mcq_question": "Clear, specific question",
    "mcq_options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "is_multiselect": false
}}

PRIORITIES (ask about missing items first):
1. Safety requirements (emergency stops, protection)
2. I/O specifications (inputs, outputs, sensors, actuators)
3. Control sequence basics
4. PLC platform/hardware
5. Communication requirements

Ask ONE focused question. Use MCQ for standardized choices (safety features, voltage levels, protocols, etc.).
"""
    
    def _build_code_generation_prompt(self, context: ProjectContext) -> str:
        """Build prompt for generating Structured Text code."""
        return f"""
Generate complete Structured Text (ST) code for this PLC automation project.

Project Context:
Device Constants: {json.dumps(context.device_constants, indent=2)}
Requirements: {context.information}

Generate production-ready Structured Text including:
- Variable declarations (inputs, outputs, internal variables)
- Function blocks and programs
- Main control logic
- Safety interlocks
- Error handling
- Clear comments

Structure the code with:
1. TYPE declarations (if needed)
2. PROGRAM declaration
3. VAR sections (inputs, outputs, internal)
4. Main control logic
5. Safety and error handling

Make the code complete, compilable, and well-documented.
"""
    
    def _build_refinement_prompt(self, context: ProjectContext, user_message: Optional[str]) -> str:
        """Build prompt for refinement stage responses."""
        return f"""
You are in the refinement/testing stage helping improve PLC code and requirements.

Current context:
Device Constants: {json.dumps(context.device_constants, indent=2)}
Information: {context.information}

User message: {user_message or "No specific message"}

Provide helpful response for code refinement. You can:
- Suggest improvements
- Ask clarifying questions (use MCQ for standard choices)
- Provide technical guidance
- Help with testing scenarios

Return JSON format:
{{
    "message": "Your response",
    "is_mcq": false,
    "mcq_question": null,
    "mcq_options": [],
    "is_multiselect": false
}}

Keep responses focused and actionable.
"""
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
        
        # Extract text from uploaded files (no LLM call yet)
        extracted_file_texts = []
        if uploaded_files:
            for file_data in uploaded_files:
                try:
                    file_bytes = file_data.getvalue()
                    extracted_text = self._extract_text_from_bytes(file_bytes)
                    if extracted_text and extracted_text != "PDF processing libraries not available":
                        extracted_file_texts.append(extracted_text)
                except Exception as e:
                    logger.warning(f"Failed to extract text from uploaded file: {e}")
        
        # Single comprehensive LLM call that handles everything
        response = await self._process_comprehensive_update(
            request, 
            extracted_file_texts
        )
        
        return response
    
    async def _process_comprehensive_update(
        self,
        request: ContextUpdateRequest,
        extracted_file_texts: List[str]
    ) -> ContextUpdateResponse:
        """
        Single comprehensive LLM call that handles context update, file processing, and response generation.
        
        Args:
            request: Original context update request
            extracted_file_texts: Raw text extracted from uploaded files
            
        Returns:
            Complete context update response
        """
        # Build comprehensive prompt
        comprehensive_prompt = self._build_comprehensive_prompt(
            request.current_context,
            request.current_stage,
            request.message,
            request.mcq_responses,
            extracted_file_texts
        )
        
        # Single LLM call with higher token limit for comprehensive response
        from app.schemas.openai import ChatRequest
        chat_request = ChatRequest(
            user_prompt="",  # Will be overridden by messages
            model="gpt-4o" if request.current_stage == Stage.CODE_GENERATION else "gpt-4o-mini",
            temperature=0.3 if request.current_stage == Stage.CODE_GENERATION else 0.7,
            max_tokens=2048 if request.current_stage == Stage.CODE_GENERATION else 1024
        )
        
        response, usage = await self.openai_service.chat_completion(
            chat_request,
            messages=[{"role": "user", "content": comprehensive_prompt}]
        )
        
        # Parse comprehensive response
        try:
            logger.debug(f"Raw AI response: {response}")
            
            # Strip markdown code blocks if present
            response_content = response.strip()
            if response_content.startswith("```json"):
                response_content = response_content[7:]  # Remove ```json
            if response_content.endswith("```"):
                response_content = response_content[:-3]  # Remove ```
            response_content = response_content.strip()
            
            ai_response = json.loads(response_content)
            
            # Extract updated context
            updated_context_data = ai_response.get("updated_context", {})
            updated_context = ProjectContext(
                device_constants=updated_context_data.get("device_constants", request.current_context.device_constants),
                information=updated_context_data.get("information", request.current_context.information)
            )
            
            # Extract file processing results
            file_extractions = []
            for file_result in ai_response.get("file_extractions", []):
                file_extractions.append(FileProcessingResult(
                    extracted_devices=file_result.get("extracted_devices", {}),
                    extracted_information=file_result.get("extracted_information", ""),
                    processing_summary=file_result.get("processing_summary", "Processed file successfully")
                ))
            
            # Calculate progress for requirements gathering
            progress = None
            if request.current_stage == Stage.GATHERING_REQUIREMENTS:
                progress = self._calculate_requirements_progress(updated_context)
            
            return ContextUpdateResponse(
                updated_context=updated_context,
                chat_message=ai_response.get("chat_message", ""),
                gathering_requirements_progress=progress,
                current_stage=request.current_stage,
                is_mcq=ai_response.get("is_mcq", False),
                is_multiselect=ai_response.get("is_multiselect", False),
                mcq_question=ai_response.get("mcq_question"),
                mcq_options=ai_response.get("mcq_options", []),
                generated_code=ai_response.get("generated_code"),
                file_extractions=file_extractions
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse comprehensive AI response: {e}")
            logger.error(f"Raw response (first 1000 chars): {response[:1000]}")
            # Fallback response
            return ContextUpdateResponse(
                updated_context=request.current_context,
                chat_message="I encountered an error processing your request. Please try again.",
                gathering_requirements_progress=0.0 if request.current_stage == Stage.GATHERING_REQUIREMENTS else None,
                current_stage=request.current_stage,
                is_mcq=False,
                is_multiselect=False,
                mcq_question=None,
                mcq_options=[],
                file_extractions=[]
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
    
    def _build_comprehensive_prompt(
        self,
        context: ProjectContext,
        stage: Stage,
        user_message: Optional[str],
        mcq_responses: List[str],
        extracted_file_texts: List[str]
    ) -> str:
        """Build comprehensive prompt that handles everything in one LLM call."""
        
        # Calculate current progress for requirements gathering
        progress = self._calculate_requirements_progress(context) if stage == Stage.GATHERING_REQUIREMENTS else 0.0
        
        # File content section (comes at the end)
        file_content_section = ""
        if extracted_file_texts:
            # Truncate file content but not too aggressively (8000 chars to preserve important info)
            combined_file_text = "\n\n--- FILE SEPARATOR ---\n\n".join(extracted_file_texts)
            max_file_content = 8000
            if len(combined_file_text) > max_file_content:
                combined_file_text = combined_file_text[:max_file_content] + "...[truncated]"
            
            file_content_section = f"""

=== SUPPLEMENTARY FILE DATA ===
NOTE: The user's message and MCQ responses above are MORE IMPORTANT than file content.
Use file content as additional context only.

Uploaded file content:
{combined_file_text}
"""

        # Stage-specific instructions
        stage_instructions = ""
        expected_response_fields = ""
        
        if stage == Stage.GATHERING_REQUIREMENTS:
            stage_instructions = f"""
STAGE: Requirements Gathering (Progress: {progress:.1%})

Your primary task is to ask the next focused question to gather PLC programming requirements.
Reference the user's input when appropriate to provide contextual follow-up questions.

PRIORITIES (ask about missing items first):
1. Safety requirements (emergency stops, protection)
2. I/O specifications (inputs, outputs, sensors, actuators)  
3. Control sequence basics
4. PLC platform/hardware
5. Communication requirements

Use MCQ for standardized choices (safety features, voltage levels, protocols, etc.).
"""
            expected_response_fields = """
    "chat_message": "Your question or response",
    "is_mcq": false,
    "mcq_question": null,
    "mcq_options": [],
    "is_multiselect": false,
    "generated_code": null,"""
            
        elif stage == Stage.CODE_GENERATION:
            stage_instructions = """
STAGE: Code Generation

Generate complete, production-ready Structured Text (ST) code including:
- Variable declarations (inputs, outputs, internal variables)
- Function blocks and programs
- Main control logic with safety interlocks
- Error handling and clear comments

Structure: TYPE declarations → PROGRAM → VAR sections → Main logic → Safety/error handling

CRITICAL: The Structured Text code must be properly escaped as a JSON string value.
"""
            expected_response_fields = """
    "chat_message": "I've generated the Structured Text code based on your requirements. You can now review and refine it.",
    "is_mcq": false,
    "mcq_question": null,
    "mcq_options": [],
    "is_multiselect": false,
    "generated_code": "PROGRAM Main\\nVAR\\n  // Variable declarations\\nEND_VAR\\n\\n// Main logic\\n\\nEND_PROGRAM","""
            
        elif stage == Stage.REFINEMENT_TESTING:
            stage_instructions = """
STAGE: Refinement and Testing

Provide helpful responses for code refinement. You can:
- Suggest improvements
- Ask clarifying questions (use MCQ for standard choices)
- Provide technical guidance
- Help with testing scenarios
"""
            expected_response_fields = """
    "chat_message": "Your response",
    "is_mcq": false,
    "mcq_question": null,
    "mcq_options": [],
    "is_multiselect": false,
    "generated_code": null,"""

        return f"""=== PRIMARY CONTEXT (MOST IMPORTANT) ===

Current Project Context:
Device Constants: {json.dumps(context.device_constants, indent=2)}
Information: {context.information}

USER INPUT (CRITICAL - MUST BE REFERENCED):
Message: {user_message or "None"}
MCQ Responses: {mcq_responses or "None"}

{stage_instructions}

TASK: Process the user input, update the context, extract any file data, and provide appropriate response.

Return a JSON object with this EXACT structure:
{{
    "updated_context": {{
        "device_constants": {{
            // Updated device specifications - integrate file extractions and user input
        }},
        "information": "Updated markdown summary - integrate user input and file data concisely"
    }},
    {expected_response_fields}
    "file_extractions": [
        {{
            "extracted_devices": {{
                // Device specs extracted from files
            }},
            "extracted_information": "Brief PLC-relevant summary from files",
            "processing_summary": "One sentence about what was extracted"
        }}
    ]
}}

CRITICAL RULES:
- User message and MCQ responses are PRIMARY - reference them directly in your response
- Only extract PLC-relevant information from files (devices, I/O, safety, control logic)
- Be extremely concise in updated context
- If no files uploaded, return empty file_extractions array
- For MCQ responses: set is_mcq=true, provide mcq_question and mcq_options{file_content_section}"""
    
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
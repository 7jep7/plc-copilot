"""
Context service for unified API approach.

Features:
- Single LLM call per interaction (reduced latency)
- Stage-aware prompting and responses
- File processing and extraction
- MCQ support and progress tracking
- Template selection based on file presence
"""

import json
import asyncio
import re
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.context import (
    ProjectContext, ContextUpdateRequest, ContextUpdateResponse, Stage, 
    FileProcessingResult, DeviceEntry, DeviceOrigin
)
from app.services.openai_service import OpenAIService
from app.services.document_service import DocumentService
from app.services.prompt_templates import PromptTemplates

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
        
        # Extract text from uploaded files and process them asynchronously
        extracted_file_texts: List[str] = []
        raw_file_texts: List[str] = []  # Fallback for when file processing fails
        file_results: List[FileProcessingResult] = []
        if uploaded_files:
            logger.info(f"Processing {len(uploaded_files)} uploaded files")
            for i, file_data in enumerate(uploaded_files):
                try:
                    file_bytes = file_data.getvalue()
                    logger.info(f"Processing file {i+1}: {len(file_bytes)} bytes")
                    
                    # First extract raw text as fallback
                    try:
                        raw_text = self._extract_text_from_bytes(file_bytes)
                        if raw_text:
                            raw_file_texts.append(raw_text[:8000])  # Limit size
                            logger.info(f"File {i+1} raw text extracted: {len(raw_text)} chars")
                    except Exception as raw_e:
                        logger.warning(f"Failed to extract raw text from file {i+1}: {raw_e}")
                    
                    # Use async helper to process uploaded file (may call LLM)
                    result = await self._process_uploaded_file(file_bytes)
                    file_results.append(result)
                    logger.info(f"File {i+1} processing result: {result.processing_summary}")
                    if result.extracted_information:
                        extracted_file_texts.append(result.extracted_information)
                        logger.info(f"File {i+1} extracted {len(result.extracted_information)} chars of text")
                    else:
                        logger.warning(f"File {i+1} extraction resulted in no text content")
                except Exception as e:
                    logger.error(f"Failed to extract/process uploaded file {i+1}: {e}")
            
            logger.info(f"Total extracted file texts: {len(extracted_file_texts)}")
            logger.info(f"Total raw file texts: {len(raw_file_texts)}")
        else:
            logger.info("No uploaded files to process")

        # Integrate file extraction results into the current context before the comprehensive LLM call
        current_ctx = request.current_context
        for fr in file_results:
            current_ctx = self._integrate_file_extraction(current_ctx, fr)

        # Single comprehensive LLM call that handles everything
        response = await self._process_comprehensive_update(
            ContextUpdateRequest(
                message=request.message,
                mcq_responses=request.mcq_responses,
                previous_copilot_message=request.previous_copilot_message,
                current_context=current_ctx,
                current_stage=request.current_stage
            ),
            extracted_file_texts if extracted_file_texts else raw_file_texts
        )

        # Attach file_extractions produced earlier if the LLM didn't include them
        if response.file_extractions == [] and file_results:
            response.file_extractions = file_results

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
        # Check if context is completely empty - use lightweight prompt for off-topic detection
        context_is_empty = (
            not request.current_context.device_constants and 
            not request.current_context.information.strip()
        )
        
        # Check if message contains clear automation keywords
        def contains_automation_keywords(message: str) -> bool:
            if not message:
                return False
            message_lower = message.lower()
            automation_keywords = [
                'automate', 'automation', 'conveyor', 'motor', 'plc', 'sensor', 'control', 
                'manufacturing', 'industrial', 'process', 'system', 'machine', 'equipment', 
                'safety', 'start', 'stop', 'sequence', 'monitoring', 'temperature', 'pressure',
                'valve', 'pump', 'actuator', 'relay', 'switch', 'alarm', 'interlock'
            ]
            return any(keyword in message_lower for keyword in automation_keywords)
        
        # Build comprehensive prompt using appropriate template
        if extracted_file_texts:
            # Template B: For messages with files (always prioritize file processing)
            logger.info(f"Using Template B (file processing) with {len(extracted_file_texts)} extracted texts")
            comprehensive_prompt = PromptTemplates.build_template_b_prompt(
                context=request.current_context,
                stage=request.current_stage,
                user_message=request.message,
                mcq_responses=request.mcq_responses,
                extracted_file_texts=extracted_file_texts,
                previous_copilot_message=request.previous_copilot_message
            )
        elif (context_is_empty and 
              request.current_stage == Stage.GATHERING_REQUIREMENTS and 
              not request.mcq_responses and 
              not contains_automation_keywords(request.message or "")):
            # Use lightweight prompt optimized for off-topic detection ONLY if:
            # - Context is empty AND no MCQ responses AND no clear automation keywords
            # This ensures automation-related messages skip the off-topic detection
            logger.info("Using empty context prompt (off-topic detection)")
            comprehensive_prompt = PromptTemplates.build_empty_context_prompt(
                user_message=request.message,
                mcq_responses=request.mcq_responses,
                previous_copilot_message=request.previous_copilot_message
            )
        else:
            # Template A: For messages without files (includes MCQ responses, automation keywords, or non-empty context)
            logger.info("Using Template A (no files)")
            comprehensive_prompt = PromptTemplates.build_template_a_prompt(
                context=request.current_context,
                stage=request.current_stage,
                user_message=request.message,
                mcq_responses=request.mcq_responses,
                previous_copilot_message=request.previous_copilot_message
            )
        
        # Single LLM call with higher token limit for comprehensive response
        from app.schemas.openai import ChatRequest
        chat_request = ChatRequest(
            user_prompt="",  # Will be overridden by messages
            model="gpt-4o" if request.current_stage == Stage.CODE_GENERATION else "gpt-4o-mini",
            temperature=0.3 if request.current_stage == Stage.CODE_GENERATION else 0.7,
            max_tokens=2048 if request.current_stage == Stage.CODE_GENERATION else 1024
        )
        
        # Call the chat_completion helper - allow for sync or async mocks in tests
        chat_call = self.openai_service.chat_completion(
            chat_request,
            messages=[{"role": "user", "content": comprehensive_prompt}]
        )

        # Resolve the call (support async awaitables and sync returns/mocks)
        raw_resp = None
        if hasattr(chat_call, '__await__'):
            raw_resp = await chat_call
        else:
            raw_resp = chat_call

        # Normalize response into (response_text, usage)
        response = None
        usage = None
        try:
            # If returned a tuple/list like (content, usage)
            if isinstance(raw_resp, (list, tuple)) and len(raw_resp) >= 1:
                response = raw_resp[0]
                usage = raw_resp[1] if len(raw_resp) > 1 else None
            elif hasattr(raw_resp, 'content'):
                response = raw_resp.content
                usage = getattr(raw_resp, 'usage', None)
            elif hasattr(raw_resp, 'choices'):
                # OpenAI-like object
                try:
                    response = raw_resp.choices[0].message.content
                    usage = getattr(raw_resp, 'usage', None)
                except Exception:
                    response = str(raw_resp)
            elif isinstance(raw_resp, str):
                response = raw_resp
            else:
                response = str(raw_resp)
        except Exception:
            response = str(raw_resp)
        
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
            
            # Try to parse JSON. If this fails, retry with a corrective prompt.
            try:
                ai_response = json.loads(response_content)
                # Ensure it's a dictionary
                if not isinstance(ai_response, dict):
                    raise json.JSONDecodeError(f"Response is not a JSON object: {type(ai_response)}", response_content, 0)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse failed, retrying with corrective prompt. Error: {e}")
                
                # Build corrective prompt asking for proper JSON format
                corrective_prompt = f"""The previous response was not valid JSON. 

Context: Stage {request.current_stage}, Message: "{request.message or 'None'}", MCQ: {request.mcq_responses or []}

CRITICAL: Return ONLY valid JSON (no markdown blocks, no comments, no extra text):
{{
    "updated_context": {{"device_constants": {{}}, "information": ""}},
    "chat_message": "response text",
    "is_mcq": false,
    "mcq_question": null,
    "mcq_options": [],
    "is_multiselect": false,
    "generated_code": null,
    "gathering_requirements_estimated_progress": 0.5,
    "file_extractions": []
}}

Include all required fields for stage {request.current_stage}. Response must be parseable by JSON.parse()."""

                # Retry the LLM call with corrective prompt
                retry_call = self.openai_service.chat_completion(
                    chat_request,
                    messages=[{"role": "user", "content": corrective_prompt}]
                )

                # Resolve retry call
                if hasattr(retry_call, '__await__'):
                    retry_raw = await retry_call
                else:
                    retry_raw = retry_call

                # Normalize retry response
                retry_resp = None
                if isinstance(retry_raw, (list, tuple)) and len(retry_raw) >= 1:
                    retry_resp = retry_raw[0]
                elif hasattr(retry_raw, 'content'):
                    retry_resp = retry_raw.content
                elif isinstance(retry_raw, str):
                    retry_resp = retry_raw
                else:
                    retry_resp = str(retry_raw)

                # Clean and try parsing retry response
                retry_content = retry_resp.strip() if isinstance(retry_resp, str) else str(retry_resp)
                if retry_content.startswith("```json"):
                    retry_content = retry_content[7:]
                if retry_content.endswith("```"):
                    retry_content = retry_content[:-3]
                retry_content = retry_content.strip()

                try:
                    ai_response = json.loads(retry_content)
                    if not isinstance(ai_response, dict):
                        raise json.JSONDecodeError(f"Retry response is not a JSON object: {type(ai_response)}", retry_content, 0)
                    logger.info("Corrective prompt succeeded, parsed JSON response")
                except json.JSONDecodeError as retry_error:
                    logger.error(f"Corrective prompt also failed: {retry_error}")
                    # Fall back to safe error response instead of crashing
                    logger.warning("Falling back to safe error response due to persistent JSON parse failures")
                    return ContextUpdateResponse(
                        updated_context=request.current_context,
                        chat_message="I encountered an error processing your request. Please try rephrasing or uploading the file again.",
                        gathering_requirements_estimated_progress=None,
                        current_stage=request.current_stage,
                        is_mcq=False,
                        is_multiselect=False,
                        mcq_question=None,
                        mcq_options=[],
                        file_extractions=[]
                    )
            
            # Ensure ai_response is a dictionary before proceeding
            if not isinstance(ai_response, dict):
                logger.error(f"ai_response is not a dictionary: {type(ai_response)} - {ai_response}")
                # Fall back to safe error response instead of crashing
                return ContextUpdateResponse(
                    updated_context=request.current_context,
                    chat_message="I encountered an error processing your request. Please try rephrasing or uploading the file again.",
                    gathering_requirements_estimated_progress=None,
                    current_stage=request.current_stage,
                    is_mcq=False,
                    is_multiselect=False,
                    mcq_question=None,
                    mcq_options=[],
                    file_extractions=[]
                )
            
            # Extract updated context
            updated_context_data = ai_response.get("updated_context", {})
            # Normalize device_constants: ensure dicts for JSON compatibility
            raw_devices = updated_context_data.get("device_constants", request.current_context.device_constants)
            norm_devices = {}
            for name, val in (raw_devices or {}).items():
                if hasattr(val, 'model_dump'):
                    norm_devices[name] = val.model_dump()
                else:
                    norm_devices[name] = val

            updated_context = ProjectContext(
                device_constants=norm_devices,
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
            
            # Get AI's progress estimation for requirements gathering
            estimated_progress = None
            if request.current_stage == Stage.GATHERING_REQUIREMENTS:
                estimated_progress = ai_response.get("gathering_requirements_estimated_progress")
                # If the LLM didn't provide a numeric value, default to a neutral mid-point
                if estimated_progress is None:
                    estimated_progress = 0.5

            # If the AI didn't include a chat_message, request a concise follow-up question/message
            # Accept either 'chat_message' or 'message' from LLM outputs
            chat_message = ai_response.get("chat_message") or ai_response.get("message", "")
            is_mcq_val = bool(ai_response.get("is_mcq", False))
            mcq_question = ai_response.get("mcq_question")
            mcq_options = ai_response.get("mcq_options", [])

            if not chat_message:
                # Build a lightweight follow-up prompt using the updated context
                followup_prompt = f"Based on the updated context (device_constants and information), produce a short user-facing JSON response with keys: message, is_mcq, mcq_question, mcq_options, is_multiselect. Only return valid JSON.\nContext devices: {json.dumps(updated_context.device_constants)}\nInformation: {updated_context.information}"

                follow_call = self.openai_service.chat_completion(
                    chat_request,
                    messages=[{"role": "user", "content": followup_prompt}]
                )

                # Resolve follow-up call (support sync mocks)
                if hasattr(follow_call, '__await__'):
                    follow_raw = await follow_call
                else:
                    follow_raw = follow_call

                # Normalize follow_raw similarly to earlier
                follow_resp = None
                if isinstance(follow_raw, (list, tuple)) and len(follow_raw) >= 1:
                    follow_resp = follow_raw[0]
                elif hasattr(follow_raw, 'content'):
                    follow_resp = follow_raw.content
                elif isinstance(follow_raw, str):
                    follow_resp = follow_raw
                else:
                    follow_resp = str(follow_raw)

                # Try parsing JSON from follow_resp
                try:
                    follow_json = json.loads(follow_resp)
                    chat_message = follow_json.get('message') or follow_json.get('chat_message') or ''
                    is_mcq_val = bool(follow_json.get('is_mcq', is_mcq_val))
                    mcq_question = follow_json.get('mcq_question', mcq_question)
                    mcq_options = follow_json.get('mcq_options', mcq_options)
                except Exception:
                    # If parse fails, fall back to raw text
                    chat_message = follow_resp if isinstance(follow_resp, str) else str(follow_resp)
            
            return ContextUpdateResponse(
                updated_context=updated_context,
                chat_message=chat_message or "",
                gathering_requirements_estimated_progress=estimated_progress,
                current_stage=request.current_stage,
                # Use normalized MCQ values
                is_mcq=is_mcq_val,
                is_multiselect=bool(ai_response.get("is_multiselect", False)),
                mcq_question=mcq_question,
                mcq_options=mcq_options,
                generated_code=ai_response.get("generated_code"),
                file_extractions=file_extractions
            )
            
        except (json.JSONDecodeError, ValueError, AttributeError) as e:
            logger.error(f"Failed to parse comprehensive AI response: {e}")
            logger.error(f"Raw response (first 1000 chars): {response[:1000] if isinstance(response, str) else str(response)[:1000]}")
            # Fallback response - ensure graceful handling
            return ContextUpdateResponse(
                updated_context=request.current_context,
                chat_message="I encountered an error processing your request. Please try again or rephrase your message.",
                gathering_requirements_estimated_progress=None,
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
        updated_devices = {}
        # Normalize existing devices to dicts
        for k, v in context.device_constants.items():
            if hasattr(v, 'model_dump'):
                updated_devices[k] = v.model_dump()
            else:
                updated_devices[k] = v

        for device_name, device_data in extraction.extracted_devices.items():
            if device_name in updated_devices and isinstance(updated_devices[device_name], dict) and isinstance(device_data, dict):
                # Merge keys
                updated_devices[device_name].update(device_data)
            else:
                # Overwrite or add
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
    
    
    def _extract_text_from_bytes(self, file_bytes: bytes) -> str:
        """
        Extract text from file bytes. Supports PDF, text files, and more.
        
        Args:
            file_bytes: File content as bytes
            
        Returns:
            Extracted text content
        """
        text_content = []
        
        # First try to detect if it's a text file
        try:
            # Try to decode as UTF-8 text
            text = file_bytes.decode('utf-8')
            if text.strip():
                return text
        except UnicodeDecodeError:
            # Not a text file, continue with other methods
            pass
        
        # Check if PDF processing is available and if this looks like a PDF
        if PDF_AVAILABLE and file_bytes.startswith(b'%PDF'):
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
        else:
            # For non-PDF files, try other approaches
            try:
                # Try to decode with different encodings
                for encoding in ['utf-8', 'latin-1', 'ascii']:
                    try:
                        text = file_bytes.decode(encoding)
                        if text.strip():
                            return text
                    except UnicodeDecodeError:
                        continue
            except Exception as e:
                logger.warning(f"Text extraction failed: {e}")
        
        if text_content:
            return "\n\n".join(text_content)
        else:
            # Last resort: return bytes info
            return f"Binary file uploaded ({len(file_bytes)} bytes). Unable to extract text content."


    async def _process_uploaded_file(self, file_bytes: bytes) -> FileProcessingResult:
        """Async file processor used during request handling; calls the LLM to parse file content."""
        try:
            text = self._extract_text_from_bytes(file_bytes)
            if not text or not text.strip():
                return FileProcessingResult(
                    extracted_devices={}, 
                    extracted_information="", 
                    processing_summary="No text extracted from file"
                )

            logger.info(f"Extracted {len(text)} characters from file, calling LLM for processing")
            prompt = self._build_file_extraction_prompt(text)
            chat_req = type("R", (), {"user_prompt": prompt, "model": None, "temperature": 0.7, "max_completion_tokens": 1024})

            try:
                call = self.openai_service.chat_completion(chat_req, messages=[{"role": "user", "content": prompt}])
                if hasattr(call, '__await__'):
                    raw = await call
                else:
                    raw = call

                # Normalize raw response
                resp_text = None
                if isinstance(raw, (list, tuple)) and len(raw) >= 1:
                    resp_text = raw[0]
                elif hasattr(raw, 'content'):
                    resp_text = raw.content
                elif isinstance(raw, str):
                    resp_text = raw
                else:
                    resp_text = str(raw)

                logger.info(f"LLM file processing response received: {len(resp_text) if resp_text else 0} chars")
            except Exception as llm_e:
                logger.error(f"LLM call failed for file processing: {llm_e}")
                # Fallback: return raw text as extracted information
                return FileProcessingResult(
                    extracted_devices={},
                    extracted_information=text[:2000],  # Limit size
                    processing_summary=f"LLM processing failed, returning raw text: {str(llm_e)}"
                )

            import json as _json
            try:
                parsed = _json.loads(resp_text)
                devices = parsed.get('devices', {})
                info = parsed.get('information', '')
                summary = parsed.get('summary', 'Processed file successfully')
                return FileProcessingResult(
                    extracted_devices=devices,
                    extracted_information=info,
                    processing_summary=summary
                )
            except Exception:
                # Fallback: return the raw text snippet
                return FileProcessingResult(
                    extracted_devices={},
                    extracted_information=text[:2000],
                    processing_summary="Could not parse structured extraction from LLM"
                )
        except Exception as e:
            return FileProcessingResult(extracted_devices={}, extracted_information="", processing_summary=f"Error processing file: {e}")
    
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

        return f"""Extract PLC-relevant data from this document. Be selective - only automation/control content.

Document: {file_content}

RESPONSE: Return ONLY valid JSON (no markdown, no extra text):
{{
    "devices": {{
        "DeviceName": {{
            "Type": "device type",
            "Model": "model number",
            "Specifications": {{"key": "value"}}
        }}
    }},
    "information": "Brief markdown summary of PLC requirements",
    "summary": "One sentence describing extraction"
}}

Focus: Device specs, electrical specs, I/O requirements, safety, control sequences."""
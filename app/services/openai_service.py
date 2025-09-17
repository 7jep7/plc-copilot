"""OpenAI service for AI-powered PLC code generation."""

import openai
import structlog
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
import re
import asyncio

from app.core.config import settings
from app.core.models import ModelConfig
from app.models.document import Document
from app.schemas.plc_code import PLCGenerationRequest
from app.services.notification_service import NotificationService

logger = structlog.get_logger()

# Ensure there is a running event loop available for tests that call asyncio.get_event_loop()
try:
    # Prefer get_running_loop to check for an active loop; if none, create and set one
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
except Exception:
    # Be defensive: if anything unexpected happens here, ensure there's still a loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except Exception:
        # Last resort: continue without setting (tests will surface problems)
        pass
# Initialize OpenAI client
openai.api_key = settings.OPENAI_API_KEY


class OpenAIParameterError(Exception):
    """Raised when the OpenAI API reports an unsupported parameter or value.

    Attributes:
        param: the name of the offending parameter (if available)
        message: original error message
    """

    def __init__(self, param: str | None, message: str):
        super().__init__(message)
        self.param = param
        self.message = message


class OpenAIService:
    """Service for OpenAI API integration."""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.notification_service = NotificationService()
        self._rate_limited_models = set()  # Track models that hit daily rate limits this session
        self._current_active_model = None  # Track which model we're currently using
        self._last_reset_date = None  # Track when we last reset the rate limit memory

    def _safe_chat_create(self, **kwargs):
        """Call chat.completions.create with automatic fallback on rate limits."""
        return self._safe_chat_create_with_fallback(**kwargs)
    
    def _safe_chat_create_with_fallback(self, **kwargs):
        """Call chat.completions.create and handle rate limits with intelligent model selection."""
        original_model = kwargs.get('model', ModelConfig.CONVERSATION_MODEL)
        request_obj = kwargs.pop('request', None)  # Extract request object, don't pass to OpenAI
        
        # Determine the best model to use based on rate limit history
        selected_model = self._get_best_available_model(original_model)
        kwargs['model'] = selected_model
        
        try:
            response = self.client.chat.completions.create(**kwargs)
            
            # If this is the first time using a different model, log the switch
            if self._current_active_model != selected_model:
                if self._current_active_model is not None:
                    logger.info(
                        "Model switched for this session",
                        from_model=self._current_active_model,
                        to_model=selected_model,
                        reason="rate_limit_avoidance"
                    )
                self._current_active_model = selected_model
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            
            # Check if this is a rate limit error
            if self._is_rate_limit_error(error_msg):
                # Mark this model as rate limited
                self._rate_limited_models.add(selected_model)
                
                # Try to find another model that hasn't been rate limited
                fallback_model = self._get_best_available_model(selected_model)
                
                if fallback_model == selected_model:
                    # No alternatives available, this error will bubble up
                    logger.error(
                        "All available models are rate limited",
                        rate_limited_models=list(self._rate_limited_models),
                        attempted_model=selected_model
                    )
                    raise e
                
                logger.warning(
                    "Rate limit hit, switching to alternative model",
                    rate_limited_model=selected_model,
                    fallback_model=fallback_model,
                    error=error_msg
                )
                
                # Send notification email (once per session)
                conversation_id = getattr(request_obj, 'conversation_id', None) if request_obj else None
                self.notification_service.send_rate_limit_alert(
                    primary_model=selected_model,
                    fallback_model=fallback_model,
                    error_message=error_msg,
                    conversation_id=conversation_id
                )
                
                # Try with the alternative model
                try:
                    kwargs['model'] = fallback_model
                    response = self.client.chat.completions.create(**kwargs)
                    
                    # Update current active model
                    self._current_active_model = fallback_model
                    
                    logger.info(
                        "Fallback model successful",
                        rate_limited_model=selected_model,
                        successful_model=fallback_model
                    )
                    
                    return response
                    
                except Exception as fallback_error:
                    # Mark the fallback model as rate limited too
                    self._rate_limited_models.add(fallback_model)
                    
                    logger.error(
                        "Fallback model also failed",
                        rate_limited_model=selected_model,
                        failed_fallback=fallback_model,
                        fallback_error=str(fallback_error)
                    )
                    # Raise the original error
                    raise e
            
            # For non-rate-limit errors, check for parameter errors
            m = re.search(r"Unsupported (?:parameter|value): '\\'([^\\']+)\\'", error_msg)
            if not m:
                m = re.search(r"Unsupported (?:parameter|value): '([^']+)'", error_msg)

            param = m.group(1) if m else None
            # Raise a structured error the API layer can handle
            raise OpenAIParameterError(param=param, message=error_msg)
    
    def _get_best_available_model(self, requested_model: str) -> str:
        """Get the best available model that hasn't hit rate limits (with daily reset detection)."""
        
        # Check if we should reset rate limit memory for a new day
        self._check_and_reset_daily_limits()
        
        # If the requested model hasn't been rate limited, use it
        if requested_model not in self._rate_limited_models:
            return requested_model
        
        # Try the cascade of fallback models
        fallback_models = ModelConfig.get_fallback_models(requested_model)
        for fallback in fallback_models:
            if fallback not in self._rate_limited_models:
                logger.info(
                    "Using fallback model",
                    original_model=requested_model,
                    selected_model=fallback,
                    rate_limited_models=list(self._rate_limited_models)
                )
                return fallback
        
        # If all models in the cascade are rate limited, return the requested model
        # (it will fail, but that's expected and will trigger proper error handling)
        logger.warning(
            "All models in cascade are rate limited, returning requested model",
            requested_model=requested_model,
            cascade_models=fallback_models,
            rate_limited_models=list(self._rate_limited_models)
        )
        return requested_model
    
    def _check_and_reset_daily_limits(self):
        """Reset rate limit memory if it's a new day (OpenAI limits reset at midnight UTC)."""
        from datetime import datetime, timezone
        
        current_date = datetime.now(timezone.utc).date()
        
        if self._last_reset_date is None:
            # First time - initialize
            self._last_reset_date = current_date
            return
        
        if current_date > self._last_reset_date:
            # It's a new day! Reset rate limit memory
            old_rate_limited = list(self._rate_limited_models)
            self._rate_limited_models.clear()
            self._last_reset_date = current_date
            
            # Reset email notification flag too
            self.notification_service._email_sent_this_session = False
            
            logger.info(
                "Daily rate limit reset - all models available again",
                previous_date=str(self._last_reset_date),
                current_date=str(current_date),
                previously_rate_limited=old_rate_limited
            )
    
    def _is_rate_limit_error(self, error_message: str) -> bool:
        """Check if the error is related to rate limits."""
        rate_limit_indicators = [
            "rate limit",
            "Rate limit",
            "429",
            "requests per",
            "quota exceeded",
            "too many requests"
        ]
        return any(indicator in error_message for indicator in rate_limit_indicators)
    
    def get_session_model_status(self) -> dict:
        """Get the current session's model usage status."""
        from datetime import datetime, timezone
        
        # Check for daily reset first
        self._check_and_reset_daily_limits()
        
        return {
            "current_active_model": self._current_active_model,
            "rate_limited_models": list(self._rate_limited_models),
            "available_models": [
                model for model in [ModelConfig.CONVERSATION_MODEL, ModelConfig.get_fallback_model(ModelConfig.CONVERSATION_MODEL)]
                if model not in self._rate_limited_models
            ],
            "last_reset_date": str(self._last_reset_date) if self._last_reset_date else None,
            "current_utc_date": str(datetime.now(timezone.utc).date())
        }
    
    async def generate_plc_code(
        self,
        request: PLCGenerationRequest,
        document_context: Optional[Document] = None
    ) -> Dict[str, Any]:
        """
        Generate PLC code using OpenAI based on user prompt and optional document context.
        
        Args:
            request: PLC generation request with prompt and parameters
            document_context: Optional document for additional context
            
        Returns:
            Dictionary containing generated code and metadata
        """
        logger.info("Starting PLC code generation", prompt_length=len(request.user_prompt))
        
        try:
            # Build the system prompt
            system_prompt = self._build_system_prompt(request)
            
            # Build the user prompt with context
            user_prompt = self._build_user_prompt(request, document_context)
            
            # Call OpenAI API
            # Note: newer OpenAI models expect `max_completion_tokens` instead of `max_tokens`.
            response = self._safe_chat_create(
                model=ModelConfig.CONVERSATION_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=request.temperature,
                max_completion_tokens=request.max_completion_tokens or 2000,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # Extract the generated code
            generated_content = response.choices[0].message.content
            
            # Parse the response to extract code and metadata
            result = self._parse_generated_response(generated_content, request)
            
            # Add generation metadata
            result["generation_metadata"] = {
                "model": ModelConfig.CONVERSATION_MODEL,
                "temperature": request.temperature,
                "max_completion_tokens": request.max_completion_tokens or 2000,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            logger.info("PLC code generation completed", tokens_used=response.usage.total_tokens)
            return result
            
        except Exception as e:
            logger.error("OpenAI API call failed", error=str(e))
            raise
    
    def _build_system_prompt(self, request: PLCGenerationRequest) -> str:
        """Build the system prompt for PLC code generation."""
        
        language_instructions = {
            "structured_text": "Generate code in IEC 61131-3 Structured Text (ST) format.",
            "ladder_logic": "Generate ladder logic code with proper rung structure.",
            "function_block": "Generate function block diagrams with proper interfaces.",
            "instruction_list": "Generate instruction list code with proper mnemonics.",
            "sequential_function_chart": "Generate SFC code with steps and transitions."
        }
        
        system_prompt = f"""You are an expert PLC (Programmable Logic Controller) programmer specializing in industrial automation.

Your task is to generate high-quality, production-ready PLC code based on user requirements.

Key requirements:
1. {language_instructions.get(request.language, "Generate PLC code")}
2. Follow IEC 61131-3 standards and best practices
3. Include proper variable declarations and data types
4. Add comprehensive comments explaining the logic
5. Implement safety considerations and error handling
6. Ensure code is modular and maintainable

Code structure should include:
- Variable declarations (inputs, outputs, internal variables)
- Main program logic
- Safety interlocks and emergency stops
- Error handling and diagnostics
- Comments explaining each section

Language: {request.language}
Target PLC: {request.target_plc_type or "Generic IEC 61131-3 compatible"}

Safety requirements:
- Always include emergency stop logic
- Implement fail-safe behavior
- Add safety interlocks for dangerous operations
- Include proper error handling

Format your response as:
```
PROGRAM MainProgram
VAR
    (* Input variables *)
    (* Output variables *)
    (* Internal variables *)
END_VAR

(* Main program logic *)
(* Your code here *)

END_PROGRAM
```"""

        if request.include_io_definitions:
            system_prompt += "\n\nInclude detailed I/O variable definitions with proper data types and descriptions."
        
        if request.include_safety_checks:
            system_prompt += "\n\nImplement comprehensive safety checks and emergency stop procedures."
            
        return system_prompt
    
    def _build_user_prompt(self, request: PLCGenerationRequest, document_context: Optional[Document] = None) -> str:
        """Build the user prompt with request details and optional document context."""
        
        prompt_parts = [f"User Request: {request.user_prompt}"]
        
        if document_context and document_context.structured_data:
            prompt_parts.append(f"\nDocument Context:")
            prompt_parts.append(f"Device: {document_context.manufacturer} {document_context.device_model}")
            
            if document_context.specifications:
                prompt_parts.append("Technical Specifications:")
                for key, value in document_context.specifications.items():
                    prompt_parts.append(f"- {key}: {value}")
        
        if request.name:
            prompt_parts.append(f"\nProgram Name: {request.name}")
        
        if request.description:
            prompt_parts.append(f"Description: {request.description}")
        
        return "\n".join(prompt_parts)
    
    def _parse_generated_response(self, content: str, request: PLCGenerationRequest) -> Dict[str, Any]:
        """Parse the OpenAI response to extract structured information."""
        
        # Extract code blocks
        code_start = content.find("```")
        if code_start != -1:
            code_end = content.find("```", code_start + 3)
            if code_end != -1:
                source_code = content[code_start + 3:code_end].strip()
                
                # Remove language identifier if present
                if source_code.startswith(("st", "plc", "iec")):
                    source_code = "\n".join(source_code.split("\n")[1:])
            else:
                source_code = content[code_start + 3:].strip()
        else:
            source_code = content.strip()
        
        # Extract variable definitions (simplified parsing)
        input_vars = self._extract_variables(source_code, "Input")
        output_vars = self._extract_variables(source_code, "Output")
        
        return {
            "source_code": source_code,
            "input_variables": input_vars,
            "output_variables": output_vars,
            "language": request.language,
            "name": request.name or "GeneratedProgram",
            "description": request.description or "AI-generated PLC program"
        }
    
    def _extract_variables(self, source_code: str, var_type: str) -> Dict[str, Any]:
        """Extract variable definitions from the generated code."""
        # This is a simplified implementation
        # In a production system, you'd want more sophisticated parsing
        variables = {}
        
        lines = source_code.split("\n")
        in_var_section = False
        
        for line in lines:
            line = line.strip()
            if f"(* {var_type}" in line:
                in_var_section = True
                continue
            elif line.startswith("(*") and in_var_section:
                in_var_section = False
                continue
            elif in_var_section and ":" in line and not line.startswith("(*"):
                parts = line.split(":")
                if len(parts) >= 2:
                    var_name = parts[0].strip()
                    var_type_str = parts[1].split(";")[0].strip()
                    variables[var_name] = {"type": var_type_str}
        
        return variables

    async def analyze_document_for_plc_context(self, document: Document) -> Dict[str, Any]:
        """
        Analyze a document to extract PLC-relevant information.
        
        Args:
            document: Document to analyze
            
        Returns:
            Dictionary with extracted PLC context information
        """
        if not document.raw_text:
            return {}
        
        try:
            response = self._safe_chat_create(
                model=ModelConfig.DOCUMENT_ANALYSIS_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert in industrial automation and PLC programming. 
                        Analyze the provided technical document and extract information relevant for PLC programming.
                        
                        Focus on:
                        1. I/O specifications (inputs, outputs, analog/digital)
                        2. Control logic requirements
                        3. Safety requirements
                        4. Operating parameters
                        5. Communication protocols
                        6. Timing requirements
                        
                        Return a structured JSON response with these categories."""
                    },
                    {
                        "role": "user", 
                        "content": f"Document content:\n{document.raw_text[:8000]}"  # Limit content
                    }
                ],
                temperature=0.3,
                max_completion_tokens=1500
            )
            
            content = response.choices[0].message.content
            # In a production system, you'd want to parse this more carefully
            return {"analysis": content, "model_used": ModelConfig.DOCUMENT_ANALYSIS_MODEL}
            
        except Exception as e:
            logger.error("Document analysis failed", error=str(e))
            return {"error": str(e)}

    from typing import Tuple

    async def chat_completion(
        self,
        request,
        retry_on_length: bool = True,
        retry_max_completion_tokens: int = 2048,
        return_raw: bool = False,
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[str, dict]:
        """
        Chat completion with support for both simple prompts and structured messages.

        Args:
            request: Request object with user_prompt, model, temperature, etc.
            retry_on_length: Whether to retry with larger max_tokens if truncated
            retry_max_completion_tokens: Max tokens for retry attempt
            return_raw: Whether to return raw response as third element
            messages: Optional list of messages [{"role": "system/user/assistant", "content": "..."}]
                     If provided, overrides request.user_prompt

        Returns:
            Tuple of (content, usage) or (content, usage, raw_response) if return_raw=True
        """
        model = getattr(request, "model", ModelConfig.CONVERSATION_MODEL) or ModelConfig.CONVERSATION_MODEL

        def _call_with_max(max_tokens_val):
            # Use structured messages if provided, otherwise fall back to simple user prompt
            if messages:
                call_messages = messages
            else:
                call_messages = [{"role": "user", "content": request.user_prompt}]
            
            return self._safe_chat_create(
                model=model,
                messages=call_messages,
                temperature=getattr(request, "temperature", 1.0),
                max_completion_tokens=max_tokens_val,
                request=request,  # Pass request object for conversation_id access
            )

        try:
            # Support both 'max_completion_tokens' and legacy 'max_tokens' on request objects
            initial_max = getattr(request, 'max_completion_tokens', None) or getattr(request, 'max_tokens', None) or 512

            response = _call_with_max(initial_max)

            # Helper to extract content and usage
            def _extract(resp):
                try:
                    content_val = resp.choices[0].message.content
                except Exception:
                    content_val = None
                
                usage_val = getattr(resp, "usage", None)
                # Convert usage object to dictionary for JSON serialization
                if usage_val is not None:
                    try:
                        if hasattr(usage_val, 'model_dump'):
                            usage_val = usage_val.model_dump()
                        elif hasattr(usage_val, 'dict'):
                            usage_val = usage_val.dict()
                        elif hasattr(usage_val, '__dict__'):
                            usage_val = usage_val.__dict__
                    except Exception:
                        usage_val = None
                        
                return content_val, usage_val

            content, usage = _extract(response)

            # Best-effort to inspect the raw response as a dict for decision logic
            parsed_raw = None
            try:
                parsed_raw = response.to_dict()
            except Exception:
                try:
                    parsed_raw = response.json()
                except Exception:
                    parsed_raw = None

            # If the model finished due to length and produced no visible content, optionally retry
            try:
                if (
                    retry_on_length
                    and parsed_raw
                    and parsed_raw.get("choices")
                    and len(parsed_raw.get("choices")) > 0
                ):
                    ch0 = parsed_raw.get("choices")[0]
                    finish = ch0.get("finish_reason")
                    msg = ch0.get("message") or {}
                    content_str = msg.get("content") if isinstance(msg, dict) else None

                    if finish == "length" and (not content_str or len(content_str.strip()) < 10):
                        logger.warning(
                            "chat_completion truncated by max tokens; retrying with larger max",
                            initial_max=initial_max,
                            retry_max=retry_max_completion_tokens,
                        )
                        try:
                            response = _call_with_max(retry_max_completion_tokens)
                            content, usage = _extract(response)
                        except Exception as e:
                            logger.error("Retry after length truncation failed", error=str(e))
            except Exception:
                # Be defensive: don't let diagnostic logic break the normal flow
                pass

            if return_raw:
                return content, usage, response
            else:
                return content, usage

        except OpenAIParameterError:
            # Re-raise parameter errors as-is
            raise
        except Exception as e:
            logger.error("OpenAI chat completion failed", error=str(e))
            raise
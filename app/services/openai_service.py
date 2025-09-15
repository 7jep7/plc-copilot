"""OpenAI service for AI-powered PLC code generation."""

import openai
import structlog
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import re

from app.core.config import settings
from app.models.document import Document
from app.schemas.plc_code import PLCGenerationRequest

logger = structlog.get_logger()

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

    def _safe_chat_create(self, **kwargs):
        """Call chat.completions.create and raise OpenAIParameterError when the
        API reports unsupported parameters or values.
        """
        try:
            return self.client.chat.completions.create(**kwargs)
        except Exception as e:
            msg = str(e)
            # Look for explicit unsupported parameter/value messages
            m = re.search(r"Unsupported (?:parameter|value): '\\'([^\\']+)\\'", msg)
            if not m:
                m = re.search(r"Unsupported (?:parameter|value): '([^']+)'", msg)

            param = m.group(1) if m else None
            # Raise a structured error the API layer can handle
            raise OpenAIParameterError(param=param, message=msg)
    
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
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=request.temperature,
                max_completion_tokens=request.max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # Extract the generated code
            generated_content = response.choices[0].message.content
            
            # Parse the response to extract code and metadata
            result = self._parse_generated_response(generated_content, request)
            
            # Add generation metadata
            # Keep the original request value for backwards compatibility while
            # also indicating the actual parameter passed to the API.
            result["generation_metadata"] = {
                "model": "gpt-4-turbo-preview",
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "max_completion_tokens": request.max_tokens,
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
                model="gpt-4-turbo-preview",
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
            return {"analysis": content, "model_used": "gpt-4-turbo-preview"}
            
        except Exception as e:
            logger.error("Document analysis failed", error=str(e))
            return {"error": str(e)}

    from typing import Tuple

    async def chat_completion(self, request) -> Tuple[str, dict]:
        """
        Simple chat wrapper that sends a single user prompt to the specified model and returns text + usage.
        """
        model = getattr(request, "model", "gpt-5-nano") or "gpt-5-nano"
        try:
            response = self._safe_chat_create(
                model=model,
                messages=[{"role": "user", "content": request.user_prompt}],
                temperature=getattr(request, "temperature", 0.7),
                max_completion_tokens=getattr(request, "max_tokens", 512)
            )

            content = response.choices[0].message.content
            usage = getattr(response, "usage", None)
            return content, usage

        except Exception as e:
            logger.error("chat_completion failed", error=str(e))
            raise
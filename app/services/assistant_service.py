"""
Simplified OpenAI Assistant Service for PLC Copilot.

This service handles interactions with the OpenAI Assistant API using a
configurable assistant ID from environment variables.

The assistant is configured with system instructions and always returns
structured JSON responses according to the plc_response_schema.
"""

import json
import time
import structlog
from typing import Dict, Any, Optional, List
from openai import OpenAI

from app.core.config import settings

logger = structlog.get_logger()


class AssistantService:
    """Simplified service for OpenAI Assistant API interactions."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.assistant_id = settings.OPENAI_ASSISTANT_ID
    
    async def process_message(
        self,
        user_message: str,
        current_context: Optional[Dict[str, Any]] = None,
        file_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message through the OpenAI Assistant.
        
        The assistant will automatically search the configured vector store
        for relevant information from uploaded files.
        
        Args:
            user_message: The user's input message
            current_context: Current project context (device_constants, information)
            file_ids: List of file IDs uploaded to vector store (for reference)
            
        Returns:
            Parsed JSON response from the assistant following plc_response_schema
        """
        try:
            logger.info(f"Processing message with OpenAI Assistant: message_length={len(user_message)}, has_context={current_context is not None}, file_count={len(file_ids) if file_ids else 0}")
            
            # Build the complete message with context and file reference
            complete_message = self._build_complete_message(
                user_message, current_context, file_ids
            )
            
            # Create thread
            thread = self.client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": complete_message
                    }
                ]
            )
            
            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Wait for completion
            response_data = self._wait_for_completion(thread.id, run.id)
            
            logger.info("Assistant response received successfully")
            return response_data
            
        except Exception as e:
            logger.error("Error processing message with assistant", error=str(e))
            # Return fallback response structure
            return self._create_fallback_response(str(e))
    
    def _build_complete_message(
        self,
        user_message: str,
        current_context: Optional[Dict[str, Any]],
        file_ids: Optional[List[str]]
    ) -> str:
        """Build the complete message with context and file reference."""
        
        message_parts = []
        
        # Add current project context if available
        if current_context:
            message_parts.append("## Current Project Context")
            
            if current_context.get("device_constants"):
                message_parts.append("### Device Constants:")
                message_parts.append(json.dumps(current_context["device_constants"], indent=2))
            
            if current_context.get("information"):
                message_parts.append("### Project Information:")
                message_parts.append(current_context["information"])
        
        # Add file reference if files were uploaded
        if file_ids:
            message_parts.append("## Uploaded Files")
            message_parts.append(f"I have uploaded {len(file_ids)} file(s) to the vector store for analysis.")
            message_parts.append("Please analyze these files and extract relevant PLC programming information.")
        
        # Add the user message
        message_parts.append("## User Message")
        message_parts.append(user_message)
        
        return "\n\n".join(message_parts)
    
    def _wait_for_completion(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Wait for the assistant run to complete and return the response."""
        
        max_wait_time = 60  # Maximum wait time in seconds
        poll_interval = 1   # Poll every second
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run_status.status == "completed":
                # Get the response messages
                messages = self.client.beta.threads.messages.list(thread_id=thread_id)
                
                # Get the assistant's response (should be the first message)
                for message in messages.data:
                    if message.role == "assistant":
                        content = message.content[0].text.value
                        return self._parse_assistant_response(content)
                
                raise Exception("No assistant response found in thread")
            
            elif run_status.status in ["failed", "cancelled", "expired"]:
                error_msg = f"Assistant run {run_status.status}"
                if hasattr(run_status, 'last_error') and run_status.last_error:
                    error_msg += f": {run_status.last_error.message}"
                raise Exception(error_msg)
            
            # Continue polling
            time.sleep(poll_interval)
        
        raise Exception(f"Assistant run timed out after {max_wait_time} seconds")
    
    def _parse_assistant_response(self, content: str) -> Dict[str, Any]:
        """Parse the assistant's JSON response."""
        try:
            # The assistant should return valid JSON according to plc_response_schema
            response_data = json.loads(content)
            
            # Validate required fields
            required_fields = [
                "updated_context", "chat_message", "is_mcq", 
                "gathering_requirements_estimated_progress"
            ]
            
            for field in required_fields:
                if field not in response_data:
                    logger.warning(f"Missing required field in assistant response: {field}")
                    response_data[field] = self._get_default_value(field)
            
            # Ensure updated_context has the required structure
            if "updated_context" in response_data:
                context = response_data["updated_context"]
                if "device_constants" not in context:
                    context["device_constants"] = {}
                if "information" not in context:
                    context["information"] = ""
            
            return response_data
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse assistant JSON response", error=str(e), content=content)
            return self._create_fallback_response(f"JSON parsing error: {str(e)}")
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing fields."""
        defaults = {
            "updated_context": {"device_constants": {}, "information": ""},
            "chat_message": "I apologize, but I encountered an error processing your request.",
            "is_mcq": False,
            "mcq_question": None,
            "mcq_options": [],
            "is_multiselect": False,
            "generated_code": None,
            "gathering_requirements_estimated_progress": 0.0
        }
        return defaults.get(field, None)
    
    def _create_fallback_response(self, error_message: str) -> Dict[str, Any]:
        """Create a fallback response when the assistant fails."""
        return {
            "updated_context": {
                "device_constants": {},
                "information": f"Error occurred: {error_message}"
            },
            "chat_message": "I apologize, but I encountered an error processing your request. Please try again.",
            "is_mcq": False,
            "mcq_question": None,
            "mcq_options": [],
            "is_multiselect": False,
            "generated_code": None,
            "gathering_requirements_estimated_progress": 0.0
        }
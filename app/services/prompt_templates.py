"""
Prompt templates for the context service.

Template A: For user messages without files (optimized for direct interaction)
Template B: For user messages with files (optimized for file analysis)
"""

import json
from typing import List, Optional, Dict, Any
from app.schemas.context import ProjectContext, Stage


class PromptTemplates:
    """Manages prompt templates for different interaction scenarios."""
    
    @staticmethod
    def build_template_a_prompt(
        context: ProjectContext,
        stage: Stage,
        user_message: Optional[str],
        mcq_responses: List[str]
    ) -> str:
        """
        Template A: Optimized for user messages without files.
        Focuses on direct user interaction, MCQ responses, and current context.
        """
        # Calculate current progress for requirements gathering
        progress = PromptTemplates._calculate_requirements_progress(context) if stage == Stage.GATHERING_REQUIREMENTS else 0.0
        
        # Stage-specific instructions
        stage_instructions, expected_response_fields = PromptTemplates._get_stage_instructions(stage, progress)
        
        # Prepare device constants for JSON serialization (handle DeviceEntry objects)
        device_constants_dict = {}
        for device_name, device_info in context.device_constants.items():
            if hasattr(device_info, 'model_dump'):  # It's a DeviceEntry
                device_constants_dict[device_name] = device_info.model_dump()
            else:  # It's legacy plain dict
                device_constants_dict[device_name] = device_info
        
        # Check if context is empty (no device constants and no information)
        context_is_empty = not device_constants_dict and not context.information.strip()
        
        # Build user input section
        user_input_section = f"USER INPUT (PRIMARY FOCUS):\nMessage: {user_message or 'No message provided'}"
        if mcq_responses:
            user_input_section += f"\nMCQ Responses: {mcq_responses}"
        
        # Build special handling section (only if context is empty)
        special_handling_section = ""
        if context_is_empty:
            special_handling_section = """
SPECIAL HANDLING FOR OFF-TOPIC REQUESTS:
If the user's message has nothing to do with industrial automation, offer 3 illustrative example automation projects as MCQ options instead of trying to force automation context."""
        
        # Build critical rules (conditional based on context and inputs)
        critical_rules = ["- Focus entirely on user message" + (" and MCQ responses" if mcq_responses else "")]
        if context_is_empty:
            critical_rules.append("- If user input is off-topic: Suggest 3 automation project examples as MCQ")
        critical_rules.extend([
            "- Be GENEROUS with information storage - capture all potentially useful details from user input",
            "- Information should NOT duplicate device constants (those go in device_constants section)",
            "- Reference their input directly in your response",
            "- For each device in device_constants, specify origin as \"user message\" since no files are involved",
            "- Be conversational and responsive to their specific needs",
            "- No file processing needed - file_extractions always empty array"
        ])
        
        return f"""=== DIRECT USER INTERACTION ===

Current Project Context:
Device Constants: {json.dumps(device_constants_dict, indent=2)}
Information: {context.information}

{user_input_section}

{stage_instructions}

TASK: Process the user input directly, update the context based on their message{" and MCQ responses" if mcq_responses else ""}, and provide appropriate response.{special_handling_section}

Return a JSON object with this EXACT structure:
{{
    "updated_context": {{
        "device_constants": {{
            "DeviceName": {{
                "data": {{
                    // Device specifications and properties
                }},
                "origin": "user message"  // Options: "file", "user message", "internet", "internal knowledge base", "other"
            }}
        }},
        "information": "Updated markdown summary - be GENEROUS with information storage. Include ALL relevant details from user input that could be useful throughout the automation project. Store requirements, preferences, constraints, goals, operational details, environmental factors, etc. Do NOT duplicate device constants here."
    }},
    {expected_response_fields}
    "file_extractions": []
}}

CRITICAL RULES:
{chr(10).join(critical_rules)}"""
    
    @staticmethod
    def build_template_b_prompt(
        context: ProjectContext,
        stage: Stage,
        user_message: Optional[str],
        mcq_responses: List[str],
        extracted_file_texts: List[str]
    ) -> str:
        """
        Template B: Optimized for user messages with files.
        Uses current prioritized approach with user input first, files supplementary.
        """
        # Calculate current progress for requirements gathering
        progress = PromptTemplates._calculate_requirements_progress(context) if stage == Stage.GATHERING_REQUIREMENTS else 0.0
        
        # File content section (comes at the end)
        file_content_section = ""
        if extracted_file_texts:
            # Truncate file content but preserve important info (8000 chars)
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
        stage_instructions, expected_response_fields = PromptTemplates._get_stage_instructions(stage, progress)
        
        # Prepare device constants for JSON serialization (handle DeviceEntry objects)
        device_constants_dict = {}
        for device_name, device_info in context.device_constants.items():
            if hasattr(device_info, 'model_dump'):  # It's a DeviceEntry
                device_constants_dict[device_name] = device_info.model_dump()
            else:  # It's legacy plain dict
                device_constants_dict[device_name] = device_info
        
        # Check if context is empty (no device constants and no information)
        context_is_empty = not device_constants_dict and not context.information.strip()
        
        # Build user input section
        user_input_section = f"USER INPUT (CRITICAL - MUST BE REFERENCED):\nMessage: {user_message or 'None'}"
        if mcq_responses:
            user_input_section += f"\nMCQ Responses: {mcq_responses}"
        
        # Build special handling section (only if context is empty)
        special_handling_section = ""
        if context_is_empty:
            special_handling_section = """
SPECIAL HANDLING FOR OFF-TOPIC REQUESTS:
If the user's message has nothing to do with industrial automation, offer 3 illustrative example automation projects as MCQ options instead of trying to force automation context."""
        
        # Build critical rules (conditional based on context and inputs)
        critical_rules = []
        if context_is_empty:
            critical_rules.append("- If user input is off-topic: Suggest 3 automation project examples as MCQ")
        critical_rules.extend([
            "- Be GENEROUS with information storage - capture all potentially useful details from user input and file data",
            "- Information should NOT duplicate device constants (those go in device_constants section)",
            f"- User message{' and MCQ responses' if mcq_responses else ''} are PRIMARY - reference them directly in your response",
            "- Only extract PLC-relevant information from files (devices, I/O, safety, control logic)",
            "- Set origin=\"user message\" for devices from user input, origin=\"file\" for devices from uploaded files",
            "- If no files uploaded, return empty file_extractions array"
        ])
        if mcq_responses:
            critical_rules.append("- For MCQ responses: set is_mcq=true, provide mcq_question and mcq_options")
        
        return f"""=== PRIMARY CONTEXT (MOST IMPORTANT) ===

Current Project Context:
Device Constants: {json.dumps(device_constants_dict, indent=2)}
Information: {context.information}

{user_input_section}

{stage_instructions}

TASK: Process the user input, update the context, extract any file data, and provide appropriate response.{special_handling_section}

Return a JSON object with this EXACT structure:
{{
    "updated_context": {{
        "device_constants": {{
            "DeviceName": {{
                "data": {{
                    // Device specifications and properties  
                }},
                "origin": "user message"  // For user input devices, or "file" for file-extracted devices
            }}
        }},
        "information": "Updated markdown summary - be GENEROUS with information storage. Include ALL relevant details from user input and file data that could be useful throughout the automation project. Store requirements, preferences, constraints, goals, operational details, environmental factors, etc. Do NOT duplicate device constants here."
    }},
    {expected_response_fields}
    "file_extractions": [
        {{
            "extracted_devices": {{
                "DeviceName": {{
                    "data": {{
                        // Device specs extracted from files
                    }},
                    "origin": "file"
                }}
            }},
            "extracted_information": "Brief PLC-relevant summary from files",
            "processing_summary": "One sentence about what was extracted"
        }}
    ]
}}

CRITICAL RULES:
{chr(10).join(critical_rules)}{file_content_section}"""
    
    @staticmethod
    def _get_stage_instructions(stage: Stage, progress: float = 0.0) -> tuple[str, str]:
        """Get stage-specific instructions and expected response fields."""
        
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
        
        else:
            stage_instructions = ""
            expected_response_fields = """
    "chat_message": "Your response",
    "is_mcq": false,
    "mcq_question": null,
    "mcq_options": [],
    "is_multiselect": false,
    "generated_code": null,"""
        
        return stage_instructions, expected_response_fields
    
    @staticmethod
    def _calculate_requirements_progress(context: ProjectContext) -> float:
        """Calculate requirements gathering progress based on context."""
        required_areas = ['safety', 'io', 'control', 'platform', 'communication']
        completed_areas = 0
        
        # Convert device_constants to plain dict for string operations
        device_constants_dict = {}
        for device_name, device_info in context.device_constants.items():
            if hasattr(device_info, 'model_dump'):  # It's a DeviceEntry
                device_constants_dict[device_name] = device_info.model_dump()
            else:  # It's legacy plain dict
                device_constants_dict[device_name] = device_info
        
        device_constants_str = json.dumps(device_constants_dict).lower()
        information_str = context.information.lower()
        
        # Check for safety requirements
        if any(keyword in device_constants_str + information_str for keyword in 
               ['safety', 'emergency', 'stop', 'interlock', 'protection']):
            completed_areas += 1
        
        # Check for I/O specifications
        if any(keyword in device_constants_str + information_str for keyword in 
               ['input', 'output', 'sensor', 'actuator', 'digital', 'analog']):
            completed_areas += 1
        
        # Check for control logic
        if any(keyword in device_constants_str + information_str for keyword in 
               ['control', 'sequence', 'logic', 'operation', 'process']):
            completed_areas += 1
        
        # Check for platform/hardware
        if any(keyword in device_constants_str + information_str for keyword in 
               ['plc', 'platform', 'hardware', 'siemens', 'allen', 'schneider']):
            completed_areas += 1
        
        # Check for communication
        if any(keyword in device_constants_str + information_str for keyword in 
               ['communication', 'protocol', 'modbus', 'ethernet', 'profinet']):
            completed_areas += 1
        
        return completed_areas / len(required_areas)
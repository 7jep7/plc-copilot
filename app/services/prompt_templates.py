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
    def build_empty_context_prompt(
        user_message: Optional[str],
        mcq_responses: List[str],
        previous_copilot_message: Optional[str] = None
    ) -> str:
        """
        Lightweight prompt for completely empty context - optimized for off-topic detection.
        Used when both device_constants and information are empty.
        """
        # Build user input section
        user_input_section = f"USER INPUT:\nMessage: {user_message or 'No message provided'}"
        if mcq_responses:
            user_input_section += f"\nMCQ Responses: {mcq_responses}"
        
        # Add conversation context if available
        conversation_context = ""
        if previous_copilot_message:
            conversation_context = f"\nPREVIOUS CONTEXT: {previous_copilot_message}"
        
        return f"""You are a PLC programming assistant. This is a new project with empty context.

{conversation_context}

{user_input_section}

TASK: Determine if input is automation-related or off-topic:
- IF AUTOMATION-RELATED (conveyor, motor, PLC, sensor, control, automate, automation, manufacturing, industrial, process, system, machine, equipment, safety, start, stop, sequence, monitoring, temperature, pressure): Ask follow-up question and begin requirements gathering
- IF OFF-TOPIC ("hey", "hello", casual chat, unrelated topics): Offer MCQ with 3 automation examples

IMPORTANT: Be generous in recognizing automation intent. Phrases like "automate a conveyor", "control system", "start stop sequence", "monitoring", etc. are clearly automation-related.

For off-topic inputs like "{user_message or 'No message'}", provide these MCQ options:
1. "Conveyor Belt Control System"
2. "Temperature Monitoring & Control" 
3. "Safety System with Emergency Stops"

RESPONSE: Return ONLY valid JSON (no markdown, no extra text):
{{
    "updated_context": {{"device_constants": {{}}, "information": ""}},
    "chat_message": "I'd be happy to help you with industrial automation! What type of project interests you?",
    "is_mcq": true,
    "mcq_question": "What type of automation project interests you?",
    "mcq_options": ["Conveyor Belt Control System", "Temperature Monitoring & Control", "Safety System with Emergency Stops"],
    "is_multiselect": false,
    "generated_code": null,
    "gathering_requirements_estimated_progress": 0.1,
    "file_extractions": []
}}"""
    
    @staticmethod
    def build_template_a_prompt(
        context: ProjectContext,
        stage: Stage,
        user_message: Optional[str],
        mcq_responses: List[str],
        previous_copilot_message: Optional[str] = None
    ) -> str:
        """
        Template A: Optimized for user messages without files.
        Focuses on direct user interaction, MCQ responses, and current context.
        """
        # Stage-specific instructions
        stage_instructions, expected_response_fields = PromptTemplates._get_stage_instructions(stage, context)
        
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
        
        # Add conversation context for better response interpretation
        conversation_context = ""
        if previous_copilot_message:
            conversation_context = f"\nCONVERSATION CONTEXT: Previous copilot message was: {previous_copilot_message}"
        
        # Build special handling section (only if context is empty AND no MCQ responses)
        special_handling_section = ""
        if context_is_empty and not mcq_responses:
            special_handling_section = """
SPECIAL HANDLING FOR OFF-TOPIC REQUESTS:
If the user's message has nothing to do with industrial automation, offer 3 illustrative example automation projects as MCQ options instead of trying to force automation context."""
        
        # Build critical rules (conditional based on context and inputs)
        critical_rules = ["- Focus entirely on user message" + (" and MCQ responses" if mcq_responses else "")]
        if context_is_empty and not mcq_responses:
            critical_rules.append("- If user input is off-topic: Suggest 3 automation project examples as MCQ")
        elif context_is_empty and mcq_responses:
            # Special case: User just selected an automation type from initial MCQ - start requirements gathering
            initial_mcq_options = ["Conveyor Belt Control System", "Temperature Monitoring & Control", "Safety System with Emergency Stops"]
            if any(resp in initial_mcq_options for resp in mcq_responses):
                critical_rules.append("- MCQ response indicates user selected automation type - BEGIN requirements gathering with focused follow-up questions")
                critical_rules.append("- Store the automation type in information and start collecting detailed requirements")
        critical_rules.extend([
            "- ANALYZE EXISTING CONTEXT: Intelligently assess current topic coverage and identify gaps",
            "- ESTIMATE PROGRESS: Provide expert assessment of requirements completion (0.0-1.0)",
            "- Be GENEROUS with information storage using intelligent markdown section structure",
            "- Information should NOT duplicate device constants (those go in device_constants section)",
            "- Reference their input directly and maintain conversation continuity",
            "- Use your expertise to determine next priority topic or completion readiness",
            "- For devices: specify origin as \"user message\" since no files are involved",
            "- Be conversational and responsive to their specific automation needs",
            "- No file processing needed - file_extractions always empty array"
        ])
        
        return f"""You are a PLC programming assistant. Current context:
Device Constants: {json.dumps(device_constants_dict, indent=2)}
Information: {context.information}

{conversation_context}

{user_input_section}

{stage_instructions}

TASK: Analyze context, assess progress, update with structured information, determine next action.{special_handling_section}

RESPONSE: Return ONLY valid JSON (no markdown, no extra text):
{{
    "updated_context": {{
        "device_constants": {{
            "DeviceName": {{
                "data": {{}},
                "origin": "user message"
            }}
        }},
        "information": "Structured markdown summary using stage instructions headers. Capture ALL relevant details."
    }},
    {expected_response_fields}
    "file_extractions": []
}}

RULES: {'; '.join(critical_rules)}"""
    
    @staticmethod
    def build_template_b_prompt(
        context: ProjectContext,
        stage: Stage,
        user_message: Optional[str],
        mcq_responses: List[str],
        extracted_file_texts: List[str],
        previous_copilot_message: Optional[str] = None
    ) -> str:
        """
        Template B: Optimized for user messages with files.
        Uses current prioritized approach with user input first, files supplementary.
        """
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
        stage_instructions, expected_response_fields = PromptTemplates._get_stage_instructions(stage, context)
        
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
        
        # Add conversation context for better response interpretation
        conversation_context = ""
        if previous_copilot_message:
            conversation_context = f"\nCONVERSATION CONTEXT: Previous copilot message was: {previous_copilot_message}"
        
        # Build special handling section (only if context is empty AND no file uploads AND potentially off-topic)
        special_handling_section = ""
        if context_is_empty and not extracted_file_texts:
            special_handling_section = """
SPECIAL HANDLING FOR OFF-TOPIC REQUESTS:
If the user's message has nothing to do with industrial automation, offer 3 illustrative example automation projects as MCQ options instead of trying to force automation context."""
        
        critical_rules = []
        if context_is_empty and not extracted_file_texts:
            critical_rules.append("- If user input is off-topic: Suggest 3 automation project examples as MCQ")
        elif context_is_empty and mcq_responses and not extracted_file_texts:
            # Special case: User just selected an automation type from initial MCQ - start requirements gathering
            initial_mcq_options = ["Conveyor Belt Control System", "Temperature Monitoring & Control", "Safety System with Emergency Stops"]
            if any(resp in initial_mcq_options for resp in mcq_responses):
                critical_rules.append("- MCQ response indicates user selected automation type - BEGIN requirements gathering with focused follow-up questions")
                critical_rules.append("- Store the automation type in information and start collecting detailed requirements")
        critical_rules.extend([
            "- ANALYZE EXISTING CONTEXT: Intelligently assess current topic coverage and identify gaps",
            "- ESTIMATE PROGRESS: Provide expert assessment of requirements completion (0.0-1.0)",
            "- Be GENEROUS with information storage using intelligent markdown section structure",
            "- Information should NOT duplicate device constants (those go in device_constants section)",
            f"- User message{' and MCQ responses' if mcq_responses else ''} are PRIMARY - reference them directly",
            "- Use your expertise to determine next priority topic or completion readiness",
            "- Extract only PLC-relevant information from files (devices, I/O, safety, control logic)",
            "- Set origin=\"user message\" for user devices, origin=\"file\" for file-extracted devices",
            "- If no files uploaded, return empty file_extractions array"
        ])
        
        return f"""You are a PLC programming assistant. Current context:
Device Constants: {json.dumps(device_constants_dict, indent=2)}
Information: {context.information}

{conversation_context}

{user_input_section}

{stage_instructions}

TASK: Analyze context and files, assess progress, update with structured information, extract file data, determine next action.{special_handling_section}

RESPONSE: Return ONLY valid JSON (no markdown, no extra text):
{{
    "updated_context": {{
        "device_constants": {{
            "DeviceName": {{
                "data": {{}},
                "origin": "user message"
            }}
        }},
        "information": "Structured markdown summary. Capture ALL relevant details from user input and files."
    }},
    {expected_response_fields}
    "file_extractions": [
        {{
            "extracted_devices": {{"DeviceName": {{"data": {{}}, "origin": "file"}}}},
            "extracted_information": "Brief PLC-relevant summary from files",
            "processing_summary": "One sentence about what was extracted"
        }}
    ]
}}

RULES: {'; '.join(critical_rules)}{file_content_section}"""
    
    @staticmethod
    def _get_stage_instructions(stage: Stage, context: Optional[ProjectContext] = None) -> tuple[str, str]:
        """Get stage-specific instructions and expected response fields."""
        
        if stage == Stage.GATHERING_REQUIREMENTS:
            stage_instructions = f"""
STAGE: Requirements Gathering - LLM-Driven Intelligence

You are an expert PLC programming consultant conducting focused requirements gathering.
Your task is to analyze the current context (device_constants + information), estimate progress, and help quickly surface the missing details needed to reach code generation.

## INTELLIGENT ANALYSIS REQUIRED
You must analyze the current context to:
1. **ASSESS TOPIC COVERAGE**: Determine which requirement areas are well-covered vs need attention
2. **ESTIMATE PROGRESS**: Provide your expert assessment of overall completion (0.0-1.0)
3. **STRUCTURE INFORMATION**: Use intelligent markdown organization for easy future analysis

NOTE: The frontend controls whether to proceed to code generation based on the returned `gathering_requirements_estimated_progress`. You do not need to explicitly decide the next action — instead, focus on a clear progress estimate and targeted follow-up questions when required.

## CORE REQUIREMENTS AREAS (use these as suggested markdown sections, but you may add or rename topics when appropriate)
### 1. Safety Requirements 
Emergency stops, safety interlocks, protection systems, SIL levels, hazard analysis
### 2. I/O Specifications
Digital/analog inputs/outputs, sensors, actuators, voltage levels, signal types, wiring
### 3. Control Sequence & Logic
Process flow, operational modes, timing requirements, interlocks, state machines
### 4. PLC Platform & Hardware
Brand preference, CPU model, expansion modules, memory, programming software
### 5. Communication Requirements
Network protocols, HMI connectivity, remote access, data exchange, diagnostics

You may propose additional topic sections if they improve clarity or capture project-specific concerns.

## INTELLIGENT MARKDOWN STRUCTURING
Organize the `information` field with clear sections. Be concise but generous in capturing useful details so the gathering stage is efficient and fast.
Aim to minimize the number of turn-backs: prefer MCQs where they help extract standardized choices quickly, but always allow free-text follow-up when nuance is needed.

## CLEAN UX REQUIREMENTS
- **ASK ONLY ONE QUESTION** - Never ask multiple questions in a single response
- **PREFER MCQ OPTIONS** - Use MCQ with 2-4 options whenever possible for faster user interaction
- **KEEP IT FOCUSED** - Ask about the most critical missing piece of information

## INTELLIGENT PROGRESSION STRATEGY
- **ANALYZE EXISTING CONTEXT**: Look at current information to understand what's already covered
- **IDENTIFY GAPS**: Determine which areas need more detail or are completely missing
- **PRIORITIZE FAST EXTRACTION**: Ask high-value questions (safety, I/O, platform) and use MCQs liberally to speed user responses
- **ASK ONE TARGETED QUESTION**: Craft a single specific question or MCQ based on gaps and user's project type
- **MCQ USAGE GUIDANCE**: Use MCQs generously for standardized choices (protocols, voltage, safety categories, common configuration options). Provide multi-select options when appropriate.

## COMPLETION CRITERIA (be reasonably lenient to encourage flow)
Set gathering_requirements_estimated_progress to:
- **0.0-0.3**: Just starting, basic project understanding
- **0.4-0.6**: Core areas identified, some details gathered
- **0.7-0.8**: Most areas covered, refining details
- **0.9**: Nearly complete, final clarifications
- **1.0**: Ready for code generation (substantial coverage achieved)

When you assess 1.0 completion, the frontend will automatically transition to code generation.
"""
            expected_response_fields = """
    "chat_message": "Your expert question or response",
    "is_mcq": null,
    "mcq_question": null,
    "mcq_options": [],
    "is_multiselect": false,
    "generated_code": null,
    "gathering_requirements_estimated_progress": 0.7  // Your expert assessment (0.0-1.0) - set to 1.0 when ready for code generation"""
            
        elif stage == Stage.CODE_GENERATION:
            stage_instructions = """
STAGE: Code Generation

MANDATORY: You MUST always generate Structured Text (ST) code, even if context is minimal or sparse.

## CODE GENERATION RULES:
1. **ALWAYS generate code** - even if it's just a basic ST framework
2. **If context is insufficient** - generate minimal framework code AND ask ONE focused question with MCQ options
3. **Never ask multiple questions** - limit to one question with 2-4 MCQ options
4. **Keep UX clean** - single focused interaction, not multiple follow-ups

## MINIMAL FRAMEWORK CODE (when context is sparse):
Generate at least this basic structure:
```
PROGRAM Main
VAR
    // Basic variable declarations
    start_button : BOOL;
    stop_button : BOOL;
    system_running : BOOL;
END_VAR

// Main control logic
IF start_button AND NOT stop_button THEN
    system_running := TRUE;
ELSIF stop_button THEN
    system_running := FALSE;
END_IF;

END_PROGRAM
```

## COMPLETE CODE (when context is sufficient):
Generate complete, production-ready Structured Text (ST) code including:
- Variable declarations (inputs, outputs, internal variables)
- Function blocks and programs
- Main control logic with safety interlocks
- Error handling and clear comments

Structure: TYPE declarations → PROGRAM → VAR sections → Main logic → Safety/error handling

CRITICAL: The Structured Text code must be properly escaped as a JSON string value.

## WHEN TO ASK ADDITIONAL QUESTIONS:
If you need ONE critical piece of information to enhance the code, ask a single focused question with MCQ options. Examples:
- "What type of system are you controlling?" with options like ["Conveyor System", "Motor Control", "Process Control", "Safety System"]
- "What's your primary control objective?" with options like ["Start/Stop Control", "Speed Control", "Temperature Control", "Safety Monitoring"]
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
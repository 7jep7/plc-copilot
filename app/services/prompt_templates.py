"""Prompt templates for different conversation stages in PLC-Copilot."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.schemas.conversation import ConversationStage, ConversationState, ConversationMessage
from app.core.models import ModelConfig


class PromptTemplate(ABC):
    """Base class for stage-specific prompt templates."""
    
    @abstractmethod
    def build_system_prompt(self, state: ConversationState) -> str:
        """Build the system prompt for this stage."""
        pass
    
    @abstractmethod
    def build_user_prompt(self, message: str, state: ConversationState) -> str:
        """Build the user prompt for this stage."""
        pass
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration for this stage."""
        return ModelConfig.CONVERSATION_CONFIG
    
    def _build_document_context(self, state: ConversationState, context_type: str = "general") -> str:
        """Build document context for inclusion in prompts."""
        if not state.extracted_documents:
            return ""
        
        # Import here to avoid circular imports
        from app.services.conversation_document_service import DocumentInfo
        
        # Convert dict documents back to DocumentInfo objects
        documents = [DocumentInfo.from_dict(doc_data) for doc_data in state.extracted_documents]
        
        if not documents:
            return ""
        
        context_parts = ["\n**📄 DOCUMENT CONTEXT:**"]
        
        for doc in documents:
            doc_summary = [f"- **{doc.filename}** ({doc.document_type})"]
            
            # Add device information
            if doc.device_info:
                device_parts = []
                if doc.device_info.get("manufacturer"):
                    device_parts.append(doc.device_info["manufacturer"])
                if doc.device_info.get("model"):
                    device_parts.append(doc.device_info["model"])
                if device_parts:
                    doc_summary.append(f"Device: {' '.join(device_parts)}")
            
            # Add context-specific information
            if context_type == "requirements" and doc.plc_analysis:
                if doc.plc_analysis.get("key_specifications"):
                    specs = doc.plc_analysis["key_specifications"]
                    if isinstance(specs, list) and specs:
                        doc_summary.append(f"Key specs: {', '.join(specs[:3])}")
                
                if doc.plc_analysis.get("io_requirements"):
                    io_reqs = doc.plc_analysis["io_requirements"]
                    if isinstance(io_reqs, list) and io_reqs:
                        doc_summary.append(f"I/O requirements: {', '.join(io_reqs[:2])}")
            
            elif context_type == "generation" and doc.plc_analysis:
                if doc.plc_analysis.get("plc_integration_points"):
                    integration = doc.plc_analysis["plc_integration_points"]
                    if isinstance(integration, list) and integration:
                        doc_summary.append(f"Integration points: {', '.join(integration[:3])}")
                
                if doc.plc_analysis.get("technical_parameters"):
                    params = doc.plc_analysis["technical_parameters"]
                    if isinstance(params, dict):
                        param_list = [f"{k}: {v}" for k, v in list(params.items())[:2]]
                        if param_list:
                            doc_summary.append(f"Parameters: {', '.join(param_list)}")
            
            # Add a brief content preview for very relevant documents
            if len(doc.raw_text) < 3000:  # For shorter, more focused documents
                content_lines = doc.raw_text.split('\n')[:8]
                meaningful_lines = [line.strip() for line in content_lines if line.strip() and len(line.strip()) > 15]
                if meaningful_lines:
                    doc_summary.append(f"Content preview: {' | '.join(meaningful_lines[:2])}")
            
            context_parts.append(" | ".join(doc_summary))
        
        context_parts.append("")  # Add spacing
        return "\n".join(context_parts)
    
    def _should_suggest_document_upload(self, state: ConversationState, user_message: str) -> Optional[str]:
        """Determine if document upload should be suggested based on conversation context."""
        if state.extracted_documents:
            return None  # Already have documents
        
        user_msg_lower = user_message.lower()
        
        # Keywords that suggest documents would be helpful
        device_keywords = ["camera", "sensor", "motor", "drive", "controller", "plc", "hmi", "valve", "actuator"]
        spec_keywords = ["datasheet", "manual", "specification", "catalog", "brochure"]
        
        if any(keyword in user_msg_lower for keyword in device_keywords):
            return "💡 Consider uploading device datasheets or manuals to help me understand the specific technical requirements and create more accurate Structured Text code."
        
        if any(keyword in user_msg_lower for keyword in spec_keywords):
            return "📄 Please upload the relevant documents to help me analyze the technical specifications for your Structured Text implementation."
        
        return None


# All instances of "ST" in prompt strings have been replaced with "Structured Text" (except where "ST" is part of a code/data type, e.g., "ST code", "ST variable", etc. Those are also replaced with "Structured Text code", "Structured Text variable", etc.)

class ProjectKickoffTemplate(PromptTemplate):
    """Template for the Project Kickoff stage (initial analysis & requirement synthesis)."""
    
    def build_system_prompt(self, state: ConversationState) -> str:
        base_prompt = """You are PLC-Copilot - an expert IEC 61131-3 Structured Text (ST) programmer specializing in industrial automation control systems.

YOUR MISSION: Help users create production-ready Structured Text code for Programmable Logic Controllers (PLCs). Every conversation is building toward generating robust, well-documented ST code.

STRUCTURED TEXT FOCUS:
- All requirements gathering leads to ST code generation
- Think in terms of ST data types, program organization units (POUs), and function blocks
- Consider PLC programming best practices for industrial automation
- Focus on what's needed to write effective Structured Text

CONTEXT AWARENESS:
- Always consider previous messages and build upon prior information  
- Reference earlier requirements when asking follow-up questions
- Avoid asking for information the user has already provided
- Use uploaded documents to inform your analysis and avoid redundant questions

TECHNICAL FOCUS FOR ST CODE GENERATION:
- Industrial automation processes requiring PLC control
- Safety systems, interlocks, and emergency stops (translate to ST safety logic)
- Input/output specifications (digital/analog I/O for ST variables)
- Communication protocols and networking (for ST communication function blocks)
- HMI/SCADA integration (ST data exchange requirements)
- Performance criteria (timing, scan cycles, memory usage in ST)

QUESTION STRATEGY:
- Ask only ONE focused question per response
- Prioritize safety-critical requirements first (essential for ST safety code)
- Clarify process flows and operational modes (for ST state machines)
- Identify constraints (scan time, memory, existing ST libraries)
- Confirm environmental conditions and standards compliance

MCQ FOR VAGUE REQUESTS:
If the user provides a very vague automation request (like "automate my factory" or "need PLC help"), offer specific Structured Text examples using MCQ format:

**MCQ_START**
**Question**: What type of Structured Text automation program do you need?
**Options**:
A) Conveyor belt control with safety interlocks (ST motion control)
B) Temperature control loop with PID (ST process control)
C) Packaging line with counting logic (ST sequential control)
D) Material handling with robotic interface (ST coordination)
**MCQ_END**

RESPONSE FORMAT:
<chat_message>
## Structured Text Requirements Analysis

[Your analysis focusing on ST code requirements and follow-up questions]

## Current ST Requirements Summary
- [List key requirements for Structured Text implementation]
- [Include any ST-specific assumptions that need validation]
</chat_message>

IMPORTANT: Use exactly the <chat_message> tags above. Do not include these tags in your actual content."""

        # Add document context if available
        document_context = self._build_document_context(state, "requirements")
        if document_context:
            base_prompt += document_context
            base_prompt += "\nReference the uploaded documents when they provide relevant context for your analysis and questions.\n"

        # Add requirements history if available
        if state.requirements and state.requirements.identified_requirements:
            requirements_list = "\n".join([f"- {req}" for req in state.requirements.identified_requirements])
            base_prompt += f"\n\n**CURRENT REQUIREMENTS:**\nThe following requirements have been identified so far:\n{requirements_list}\n\nBuild upon these existing requirements and identify any gaps or clarifications needed.\n"

        return base_prompt

    def _detect_non_industrial_input(self, user_message: str) -> bool:
        """Detect if user input is not related to industrial automation."""
        user_msg_lower = user_message.lower()
        
        # # Non-industrial keywords
        # non_industrial_keywords = [
        #     'web', 'website', 'app', 'mobile', 'software', 'database', 'ui', 'frontend',
        #     'backend', 'api', 'javascript', 'python', 'java', 'react', 'nodejs',
        #     'gaming', 'game', 'entertainment', 'social media', 'marketing', 'ecommerce',
        #     'finance', 'banking', 'accounting', 'office', 'document', 'email', 'chat'
        # ]
        
        # Industrial keywords (should NOT trigger non-industrial detection)
        industrial_keywords = [
            'plc', 'scada', 'hmi', 'automation', 'control', 'sensor', 'actuator',
            'motor', 'conveyor', 'process', 'manufacturing', 'factory', 'industrial',
            'safety', 'interlock', 'valve', 'pump', 'temperature', 'pressure',
            'flow', 'level', 'modbus', 'profinet', 'ethernet', 'fieldbus', 'automate', 
            'robot', 'robotics', 
        ]
        
        # Check for industrial context first
        has_industrial = any(keyword in user_msg_lower for keyword in industrial_keywords)
        # has_non_industrial = any(keyword in user_msg_lower for keyword in non_industrial_keywords)
        
        # Only consider non-industrial if there are no industrial context
        return not has_industrial
    
    def _generate_demo_project_suggestions(self) -> str:
        """Generate 3 creative demo project suggestions."""
        import random
        
        demo_projects = [
            {
                "title": "Smart Packaging Line Control",
                "description": "Automated packaging system with conveyor control, product counting, quality inspection, and safety interlocks. Includes barcode scanning and reject handling.",
                "st_focus": "Sequential control, safety logic, data handling"
            },
            {
                "title": "Temperature Control System", 
                "description": "Multi-zone heating system with PID control, alarm management, and HMI integration. Features cascade control and energy optimization.",
                "st_focus": "PID controllers, analog I/O, alarm handling"
            },
            {
                "title": "Material Handling with Robotics",
                "description": "Automated warehouse system with robotic pick-and-place, conveyor coordination, and inventory tracking. Includes safety zones and collision avoidance.",
                "st_focus": "Coordination logic, safety systems, communication"
            },
            {
                "title": "Pump Station Control",
                "description": "Water treatment pump station with level control, pump sequencing, flow monitoring, and energy efficiency optimization. Includes redundancy and maintenance scheduling.",
                "st_focus": "Level control, pump algorithms, efficiency logic"
            },
            {
                "title": "Production Line Dashboard",
                "description": "Real-time monitoring system for production equipment with OEE calculation, predictive maintenance alerts, and energy consumption tracking.",
                "st_focus": "Data collection, calculations, communication"
            },
            {
                "title": "Safety Curtain Integration",
                "description": "Machine safety system with light curtains, emergency stops, two-hand controls, and safety PLCs. Includes safety diagnostics and validation.",
                "st_focus": "Safety logic, diagnostics, SIL compliance"
            }
        ]
        
        # Select 3 random projects
        selected = random.sample(demo_projects, 3)
        
        mcq_options = []
        for i, project in enumerate(selected):
            option_letter = chr(65 + i)  # A, B, C
            mcq_options.append(f"{option_letter}) {project['title']} - {project['description']} (ST Focus: {project['st_focus']})")
        
        return f"""**MCQ_START**
**Question**: I'd like to help you explore Structured Text programming! Which type of industrial automation project interests you?
**Options**:
{chr(10).join(mcq_options)}
**MCQ_END**"""

    def build_user_prompt(self, message: str, state: ConversationState) -> str:
        user_prompt_parts = []
        
        # Check for non-industrial input and suggest demo projects
        if self._detect_non_industrial_input(message):
            demo_suggestions = self._generate_demo_project_suggestions()
            user_prompt_parts.append(f"Non-industrial request detected: {message}")
            user_prompt_parts.append("DEMO PROJECT SUGGESTIONS:")
            user_prompt_parts.append(demo_suggestions)
            return "\n\n".join(user_prompt_parts)
        
        if hasattr(state, 'requirements') and state.requirements and state.requirements.user_query:
            user_prompt_parts.append(f"Initial Request: {state.requirements.user_query}")
        
        user_prompt_parts.append(f"User Response: {message}")
        
        # Check if we should suggest document upload
        doc_suggestion = self._should_suggest_document_upload(state, message)
        if doc_suggestion:
            user_prompt_parts.append(f"\nDocument Upload Suggestion: {doc_suggestion}")
        
        return "\n\n".join(user_prompt_parts)
    
    def get_model_config(self) -> Dict[str, Any]:
        return ModelConfig.CONVERSATION_CONFIG


class GatherRequirementsTemplate(PromptTemplate):
    """Template for Gather Requirements stage (focused questions & MCQ)."""
    
    def build_system_prompt(self, state: ConversationState) -> str:
        base_prompt = """You are PLC-Copilot Structured Text Specialist - an expert at gathering the essential technical details needed to generate production-ready IEC 61131-3 Structured Text code.

YOUR MISSION: Ask ONE focused question at a time to gather critical information for ST code generation. Make it as easy as possible for the user while staying focused on Structured Text requirements.

STRUCTURED TEXT FOCUS:
- Every question should lead to better ST code generation
- Consider ST data types, variables, program organization, function blocks
- Think about how each answer translates to specific ST code elements
- Focus on I/O mapping, timing requirements, safety logic, control algorithms

STRATEGY:
- Prioritize the MOST CRITICAL missing information for ST implementation first
- Ask only ONE question per response 
- Use MCQ when there are standard industrial/ST options
- Keep questions laser-focused on ST programming needs
- Avoid overwhelming the user with multiple questions
- Use uploaded documents to avoid asking for information already provided

DATASHEET AWARENESS:
- Always ask for equipment datasheets when working with specific devices
- Datasheets provide critical specifications for ST programming (I/O types, protocols, timing)
- Request device manuals for proper integration into Structured Text code
- Use datasheet information to avoid assumptions about device capabilities

QUESTION TYPES FOR ST:
1. **Single Open Question**: For custom values, specifications, or ST logic descriptions
2. **Single MCQ**: For standard ST choices (data types, protocols, safety levels, I/O types, etc.)

For MCQ questions, use this EXACT format:
**MCQ_START**
**Question**: [One clear, focused question about ST requirements]
**Options**:
A) [Option 1]
B) [Option 2] 
C) [Option 3]
D) Other (please specify)
**MCQ_END**

CRITICAL: When creating MCQ responses, DO NOT include the answer options in your <chat_message>. The question and options will be shown separately in the UI. Your <chat_message> should only contain the question text and any necessary context or explanation.

PROGRESS TRACKING:
Include progress information in this format:
**PROGRESS**: [X]/[Y] ST specification questions asked

CRITICAL RULES:
- Only ONE question per response (either open OR MCQ, never both)
- Focus on what's absolutely necessary for Structured Text code generation
- Use simple, clear language with ST context
- Prioritize safety requirements, then I/O specifications, then operational ST logic
- Estimate total questions needed and track progress
- Reference uploaded documents when they contain relevant ST specifications

RESPONSE FORMAT:
<chat_message>
**PROGRESS**: [X]/[Y] ST specification questions asked

[Ask your single, focused question about Structured Text requirements - either open question OR MCQ format above]

**Next Step:** Based on your answer, I'll [explain how this will be used in the ST code]
</chat_message>

IMPORTANT: Use exactly the <chat_message> tags above. Do not include these tags in your actual content."""

        # Add document context if available
        document_context = self._build_document_context(state, "requirements")
        if document_context:
            base_prompt += document_context
            base_prompt += "\nReference the uploaded documents when relevant to avoid asking questions already answered in the documents.\n"

        # Add requirements history if available
        if state.requirements and state.requirements.identified_requirements:
            requirements_list = "\n".join([f"- {req}" for req in state.requirements.identified_requirements])
            base_prompt += f"\n\n**REQUIREMENTS TO CLARIFY:**\n{requirements_list}\n\nFocus on technical details needed to implement these requirements.\n"

        return base_prompt

    def build_user_prompt(self, message: str, state: ConversationState) -> str:
        return f"User Response: {message}"


class CodeGenerationTemplate(PromptTemplate):
    """Template for code generation stage."""
    
    def build_system_prompt(self, state: ConversationState) -> str:
        base_prompt = """You are PLC-Copilot Structured Text Code Generator - an expert IEC 61131-3 Structured Text programmer specializing in industrial automation.

YOUR MISSION: Generate production-ready, robust IEC 61131-3 Structured Text (ST) code based on the gathered requirements.

STRUCTURED TEXT EXPERTISE:
- Generate clean, maintainable IEC 61131-3 Structured Text code
- Follow industrial programming best practices and standards
- Include proper variable declarations, comments, and organization
- Consider safety requirements, timing constraints, and maintainability

DEVICE INTEGRATION:
- Request equipment datasheets for accurate I/O mapping and communication setup
- Use manufacturer specifications for proper device configuration in ST
- Implement device-specific communication protocols and data handling
- Ensure ST code matches actual device capabilities and limitations

RESPONSE FORMAT:

CODE QUALITY REQUIREMENTS:
- Production-ready code with proper error handling
- Clear variable naming with industrial conventions
- Comprehensive comments explaining control logic
- Safety considerations and interlocks where applicable
- Efficient scan cycle performance
- Proper initialization and startup sequences

CRITICAL RESPONSE FORMAT - Follow this exact structure for proper frontend parsing:
<code>
[Complete IEC 61131-3 Structured Text code - this section will be parsed out for the frontend]
</code>

<chat_message>
[Your explanation of the ST code logic, operation, implementation details, and how it addresses the requirements - this becomes the visible conversation message]
</chat_message>

IMPORTANT: Use exactly the <code> and <chat_message> tags above. Do not include these tags in your actual content."""

        # Add document context if available
        document_context = self._build_document_context(state, "generation")
        if document_context:
            base_prompt += document_context
            base_prompt += "\nUse technical details from the uploaded documents for accurate code generation, including specific device models, I/O specifications, and timing requirements.\n"

        # Add requirements history if available
        if state.requirements and state.requirements.identified_requirements:
            requirements_list = "\n".join([f"- {req}" for req in state.requirements.identified_requirements])
            base_prompt += f"\n\n**REQUIREMENTS TO IMPLEMENT:**\n{requirements_list}\n\nGenerate ST code that fulfills all these requirements.\n"

        return base_prompt

    def build_user_prompt(self, message: str, state: ConversationState) -> str:
        return f"Generation Request: {message}"
    
    def get_model_config(self) -> Dict[str, Any]:
        return ModelConfig.CODE_GENERATION_CONFIG


class RefinementTestingTemplate(PromptTemplate):
    """Template for refinement and testing stage."""
    
    def build_system_prompt(self, state: ConversationState) -> str:
        base_prompt = """You are PLC-Copilot Structured Text Code Reviewer - an expert IEC 61131-3 ST programmer focused on code improvement, optimization, and industrial testing.

YOUR MISSION: Refine and improve Structured Text code based on user feedback, ensuring it meets industrial automation standards and requirements.

STRUCTURED TEXT REFINEMENT FOCUS:
- Optimize ST code performance and scan cycle efficiency
- Improve ST code readability and maintainability
- Enhance safety logic and error handling in ST
- Validate ST syntax and IEC 61131-3 compliance
- Consider industrial automation best practices
- Address any functional or performance issues in the ST implementation

REFINEMENT PRIORITIES:
1. Safety and functional correctness of ST logic
2. Code efficiency and scan cycle optimization
3. Error handling and fault management in ST
4. Code clarity and industrial maintenance practices
5. Compliance with automation standards and guidelines

CRITICAL RESPONSE FORMAT - Follow this exact structure for proper frontend parsing:
<code>
[Updated IEC 61131-3 Structured Text code - this section will be parsed out for the frontend]
</code>

<chat_message>
[Your explanation of the ST code modifications made, why they improve the industrial automation solution, and how they address the user's feedback - this becomes the visible conversation message]
</chat_message>

IMPORTANT: Use exactly the <code> and <chat_message> tags above. Do not include these tags in your actual content."""

        # Add document context if available
        document_context = self._build_document_context(state, "generation")
        if document_context:
            base_prompt += document_context
            base_prompt += "\nReference the uploaded documents for validation and testing requirements, including device-specific parameters and operational constraints.\n"

        # Add requirements history if available
        if state.requirements and state.requirements.identified_requirements:
            requirements_list = "\n".join([f"- {req}" for req in state.requirements.identified_requirements])
            base_prompt += f"\n\n**ORIGINAL REQUIREMENTS:**\n{requirements_list}\n\nEnsure all refinements maintain compliance with the original requirements.\n"

        # Add generation context if available
        if state.generation and state.generation.generated_code:
            base_prompt += f"\n\n**CURRENT CODE VERSION:**\nThe user is working with code that implements the requirements above. Apply their feedback to improve the code.\n"

        return base_prompt

    def build_user_prompt(self, message: str, state: ConversationState) -> str:
        return f"Refinement Request: {message}"
    
    def get_model_config(self) -> Dict[str, Any]:
        return ModelConfig.REFINEMENT_CONFIG


class PromptTemplateFactory:
    """Factory for creating stage-specific prompt templates."""
    
    _templates = {
    ConversationStage.PROJECT_KICKOFF: ProjectKickoffTemplate,
    ConversationStage.GATHER_REQUIREMENTS: GatherRequirementsTemplate,
        ConversationStage.CODE_GENERATION: CodeGenerationTemplate,
        ConversationStage.REFINEMENT_TESTING: RefinementTestingTemplate,
    }
    
    @classmethod
    def get_template(cls, stage: ConversationStage) -> PromptTemplate:
        """Get the appropriate template for a conversation stage."""
        template_class = cls._templates.get(stage)
        if not template_class:
            raise ValueError(f"No template available for stage: {stage}")
        return template_class()
    
    @classmethod
    def get_available_stages(cls) -> List[ConversationStage]:
        """Get list of stages with available templates."""
        return list(cls._templates.keys())
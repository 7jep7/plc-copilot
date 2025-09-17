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
        spec_keywords = ["specification", "datasheet", "manual", "catalog", "model", "part number"]
        
        has_device = any(keyword in user_msg_lower for keyword in device_keywords)
        has_spec_request = any(keyword in user_msg_lower for keyword in spec_keywords)
        
        if has_device or has_spec_request:
            return ("If you have datasheets, manuals, or technical specifications for your devices, "
                   "uploading them can help me provide more accurate requirements and code generation.")
        
        return None


class ProjectKickoffTemplate(PromptTemplate):
    """Template for the Project Kickoff stage (initial analysis & requirement synthesis)."""
    
    def build_system_prompt(self, state: ConversationState) -> str:
        base_prompt = """You are PLC-Copilot Requirements Analyst - an expert Programmable Logic Controller (PLC) systems engineer specializing in requirements gathering for industrial automation projects.

Your role is to conduct thorough requirements analysis by asking strategic questions to fully understand the user's automation needs. You help users define clear, comprehensive requirements for PLC-based control systems.

CONTEXT AWARENESS:
- Always consider previous messages and build upon prior information
- Reference earlier requirements when asking follow-up questions
- Avoid asking for information the user has already provided
- Use uploaded documents to inform your analysis and avoid redundant questions

TECHNICAL FOCUS:
- Industrial automation processes and control requirements
- Safety systems, interlocks, and emergency stops
- Input/output specifications (digital, analog sensors/actuators)
- Communication protocols and networking needs
- HMI/SCADA integration requirements
- Performance criteria (timing, precision, throughput)

QUESTION STRATEGY:
- Ask only ONE focused question per response
- Prioritize safety-critical requirements first
- Clarify process flows and operational modes
- Identify constraints (budget, timeline, existing equipment)
- Confirm environmental conditions and standards compliance

MCQ FOR VAGUE REQUESTS:
If the user provides a very vague automation request (like "automate my factory" or "need PLC help"), offer specific examples using MCQ format:

**MCQ_START**
**Question**: What type of automation project are you looking to implement?
**Options**:
A) Conveyor belt sorting system with safety interlocks
B) Temperature control for manufacturing process
C) Packaging line with count and quality control
D) Material handling with robotic integration
**MCQ_END**

RESPONSE FORMAT:
<chat_message>
## Requirements Analysis

[Your analysis and follow-up questions]

## Current Requirements Summary
- [List key requirements identified so far]
- [Include any assumptions that need validation]
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

    def build_user_prompt(self, message: str, state: ConversationState) -> str:
        user_prompt_parts = []
        
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
        base_prompt = """You are PLC-Copilot Requirements Specialist - an expert at gathering just the essential information needed for PLC code generation.

YOUR MISSION: Ask ONE focused question at a time to gather critical missing information for PLC programming. Make it as easy as possible for the user.

STRATEGY:
- Prioritize the MOST CRITICAL missing information first
- Ask only ONE question per response 
- Use MCQ when there are standard industry options
- Keep questions laser-focused and easy to understand
- Avoid overwhelming the user with multiple questions
- Use uploaded documents to avoid asking for information already provided

QUESTION TYPES:
1. **Single Open Question**: For custom values, descriptions, or specifications
2. **Single MCQ**: For standard industry choices (safety levels, voltages, protocols, etc.)

For MCQ questions, use this EXACT format:
**MCQ_START**
**Question**: [One clear, focused question]
**Options**:
A) [Option 1]
B) [Option 2] 
C) [Option 3]
D) Other (please specify)
**MCQ_END**

PROGRESS TRACKING:
Include progress information in this format:
**PROGRESS**: [X]/[Y] scoping questions asked

CRITICAL RULES:
- Only ONE question per response (either open OR MCQ, never both)
- Focus on what's absolutely necessary for code generation
- Use simple, clear language
- Prioritize safety requirements, then I/O, then operational details
- Estimate total questions needed and track progress
- Reference uploaded documents when they contain relevant answers

RESPONSE FORMAT:
<chat_message>
**PROGRESS**: [X]/[Y] scoping questions asked

[Ask your single, focused question - either open question OR MCQ format above]

**Next Step:** Based on your answer, I'll [explain what you'll do with this information]
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
        base_prompt = """You are PLC-Copilot Code Generator - an expert IEC 61131-3 Structured Text programmer.

Generate production-ready Structured Text (ST) code based on requirements.

CRITICAL RESPONSE FORMAT - Follow this exact structure for proper frontend parsing:
<code>
[Full ST code in structured text format - this section will be parsed out for the frontend]
</code>

<chat_message>
[Your explanation of the code logic, operation, and implementation details - this becomes the visible conversation message]
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
        base_prompt = """You are PLC-Copilot Code Reviewer - an expert focused on code improvement and testing.

Help users refine and improve generated PLC code based on feedback.

CRITICAL RESPONSE FORMAT - Follow this exact structure for proper frontend parsing:
<code>
[Updated ST code in structured text format - this section will be parsed out for the frontend]
</code>

<chat_message>
[Your explanation of the modifications made and why they improve the code - this becomes the visible conversation message]
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
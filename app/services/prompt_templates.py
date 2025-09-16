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


class RequirementsGatheringTemplate(PromptTemplate):
    """Template for requirements gathering stage."""
    
    def build_system_prompt(self, state: ConversationState) -> str:
        base_prompt = """You are PLC-Copilot Requirements Analyst - an expert Programmable Logic Controller (PLC) systems engineer specializing in requirements gathering for industrial automation projects.

Your role is to conduct thorough requirements analysis by asking strategic questions to fully understand the user's automation needs. You help users define clear, comprehensive requirements for PLC-based control systems.

CONTEXT AWARENESS:
- Always consider previous messages and build upon prior information
- Reference earlier requirements when asking follow-up questions
- Avoid asking for information the user has already provided

TECHNICAL FOCUS:
- Industrial automation processes and control requirements
- Safety systems, interlocks, and emergency stops
- Input/output specifications (digital, analog sensors/actuators)
- Communication protocols and networking needs
- HMI/SCADA integration requirements
- Performance criteria (timing, precision, throughput)

QUESTION STRATEGY:
- Ask 1-3 focused questions per response
- Prioritize safety-critical requirements first
- Clarify process flows and operational modes
- Identify constraints (budget, timeline, existing equipment)
- Confirm environmental conditions and standards compliance

RESPONSE FORMAT:
## Requirements Analysis

[Your analysis and follow-up questions]

## Current Requirements Summary
- [List key requirements identified so far]
- [Include any assumptions that need validation]
"""

        # Add document context if available
        if state.document_ids:
            doc_count = len(state.document_ids)
            base_prompt += f"\n\nDOCUMENT CONTEXT:\nYou have access to {doc_count} uploaded document(s) that may contain relevant technical specifications, drawings, or requirements. Reference these documents when they provide relevant context for your questions.\n"

        # Add requirements history if available
        if state.requirements and state.requirements.identified_requirements:
            requirements_list = "\n".join([f"- {req}" for req in state.requirements.identified_requirements])
            base_prompt += f"\n\nCURRENT REQUIREMENTS:\nThe following requirements have been identified so far:\n{requirements_list}\n\nBuild upon these existing requirements and identify any gaps or clarifications needed.\n"

        return base_prompt

    def build_user_prompt(self, message: str, state: ConversationState) -> str:
        if hasattr(state, 'requirements') and state.requirements and state.requirements.user_query:
            return f"Initial Request: {state.requirements.user_query}\n\nUser Response: {message}"
        return f"User Message: {message}"
    
    def get_model_config(self) -> Dict[str, Any]:
        return ModelConfig.CONVERSATION_CONFIG


class QAClarificationTemplate(PromptTemplate):
    """Template for Q&A clarification stage."""
    
    def build_system_prompt(self, state: ConversationState) -> str:
        base_prompt = """You are PLC-Copilot Technical Interviewer - an expert PLC engineer conducting technical clarification interviews.

Your role is to ask precise technical questions to clarify ambiguous requirements and gather missing details needed for PLC code generation.

CLARIFICATION FOCUS:
- Technical specifications and performance criteria
- Edge cases and fault handling
- Integration with existing systems
- Specific PLC programming requirements

QUESTION TYPES:
1. **Open Questions**: When you need detailed explanations or custom values
2. **Multiple Choice Questions (MCQ)**: When there are standard options to choose from

For MCQ questions, format them as:
**Question**: [Your question here]
**Options**:
A) [Option 1]
B) [Option 2]
C) [Option 3]
D) Other (please specify)

RESPONSE FORMAT:
## Technical Clarification

[Your focused questions and clarifications - mix of open questions and MCQ as appropriate]

**Follow-up Actions:**
- [What you'll do with the answers]
"""

        # Add document context if available
        if state.document_ids:
            doc_count = len(state.document_ids)
            base_prompt += f"\n\nDOCUMENT CONTEXT:\nReference the {doc_count} uploaded document(s) for technical details when asking clarification questions.\n"

        # Add requirements history if available
        if state.requirements and state.requirements.identified_requirements:
            requirements_list = "\n".join([f"- {req}" for req in state.requirements.identified_requirements])
            base_prompt += f"\n\nREQUIREMENTS TO CLARIFY:\n{requirements_list}\n\nFocus on technical details needed to implement these requirements.\n"

        return base_prompt

    def build_user_prompt(self, message: str, state: ConversationState) -> str:
        return f"User Response: {message}"


class CodeGenerationTemplate(PromptTemplate):
    """Template for code generation stage."""
    
    def build_system_prompt(self, state: ConversationState) -> str:
        base_prompt = """You are PLC-Copilot Code Generator - an expert IEC 61131-3 Structured Text programmer.

Generate production-ready Structured Text (ST) code based on requirements.

RESPONSE FORMAT:
## Generated PLC Code

### Structured Text Code
[Full ST code here in structured text format]

### Explanation
[Detailed explanation of the logic and operation]
"""

        # Add document context if available
        if state.document_ids:
            doc_count = len(state.document_ids)
            base_prompt += f"\n\nDOCUMENT CONTEXT:\nUse technical details from the {doc_count} uploaded document(s) for accurate code generation.\n"

        # Add requirements history if available
        if state.requirements and state.requirements.identified_requirements:
            requirements_list = "\n".join([f"- {req}" for req in state.requirements.identified_requirements])
            base_prompt += f"\n\nREQUIREMENTS TO IMPLEMENT:\n{requirements_list}\n\nGenerate ST code that fulfills all these requirements.\n"

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

RESPONSE FORMAT:
## Code Refinement

### Modified Code
[Updated ST code in structured text format]

### Change Explanation
[Explanation of modifications]
"""

        # Add document context if available
        if state.document_ids:
            doc_count = len(state.document_ids)
            base_prompt += f"\n\nDOCUMENT CONTEXT:\nReference the {doc_count} uploaded document(s) for validation and testing requirements.\n"

        # Add requirements history if available
        if state.requirements and state.requirements.identified_requirements:
            requirements_list = "\n".join([f"- {req}" for req in state.requirements.identified_requirements])
            base_prompt += f"\n\nREQUIREMENTS TO VALIDATE:\n{requirements_list}\n\nEnsure all refinements maintain compliance with these requirements.\n"

        return base_prompt

    def build_user_prompt(self, message: str, state: ConversationState) -> str:
        return f"Refinement Request: {message}"
    
    def get_model_config(self) -> Dict[str, Any]:
        return ModelConfig.REFINEMENT_CONFIG


class PromptTemplateFactory:
    """Factory for creating stage-specific prompt templates."""
    
    _templates = {
        ConversationStage.PROJECT_KICKOFF: RequirementsGatheringTemplate,
        ConversationStage.GATHER_REQUIREMENTS: QAClarificationTemplate,
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
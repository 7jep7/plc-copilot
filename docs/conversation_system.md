# PLC-Copilot Multi-Stage Conversation System

## Overview

This system implements a robust, modular architecture for multi-stage conversations with the PLC-Copilot, supporting intelligent stage detection, dynamic prompt generation, and conversation state management.

## Architecture Components

### 1. Conversation Stages (`app/schemas/conversation.py`)

- **REQUIREMENTS_GATHERING**: Initial user query analysis and requirement identification
- **QA_CLARIFICATION**: Technical Q&A to fill information gaps
- **CODE_GENERATION**: Structured Text (ST) PLC code generation
- **REFINEMENT_TESTING**: Code refinement, testing, and optimization

### 2. Stage Detection Service (`app/services/stage_detection_service.py`)

- Uses lightweight LLM (gpt-5-nano) for low-latency stage classification
- Analyzes conversation context to suggest appropriate stage transitions
- Validates transitions using predefined rules
- Returns confidence scores and reasoning

### 3. Prompt Templates (`app/services/prompt_templates.py`)

**Modular, stage-specific prompt templates:**

- `RequirementsGatheringTemplate`: Systematic requirement analysis
- `QAClarificationTemplate`: Technical interview approach
- `CodeGenerationTemplate`: Production-ready ST code generation
- `RefinementTestingTemplate`: Code review and improvement

**Easy customization:**
```python
template = PromptTemplateFactory.get_template(ConversationStage.CODE_GENERATION)
system_prompt = template.build_system_prompt(conversation_state)
```

### 4. Conversation Orchestrator (`app/services/conversation_orchestrator.py`)

**Central coordination:**
- Manages conversation state and transitions
- Coordinates stage detection and prompt generation
- Handles message processing and response generation
- Maintains conversation history and context

### 5. API Endpoints (`app/api/api_v1/endpoints/conversations.py`)

**RESTful API:**
- `POST /conversations` - Start/continue conversation
- `GET /conversations/{id}` - Get conversation state
- `POST /conversations/{id}/stage` - Manual stage transition
- `GET /conversations/{id}/stage/suggestions` - Get stage suggestions

### 6. Database Models (`app/models/conversation.py`)

**Persistent storage:**
- `Conversation`: Main conversation state and metadata
- `ConversationMessage`: Individual messages with timestamps
- `ConversationTemplate`: Customizable prompt templates
- `ConversationMetrics`: Analytics and performance tracking

## Usage Examples

### Basic Conversation Flow

```python
from app.services.conversation_orchestrator import ConversationOrchestrator
from app.schemas.conversation import ConversationRequest

orchestrator = ConversationOrchestrator()

# Start conversation
request = ConversationRequest(
    message="I need to control a motor with safety interlocks"
)
response = await orchestrator.process_message(request)

# Continue conversation
request = ConversationRequest(
    conversation_id=response.conversation_id,
    message="The motor is 3-phase, 480V, with thermal overload protection"
)
response = await orchestrator.process_message(request)
```

### API Usage

```bash
# Start new conversation
curl -X POST "http://localhost:8000/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{"message": "I need PLC code for a conveyor system"}'

# Continue conversation
curl -X POST "http://localhost:8000/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "message": "Add emergency stop functionality"
  }'

# Get conversation state
curl "http://localhost:8000/api/v1/conversations/123e4567-e89b-12d3-a456-426614174000"
```

### Custom Prompt Templates

```python
class CustomGenerationTemplate(PromptTemplate):
    def build_system_prompt(self, state: ConversationState) -> str:
        return """Custom system prompt for specialized PLC generation..."""
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model": "gpt-4",
            "temperature": 0.1,
            "max_completion_tokens": 2048
        }

# Register custom template
PromptTemplateFactory._templates[ConversationStage.CODE_GENERATION] = CustomGenerationTemplate
```

## Configuration

### Environment Variables

```bash
OPENAI_API_KEY=your_openai_key
DATABASE_URL=postgresql://user:pass@localhost/plc_copilot
```

### Model Configuration

Default model settings per stage:
- **Stage Detection**: gpt-5-nano (fast, low-cost)
- **Requirements**: gpt-4 (temperature=0.3)
- **Code Generation**: gpt-4 (temperature=0.2)
- **Refinement**: gpt-4 (temperature=0.1)

## Testing

### Run Demo Script

```bash
PYTHONPATH=/path/to/plc-copilot python scripts/demo_conversation_system.py
```

### Unit Tests

```bash
pytest tests/test_conversation_system.py
```

## Production Considerations

### 1. Database Setup

Run database migrations:
```bash
alembic upgrade head
```

### 2. Caching and Performance

- Implement Redis for conversation state caching
- Use connection pooling for database access
- Cache prompt templates for performance

### 3. Monitoring

- Track conversation metrics (stage progression, completion rates)
- Monitor LLM token usage and costs
- Log stage transition decisions for analysis

### 4. Security

- Implement user authentication and authorization
- Validate and sanitize all user inputs
- Rate limiting for API endpoints

## Customization Points

### Easy Prompt Engineering

1. **Edit templates** in `app/services/prompt_templates.py`
2. **Adjust stage detection** in `app/services/stage_detection_service.py`
3. **Modify transition rules** in `StageTransitionRules` class
4. **Add new stages** by extending `ConversationStage` enum

### Model Selection

Change models per stage in template `get_model_config()` methods:
```python
def get_model_config(self) -> Dict[str, Any]:
    return {
        "model": "gpt-4-turbo",  # or "claude-3", "gpt-5"
        "temperature": 0.2,
        "max_completion_tokens": 1024
    }
```

### Custom Business Logic

Override orchestrator methods:
```python
class CustomOrchestrator(ConversationOrchestrator):
    async def _process_stage_message(self, conversation, message):
        # Custom processing logic
        return await super()._process_stage_message(conversation, message)
```

## Future Enhancements

1. **Multi-language support** for international users
2. **Voice interface** integration
3. **Real-time collaboration** for team projects
4. **Integration with PLC IDEs** and simulators
5. **Advanced analytics** and conversation insights
6. **Template marketplace** for specialized use cases
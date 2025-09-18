"""Services package initialization."""

from app.services.document_service import DocumentService
from app.services.plc_service import PLCService
from app.services.digital_twin_service import DigitalTwinService
from app.services.openai_service import OpenAIService
from app.services.simplified_context_service import SimplifiedContextService

# Global singleton instance for session management
_context_service_instance = None

def get_context_service() -> SimplifiedContextService:
    """Get the singleton context service instance."""
    global _context_service_instance
    if _context_service_instance is None:
        _context_service_instance = SimplifiedContextService()
    return _context_service_instance

__all__ = [
    "DocumentService",
    "PLCService", 
    "DigitalTwinService",
    "OpenAIService",
    "SimplifiedContextService",
    "get_context_service",
]
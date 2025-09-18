"""Services package initialization."""

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
    "SimplifiedContextService",
    "get_context_service",
]
"""Document model for storing uploaded PDF manuals."""

from sqlalchemy import Column, String, Text, Integer, LargeBinary
from sqlalchemy.dialects.postgresql import JSONB
from enum import Enum

from app.models.base import BaseModel


class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class DocumentType(str, Enum):
    """Document type classification."""
    MANUAL = "manual"
    DATASHEET = "datasheet"
    SPECIFICATION = "specification"
    UNKNOWN = "unknown"


class Document(BaseModel):
    """Model for storing uploaded industrial device manuals and datasheets."""
    
    __tablename__ = "documents"
    
    # Basic file information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=False)
    
    # Document classification
    document_type = Column(String(50), default=DocumentType.UNKNOWN.value)
    manufacturer = Column(String(100), nullable=True)
    device_model = Column(String(100), nullable=True)
    device_series = Column(String(100), nullable=True)
    
    # Processing status
    status = Column(String(20), default=DocumentStatus.UPLOADED.value)
    processing_error = Column(Text, nullable=True)
    
    # Extracted content
    raw_text = Column(Text, nullable=True)
    structured_data = Column(JSONB, nullable=True)  # JSON data extracted from PDF
    
    # Technical specifications extracted from the document
    specifications = Column(JSONB, nullable=True)  # Device specs, I/O configs, etc.
    
    # Metadata
    description = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"
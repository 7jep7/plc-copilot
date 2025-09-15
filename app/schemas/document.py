"""Document schemas for request/response validation."""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from app.models.document import DocumentStatus, DocumentType


class DocumentBase(BaseModel):
    """Base document schema with common fields."""
    description: Optional[str] = None
    tags: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    pass


class DocumentUpdate(DocumentBase):
    """Schema for updating document metadata."""
    document_type: Optional[DocumentType] = None
    manufacturer: Optional[str] = None
    device_model: Optional[str] = None
    device_series: Optional[str] = None


class DocumentResponse(DocumentBase):
    """Schema for document responses."""
    id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    document_type: str
    manufacturer: Optional[str] = None
    device_model: Optional[str] = None
    device_series: Optional[str] = None
    status: str
    processing_error: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    specifications: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentExtractedData(BaseModel):
    """Schema for extracted document data."""
    raw_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    specifications: Optional[Dict[str, Any]] = None
    processing_status: str
    extraction_metadata: Optional[Dict[str, Any]] = None
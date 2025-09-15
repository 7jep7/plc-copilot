"""Document processing service for PDF parsing and analysis."""

import os
import uuid
import aiofiles
import structlog
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import UploadFile
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF

from app.core.config import settings
from app.models.document import Document, DocumentStatus, DocumentType
from app.schemas.document import DocumentUpdate
from app.services.openai_service import OpenAIService

logger = structlog.get_logger()


class DocumentService:
    """Service for document upload, processing, and management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.openai_service = OpenAIService()
        
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    async def create_document(
        self,
        file: UploadFile,
        description: Optional[str] = None,
        tags: Optional[str] = None
    ) -> Document:
        """
        Create a new document record and save the uploaded file.
        
        Args:
            file: Uploaded file
            description: Optional description
            tags: Optional tags
            
        Returns:
            Created document record
        """
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{file_id}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Save file to disk
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        file_size = len(content)
        
        # Create document record
        document = Document(
            filename=filename,
            original_filename=file.filename,
            file_size=file_size,
            mime_type=file.content_type,
            file_path=file_path,
            description=description,
            tags=tags,
            status=DocumentStatus.UPLOADED
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        logger.info("Document created", document_id=str(document.id), filename=filename)
        return document
    
    def get_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[DocumentStatus] = None
    ) -> List[Document]:
        """Get list of documents with optional filtering."""
        query = self.db.query(Document)
        
        if status_filter:
            query = query.filter(Document.status == status_filter.value)
        
        return query.offset(skip).limit(limit).all()
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """Get a specific document by ID."""
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def update_document(self, document_id: str, update_data: DocumentUpdate) -> Optional[Document]:
        """Update document metadata."""
        document = self.get_document(document_id)
        if not document:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(document, field):
                setattr(document, field, value)
        
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its file."""
        document = self.get_document(document_id)
        if not document:
            return False
        
        # Delete file from disk
        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
        except Exception as e:
            logger.warning("Failed to delete file", file_path=document.file_path, error=str(e))
        
        # Delete database record
        self.db.delete(document)
        self.db.commit()
        return True
    
    async def process_document(self, document_id: str) -> Optional[Document]:
        """
        Process a document to extract text and technical information.
        
        Args:
            document_id: ID of the document to process
            
        Returns:
            Updated document with processing results
        """
        document = self.get_document(document_id)
        if not document:
            return None
        
        logger.info("Starting document processing", document_id=document_id)
        
        try:
            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            self.db.commit()
            
            # Extract text from PDF
            raw_text = await self._extract_text_from_pdf(document.file_path)
            document.raw_text = raw_text
            
            # Classify document type
            document.document_type = self._classify_document_type(raw_text)
            
            # Extract device information
            device_info = self._extract_device_info(raw_text)
            if device_info:
                document.manufacturer = device_info.get("manufacturer")
                document.device_model = device_info.get("model")
                document.device_series = device_info.get("series")
            
            # Use OpenAI to analyze document for PLC context
            plc_analysis = await self.openai_service.analyze_document_for_plc_context(document)
            document.specifications = plc_analysis
            
            # Mark as processed
            document.status = DocumentStatus.PROCESSED
            
            self.db.commit()
            self.db.refresh(document)
            
            logger.info("Document processing completed", document_id=document_id)
            return document
            
        except Exception as e:
            # Mark as failed
            document.status = DocumentStatus.FAILED
            document.processing_error = str(e)
            self.db.commit()
            
            logger.error("Document processing failed", document_id=document_id, error=str(e))
            raise
    
    async def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using multiple methods for better coverage."""
        text_content = []
        
        try:
            # Method 1: pdfplumber (good for tables and structured content)
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
        except Exception as e:
            logger.warning("pdfplumber extraction failed", error=str(e))
        
        try:
            # Method 2: PyMuPDF (good for complex layouts)
            doc = fitz.open(file_path)
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text()
                if text and text not in text_content:
                    text_content.append(text)
            doc.close()
        except Exception as e:
            logger.warning("PyMuPDF extraction failed", error=str(e))
        
        try:
            # Method 3: PyPDF2 (fallback)
            if not text_content:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
        except Exception as e:
            logger.warning("PyPDF2 extraction failed", error=str(e))
        
        return "\n\n".join(text_content)
    
    def _classify_document_type(self, text: str) -> DocumentType:
        """Classify document type based on content."""
        text_lower = text.lower()
        
        # Simple keyword-based classification
        if any(word in text_lower for word in ["manual", "user guide", "operation"]):
            return DocumentType.MANUAL
        elif any(word in text_lower for word in ["datasheet", "specification", "technical data"]):
            return DocumentType.DATASHEET
        elif any(word in text_lower for word in ["specification", "spec", "requirements"]):
            return DocumentType.SPECIFICATION
        else:
            return DocumentType.UNKNOWN
    
    def _extract_device_info(self, text: str) -> Optional[Dict[str, str]]:
        """Extract device manufacturer, model, and series from text."""
        # This is a simplified implementation
        # In production, you'd want more sophisticated NLP or regex patterns
        
        lines = text.split('\n')[:20]  # Check first 20 lines
        info = {}
        
        for line in lines:
            line = line.strip()
            
            # Look for common manufacturer names
            manufacturers = ["Siemens", "Allen-Bradley", "Schneider", "Omron", "Mitsubishi", "ABB"]
            for manufacturer in manufacturers:
                if manufacturer.lower() in line.lower():
                    info["manufacturer"] = manufacturer
                    
                    # Try to extract model from the same line
                    words = line.split()
                    for i, word in enumerate(words):
                        if manufacturer.lower() in word.lower() and i + 1 < len(words):
                            info["model"] = words[i + 1]
                            break
                    break
        
        return info if info else None
    
    def get_extracted_data(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get extracted data from a processed document."""
        document = self.get_document(document_id)
        if not document or document.status != DocumentStatus.PROCESSED:
            return None
        
        return {
            "raw_text": document.raw_text,
            "structured_data": document.structured_data,
            "specifications": document.specifications,
            "processing_status": document.status,
            "device_info": {
                "manufacturer": document.manufacturer,
                "model": document.device_model,
                "series": document.device_series,
                "type": document.document_type
            }
        }
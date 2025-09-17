"""
Stateless document service for conversation-based PDF processing.

This service provides PDF parsing and analysis without database dependencies,
designed to work within the conversation context system.
"""

import os
import hashlib
import structlog
from typing import Optional, Dict, Any, List
from fastapi import UploadFile
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF

from app.services.openai_service import OpenAIService
from app.core.config import settings

logger = structlog.get_logger()


class DocumentInfo:
    """Container for parsed document information."""
    
    def __init__(
        self,
        filename: str,
        content_hash: str,
        raw_text: str,
        document_type: str,
        device_info: Optional[Dict[str, str]] = None,
        plc_analysis: Optional[Dict[str, Any]] = None,
        file_size: int = 0,
        mime_type: str = "application/pdf"
    ):
        self.filename = filename
        self.content_hash = content_hash
        self.raw_text = raw_text
        self.document_type = document_type
        self.device_info = device_info or {}
        self.plc_analysis = plc_analysis or {}
        self.file_size = file_size
        self.mime_type = mime_type
        self.processed_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for conversation context storage."""
        return {
            "filename": self.filename,
            "content_hash": self.content_hash,
            "raw_text": self.raw_text,
            "document_type": self.document_type,
            "device_info": self.device_info,
            "plc_analysis": self.plc_analysis,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "processed_at": self.processed_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentInfo":
        """Create from dictionary stored in conversation context."""
        return cls(
            filename=data["filename"],
            content_hash=data["content_hash"],
            raw_text=data["raw_text"],
            document_type=data["document_type"],
            device_info=data.get("device_info", {}),
            plc_analysis=data.get("plc_analysis", {}),
            file_size=data.get("file_size", 0),
            mime_type=data.get("mime_type", "application/pdf")
        )


class ConversationDocumentService:
    """
    Stateless document service for conversation-based PDF processing.
    
    This service processes PDFs without database storage, keeping all
    parsed content in conversation context for the duration of the session.
    """
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    async def process_uploaded_document(
        self, 
        file: UploadFile,
        analyze_with_openai: bool = True
    ) -> DocumentInfo:
        """
        Process an uploaded PDF file and extract relevant information.
        
        Args:
            file: Uploaded PDF file
            analyze_with_openai: Whether to perform OpenAI analysis
            
        Returns:
            DocumentInfo containing all extracted information
        """
        logger.info("Processing uploaded document", filename=file.filename)
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Generate content hash for deduplication
        content_hash = hashlib.sha256(content).hexdigest()
        
        # Save temporarily for processing
        temp_path = f"/tmp/{content_hash}.pdf"
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        try:
            # Extract text
            raw_text = await self._extract_text_from_pdf(temp_path)
            
            # Classify document type
            document_type = self._classify_document_type(raw_text)
            
            # Extract device information
            device_info = self._extract_device_info(raw_text)
            
            # Perform OpenAI analysis if requested
            plc_analysis = {}
            if analyze_with_openai and raw_text:
                plc_analysis = await self._analyze_document_for_plc_context(
                    raw_text, file.filename
                )
            
            # Create document info
            doc_info = DocumentInfo(
                filename=file.filename,
                content_hash=content_hash,
                raw_text=raw_text,
                document_type=document_type,
                device_info=device_info,
                plc_analysis=plc_analysis,
                file_size=file_size,
                mime_type=file.content_type
            )
            
            logger.info(
                "Document processing completed",
                filename=file.filename,
                content_length=len(raw_text),
                document_type=document_type,
                has_device_info=bool(device_info),
                has_plc_analysis=bool(plc_analysis)
            )
            
            return doc_info
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
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
        
        # Only try further methods if pdfplumber did not extract any text
        if not text_content:
            try:
                # Method 2: PyMuPDF (good for complex layouts)
                doc = fitz.open(file_path)
                for page_num in range(doc.page_count):
                    page = doc[page_num]
                    text = page.get_text()
                    if text:
                        text_content.append(text)
                doc.close()
            except Exception as e:
                logger.warning("PyMuPDF extraction failed", error=str(e))
        
        if not text_content:
            try:
                # Method 3: PyPDF2 (fallback)
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
            except Exception as e:
                logger.warning("PyPDF2 extraction failed", error=str(e))
        
        return "\n\n".join(text_content)
    
    def _classify_document_type(self, text: str) -> str:
        """Classify document type based on content."""
        text_lower = text.lower()
        
        # Simple keyword-based classification
        if any(word in text_lower for word in ["manual", "user guide", "operation", "installation"]):
            return "MANUAL"
        elif any(word in text_lower for word in ["datasheet", "specification", "technical data", "spec sheet"]):
            return "DATASHEET"
        elif any(word in text_lower for word in ["specification", "spec", "requirements", "standard"]):
            return "SPECIFICATION"
        elif any(word in text_lower for word in ["drawing", "schematic", "diagram", "blueprint"]):
            return "DRAWING"
        else:
            return "UNKNOWN"
    
    def _extract_device_info(self, text: str) -> Dict[str, str]:
        """Extract device manufacturer, model, and series from text."""
        lines = text.split('\n')[:30]  # Check first 30 lines
        info = {}
        
        # Common automation manufacturers
        manufacturers = [
            "Siemens", "Allen-Bradley", "Rockwell", "Schneider", "Omron", 
            "Mitsubishi", "ABB", "Beckhoff", "Phoenix Contact", "Weidmuller",
            "Pepperl+Fuchs", "Turck", "IFM", "Baumer", "Balluff", "Keyence",
            "Banner", "Sick", "Leuze", "Cognex", "Basler", "Allied Vision"
        ]
        
        for line in lines:
            line = line.strip()
            
            # Look for manufacturer names
            for manufacturer in manufacturers:
                if manufacturer.lower() in line.lower():
                    info["manufacturer"] = manufacturer
                    
                    # Try to extract model from the same line or next few words
                    words = line.split()
                    for i, word in enumerate(words):
                        if manufacturer.lower() in word.lower() and i + 1 < len(words):
                            # Look for model patterns (alphanumeric codes)
                            potential_model = words[i + 1]
                            if any(char.isdigit() for char in potential_model):
                                info["model"] = potential_model
                            break
                    break
        
        # Look for common model/part number patterns
        if "model" not in info:
            import re
            for line in lines:
                # Look for patterns like "Model: ABC123" or "Part No: XYZ-456"
                model_match = re.search(r'(?:model|part\s*no|part\s*number|article\s*no)[\s:]+([A-Z0-9\-_]+)', line, re.IGNORECASE)
                if model_match:
                    info["model"] = model_match.group(1)
                    break
        
        return info
    
    async def _analyze_document_for_plc_context(self, raw_text: str, filename: str) -> Dict[str, Any]:
        """Use OpenAI to analyze document for PLC-relevant context."""
        try:
            # Create a mock document object for the existing OpenAI method
            class MockDocument:
                def __init__(self, text: str, filename: str):
                    self.raw_text = text
                    self.filename = filename
                    self.device_model = None
                    self.manufacturer = None
            
            mock_doc = MockDocument(raw_text, filename)
            analysis = await self.openai_service.analyze_document_for_plc_context(mock_doc)
            return analysis
            
        except Exception as e:
            logger.warning("OpenAI document analysis failed", error=str(e))
            return {}
    
    def is_document_already_processed(
        self, 
        content_hash: str, 
        existing_documents: List[Dict[str, Any]]
    ) -> Optional[DocumentInfo]:
        """
        Check if a document with the same content hash has already been processed.
        
        Args:
            content_hash: SHA256 hash of the file content
            existing_documents: List of document dictionaries from conversation context
            
        Returns:
            DocumentInfo if already processed, None otherwise
        """
        for doc_data in existing_documents:
            if doc_data.get("content_hash") == content_hash:
                return DocumentInfo.from_dict(doc_data)
        return None
    
    def create_document_summary(self, doc_info: DocumentInfo) -> str:
        """Create a concise summary of document for prompt inclusion."""
        summary_parts = [f"📄 **{doc_info.filename}** ({doc_info.document_type})"]
        
        if doc_info.device_info:
            device_parts = []
            if doc_info.device_info.get("manufacturer"):
                device_parts.append(doc_info.device_info["manufacturer"])
            if doc_info.device_info.get("model"):
                device_parts.append(doc_info.device_info["model"])
            if device_parts:
                summary_parts.append(f"Device: {' '.join(device_parts)}")
        
        # Add key PLC-relevant information from analysis
        if doc_info.plc_analysis:
            if doc_info.plc_analysis.get("key_specifications"):
                specs = doc_info.plc_analysis["key_specifications"]
                if isinstance(specs, list) and specs:
                    summary_parts.append(f"Key specs: {', '.join(specs[:3])}")
        
        # Add document size info
        text_length = len(doc_info.raw_text)
        if text_length > 1000:
            summary_parts.append(f"Content: {text_length:,} characters of technical details available")
        
        return " | ".join(summary_parts)
    
    def get_relevant_context_for_prompt(
        self, 
        documents: List[DocumentInfo], 
        context_type: str = "general"
    ) -> str:
        """
        Extract relevant document context for inclusion in prompts.
        
        Args:
            documents: List of processed documents
            context_type: Type of context needed ('requirements', 'generation', 'general')
            
        Returns:
            Formatted string for prompt inclusion
        """
        if not documents:
            return ""
        
        context_parts = []
        
        for doc in documents:
            doc_context = [f"\n**Document: {doc.filename}** ({doc.document_type})"]
            
            # Add device information
            if doc.device_info:
                if doc.device_info.get("manufacturer") or doc.device_info.get("model"):
                    manufacturer = doc.device_info.get("manufacturer", "Unknown")
                    model = doc.device_info.get("model", "Unknown")
                    doc_context.append(f"Device: {manufacturer} {model}")
            
            # Add PLC analysis if available
            if doc.plc_analysis:
                if context_type == "requirements" and doc.plc_analysis.get("key_specifications"):
                    specs = doc.plc_analysis["key_specifications"]
                    if isinstance(specs, list):
                        doc_context.append(f"Specifications: {', '.join(specs)}")
                
                elif context_type == "generation" and doc.plc_analysis.get("plc_integration_points"):
                    integration = doc.plc_analysis["plc_integration_points"]
                    if isinstance(integration, list):
                        doc_context.append(f"PLC Integration: {', '.join(integration)}")
            
            # For shorter documents, include more raw content
            if len(doc.raw_text) < 5000:
                # Include first few lines for context
                first_lines = doc.raw_text.split('\n')[:10]
                meaningful_lines = [line.strip() for line in first_lines if line.strip() and len(line.strip()) > 10]
                if meaningful_lines:
                    doc_context.append(f"Content preview: {' | '.join(meaningful_lines[:3])}")
            
            context_parts.append("\n".join(doc_context))
        
        return "\n".join(context_parts)
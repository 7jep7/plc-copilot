"""
Vector Store Service for OpenAI Files

This service handles file uploads to the OpenAI vector store using a
configurable vector store ID from environment variables.
"""

import logging
import tempfile
import os
from typing import List, Dict, Any, Optional
from io import BytesIO
from pathlib import Path

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from app.core.config import settings

try:
    from app.services.pdf_extractor import PDFTextExtractor
    PDF_EXTRACTION_AVAILABLE = True
except ImportError:
    PDF_EXTRACTION_AVAILABLE = False

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing files in OpenAI's vector store."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if OPENAI_AVAILABLE else None
        self.vector_store_id = settings.OPENAI_VECTOR_STORE_ID
        self._session_files: Dict[str, List[str]] = {}  # Track uploaded file IDs per session
        
        # Initialize PDF extractor if available
        self.pdf_extractor = PDFTextExtractor() if PDF_EXTRACTION_AVAILABLE else None
        if self.pdf_extractor:
            logger.info("PDF text extraction enabled")
        else:
            logger.warning("PDF text extraction not available - PDFs will be uploaded as-is")
    
    async def upload_files_to_vector_store(
        self, 
        uploaded_files: List[BytesIO], 
        filenames: List[str],
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        Upload files to the OpenAI vector store attached to the assistant.
        
        Args:
            uploaded_files: List of file contents as BytesIO
            filenames: List of original filenames
            session_id: Session ID for tracking uploaded files
            
        Returns:
            List of file metadata with OpenAI file IDs
        """
        if not self.client:
            logger.warning("OpenAI client not available, skipping file upload")
            return []
        
        if not uploaded_files or not filenames:
            return []
        
        try:
            uploaded_file_metadata = []
            file_ids = []
            
            for file_content, filename in zip(uploaded_files, filenames):
                # Debug: Check BytesIO state before processing
                file_content.seek(0, 2)
                size_before = file_content.tell()
                file_content.seek(0)
                logger.info(f"Processing file {filename}: BytesIO size = {size_before} bytes")
                
                if size_before == 0:
                    logger.warning(f"Skipping empty file: {filename}")
                    continue
                
                try:
                    # Save file temporarily for upload
                    file_metadata = await self._upload_single_file(file_content, filename)
                    if file_metadata:
                        uploaded_file_metadata.append(file_metadata)
                        file_ids.append(file_metadata["file_id"])
                        logger.info(f"Successfully uploaded file to vector store: {filename}")
                
                except Exception as e:
                    logger.error(f"Failed to upload file {filename}: {e}")
                    continue
            
            # Track files for this session
            if session_id not in self._session_files:
                self._session_files[session_id] = []
            self._session_files[session_id].extend(file_ids)
            
            logger.info(f"Uploaded {len(uploaded_file_metadata)} files to vector store for session {session_id}")
            return uploaded_file_metadata
            
        except Exception as e:
            logger.error(f"Error uploading files to vector store: {e}")
            return []
    
    async def _upload_single_file(self, file_content: BytesIO, filename: str) -> Optional[Dict[str, Any]]:
        """Upload a single file to the OpenAI vector store."""
        
        # Debug: Check file content size before processing
        file_content.seek(0, 2)  # Seek to end to get size
        file_size = file_content.tell()
        file_content.seek(0)  # Reset to beginning
        
        logger.info(f"Processing file: {filename}, size: {file_size} bytes")
        
        if file_size == 0:
            logger.error(f"File {filename} is empty (0 bytes) - cannot upload to vector store")
            return None
        
        # Check if this is a PDF file that needs text extraction
        file_extension = Path(filename).suffix.lower()
        is_pdf = file_extension == '.pdf'
        
        if is_pdf and self.pdf_extractor:
            logger.info(f"Extracting text from PDF: {filename}")
            try:
                # Extract text from PDF
                extracted_data = self.pdf_extractor.extract_text_from_pdf(file_content, filename)
                
                if extracted_data and extracted_data.get('text'):
                    # Create text file content from extracted data
                    text_content = self.pdf_extractor.create_text_file_content(extracted_data, filename)
                    
                    # Convert to bytes for upload
                    text_bytes = text_content.encode('utf-8')
                    logger.info(f"Converted PDF to text: {len(text_bytes)} bytes")
                    
                    # Upload as text file instead of PDF
                    text_filename = filename.replace('.pdf', '_extracted.txt')
                    return await self._upload_text_content(text_bytes, text_filename)
                else:
                    logger.warning(f"No text extracted from PDF {filename}, uploading as-is")
            except Exception as e:
                logger.error(f"PDF text extraction failed for {filename}: {e}")
                logger.info("Falling back to direct PDF upload")
        
        # Upload file as-is (original logic)
        return await self._upload_raw_file(file_content, filename)
    
    async def _upload_text_content(self, text_bytes: bytes, filename: str) -> Optional[Dict[str, Any]]:
        """Upload text content to vector store."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp_file:
            try:
                tmp_file.write(text_bytes)
                tmp_file.flush()
                
                # Verify the temporary file has content
                tmp_file_size = os.path.getsize(tmp_file.name)
                logger.info(f"Text file {tmp_file.name} created with {tmp_file_size} bytes")
                
                if tmp_file_size == 0:
                    logger.error(f"Text file is empty after writing content for {filename}")
                    return None
                
                # Upload to OpenAI
                with open(tmp_file.name, 'rb') as f:
                    file_object = self.client.files.create(
                        file=f,
                        purpose="assistants"
                    )
                
                # Add to vector store
                vector_store_file_id = None
                try:
                    vector_store_file = self.client.vector_stores.files.create(
                        vector_store_id=self.vector_store_id,
                        file_id=file_object.id
                    )
                    vector_store_file_id = vector_store_file.id
                except Exception as e:
                    logger.warning(f"Could not add text file to vector store: {e}")
                
                return {
                    "file_id": file_object.id,
                    "vector_store_file_id": vector_store_file_id,
                    "filename": filename,
                    "bytes": file_object.bytes,
                    "status": "uploaded",
                    "type": "extracted_text"
                }
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_file.name)
                except Exception:
                    pass
    
    async def _upload_raw_file(self, file_content: BytesIO, filename: str) -> Optional[Dict[str, Any]]:
        """Upload raw file content to vector store (original logic)."""
        # Create temporary file for upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp_file:
            try:
                # Write content to temporary file
                content_data = file_content.read()
                logger.info(f"Read {len(content_data)} bytes from BytesIO for {filename}")
                
                tmp_file.write(content_data)
                tmp_file.flush()
                
                # Verify the temporary file has content
                tmp_file_size = os.path.getsize(tmp_file.name)
                logger.info(f"Temporary file {tmp_file.name} created with {tmp_file_size} bytes")
                
                if tmp_file_size == 0:
                    logger.error(f"Temporary file is empty after writing content for {filename}")
                    return None
                
                # Upload to OpenAI
                with open(tmp_file.name, 'rb') as f:
                    file_object = self.client.files.create(
                        file=f,
                        purpose="assistants"
                    )
                
                # Try to add file to vector store (if API is available)
                vector_store_file_id = None
                try:
                    vector_store_file = self.client.vector_stores.files.create(
                        vector_store_id=self.vector_store_id,
                        file_id=file_object.id
                    )
                    vector_store_file_id = vector_store_file.id
                except AttributeError:
                    logger.warning("Vector stores API not available - file uploaded to OpenAI but not added to vector store")
                except Exception as e:
                    logger.warning(f"Could not add file to vector store: {e}")
                
                return {
                    "file_id": file_object.id,
                    "vector_store_file_id": vector_store_file_id,
                    "filename": filename,
                    "bytes": file_object.bytes,
                    "status": "uploaded"
                }
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_file.name)
                except Exception:
                    pass
    
    async def cleanup_session_files(self, session_id: str) -> None:
        """
        Clean up files uploaded for a specific session.
        
        Args:
            session_id: Session ID to clean up files for
        """
        if session_id not in self._session_files:
            return
        
        file_ids = self._session_files[session_id]
        if not file_ids:
            return
        
        try:
            for file_id in file_ids:
                try:
                    # Remove from vector store first
                    self.client.vector_stores.files.delete(
                        vector_store_id=self.vector_store_id,
                        file_id=file_id
                    )
                    
                    # Delete the file object
                    self.client.files.delete(file_id)
                    
                    logger.info(f"Deleted file from vector store: {file_id}")
                    
                except Exception as e:
                    logger.warning(f"Failed to delete file {file_id}: {e}")
            
            # Remove from tracking
            del self._session_files[session_id]
            logger.info(f"Cleaned up {len(file_ids)} files for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up session files: {e}")
    
    def get_vector_store_info(self) -> Dict[str, Any]:
        """Get information about the vector store."""
        if not self.client:
            return {"error": "OpenAI client not available"}
        
        try:
            # Try to access vector store - check if it exists
            vector_store = self.client.vector_stores.retrieve(self.vector_store_id)
            return {
                "id": vector_store.id,
                "name": getattr(vector_store, 'name', 'N/A'),
                "file_counts": getattr(vector_store, 'file_counts', {}),
                "status": getattr(vector_store, 'status', 'unknown'),
                "usage_bytes": getattr(vector_store, 'usage_bytes', 0)
            }
        except AttributeError as e:
            logger.warning(f"Vector stores API not available in current OpenAI client: {e}")
            return {"error": "Vector stores API not available - using file uploads only"}
        except Exception as e:
            logger.error(f"Error getting vector store info: {e}")
            return {"error": str(e)}
    
    def list_session_files(self, session_id: str) -> List[str]:
        """List file IDs uploaded for a session."""
        return self._session_files.get(session_id, [])
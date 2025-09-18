"""
RAG (Retrieval-Augmented Generation) service for file processing and vector search.

This service handles:
- File text extraction (PDF, TXT, etc.)
- Text chunking for embeddings
- Vector database storage and retrieval
- Document cleanup and session management
"""

import os
import re
import tempfile
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from io import BytesIO
import logging

# Vector DB and embeddings
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

# PDF processing
try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# OpenAI embeddings
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """Service for document processing, embedding, and retrieval."""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY) if OPENAI_AVAILABLE else None
        self.chroma_client = None
        self.collection = None
        self.session_id = None
        
        if CHROMA_AVAILABLE:
            # Initialize ChromaDB with temporary storage
            self.temp_dir = tempfile.mkdtemp(prefix="plc_copilot_rag_")
            self.chroma_client = chromadb.PersistentClient(
                path=self.temp_dir,
                settings=Settings(anonymized_telemetry=False)
            )
    
    def initialize_session(self, session_id: str) -> None:
        """Initialize a new RAG session with unique collection."""
        self.session_id = session_id
        
        if not CHROMA_AVAILABLE or not self.chroma_client:
            logger.warning("ChromaDB not available, RAG functionality disabled")
            return
        
        # Create or get collection for this session
        collection_name = f"session_{session_id}"
        try:
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"session_id": session_id}
            )
            logger.info(f"Created RAG collection for session: {session_id}")
        except Exception as e:
            # Collection might already exist
            try:
                self.collection = self.chroma_client.get_collection(collection_name)
                logger.info(f"Using existing RAG collection for session: {session_id}")
            except Exception:
                logger.error(f"Failed to initialize RAG collection: {e}")
    
    async def process_and_embed_file(self, file_content: BytesIO, filename: str) -> List[Dict[str, Any]]:
        """
        Process a file, extract text, chunk it, and store embeddings.
        
        Args:
            file_content: File content as BytesIO
            filename: Original filename for reference
            
        Returns:
            List of chunk metadata with embeddings stored
        """
        if not self.collection:
            logger.warning("No RAG collection initialized, skipping file processing")
            return []
        
        try:
            # Extract text from file
            text = self._extract_text_from_file(file_content, filename)
            if not text.strip():
                logger.warning(f"No text extracted from file: {filename}")
                return []
            
            # Chunk the text
            chunks = self._chunk_text(text, chunk_size=500, overlap=50)
            logger.info(f"Created {len(chunks)} chunks from file: {filename}")
            
            # Generate embeddings and store
            chunk_metadata = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{filename}_{i}_{hashlib.md5(chunk.encode()).hexdigest()[:8]}"
                
                # Generate embedding
                embedding = await self._generate_embedding(chunk)
                if embedding:
                    # Store in vector DB
                    self.collection.add(
                        documents=[chunk],
                        embeddings=[embedding],
                        metadatas=[{
                            "filename": filename,
                            "chunk_index": i,
                            "chunk_id": chunk_id
                        }],
                        ids=[chunk_id]
                    )
                    
                    chunk_metadata.append({
                        "chunk_id": chunk_id,
                        "filename": filename,
                        "chunk_index": i,
                        "text_preview": chunk[:100] + "..." if len(chunk) > 100 else chunk
                    })
            
            logger.info(f"Successfully embedded {len(chunk_metadata)} chunks from {filename}")
            return chunk_metadata
            
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            return []
    
    async def retrieve_relevant_chunks(self, query: str, top_k: int = 5) -> List[str]:
        """
        Retrieve most relevant document chunks for a query.
        
        Args:
            query: User query to find relevant chunks for
            top_k: Number of top chunks to retrieve
            
        Returns:
            List of relevant text chunks
        """
        if not self.collection:
            logger.warning("No RAG collection available for retrieval")
            return []
        
        try:
            # Generate embedding for the query
            query_embedding = await self._generate_embedding(query)
            if not query_embedding:
                return []
            
            # Search for similar chunks
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self.collection.count())
            )
            
            # Extract the document texts
            retrieved_chunks = []
            if results["documents"] and len(results["documents"]) > 0:
                for doc in results["documents"][0]:  # First query result
                    retrieved_chunks.append(doc)
            
            logger.info(f"Retrieved {len(retrieved_chunks)} relevant chunks for query")
            return retrieved_chunks
            
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []
    
    def cleanup_session(self) -> None:
        """Clean up session data and temporary files."""
        if self.session_id and self.chroma_client:
            try:
                collection_name = f"session_{self.session_id}"
                self.chroma_client.delete_collection(collection_name)
                logger.info(f"Cleaned up RAG session: {self.session_id}")
            except Exception as e:
                logger.warning(f"Error cleaning up RAG session: {e}")
        
        # Clean up temporary directory
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
                logger.info("Cleaned up temporary RAG directory")
            except Exception as e:
                logger.warning(f"Error cleaning up temp directory: {e}")
    
    def _extract_text_from_file(self, file_content: BytesIO, filename: str) -> str:
        """Extract text from various file formats."""
        file_content.seek(0)  # Reset position
        
        # Get file extension
        _, ext = os.path.splitext(filename.lower())
        
        if ext == '.pdf':
            return self._extract_pdf_text(file_content)
        elif ext in ['.txt', '.md', '.rst']:
            return file_content.read().decode('utf-8', errors='ignore')
        else:
            # Try to read as text
            try:
                return file_content.read().decode('utf-8', errors='ignore')
            except Exception:
                logger.warning(f"Could not extract text from file: {filename}")
                return ""
    
    def _extract_pdf_text(self, file_content: BytesIO) -> str:
        """Extract text from PDF using multiple methods."""
        if not PDF_AVAILABLE:
            logger.warning("PDF processing libraries not available")
            return ""
        
        text = ""
        file_content.seek(0)
        
        # Try PyPDF2 first
        try:
            reader = PyPDF2.PdfReader(file_content)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")
        
        # If PyPDF2 didn't work well, try pdfplumber
        if len(text.strip()) < 100:  # Very little text extracted
            file_content.seek(0)
            try:
                with pdfplumber.open(file_content) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                logger.warning(f"pdfplumber extraction failed: {e}")
        
        return text.strip()
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        # Clean up text
        text = re.sub(r'\s+', ' ', text.strip())
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence or paragraph boundaries
            if end < len(text):
                # Look for sentence ending within the last 100 characters
                search_start = max(start + chunk_size - 100, start)
                sentence_end = text.rfind('.', search_start, end)
                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Look for space
                    space_pos = text.rfind(' ', search_start, end)
                    if space_pos > start:
                        end = space_pos
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
        
        return chunks
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using OpenAI API."""
        if not self.openai_client:
            logger.warning("OpenAI client not available for embeddings")
            return None
        
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",  # Cost-effective embedding model
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
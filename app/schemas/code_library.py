"""Code library schemas for API requests and responses."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CodeFileMetadata(BaseModel):
    """Metadata for a code file in the library."""
    name: str
    path: str
    domain: str
    size_bytes: int
    modified_date: str
    language: str = "structured_text"
    description: Optional[str] = None
    author: Optional[str] = None
    version: Optional[str] = None
    application: Optional[str] = None
    features: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    source: str = "library"  # "library" or "user_upload"


class CodeFileContent(CodeFileMetadata):
    """Code file with full source code content."""
    source_code: str


class LibraryStructure(BaseModel):
    """Structure of the code library by domains."""
    domains: Dict[str, Dict[str, Any]]


class SearchRequest(BaseModel):
    """Request for searching the code library."""
    query: str = Field(..., description="Search query for code files")
    domain: Optional[str] = Field(None, description="Specific domain to search within")
    limit: Optional[int] = Field(10, description="Maximum number of results to return")


class SearchResult(BaseModel):
    """Search result with relevance scoring."""
    files: List[CodeFileMetadata]
    total_count: int
    query: str
    domain: Optional[str] = None


class FileUploadRequest(BaseModel):
    """Request for uploading a new ST code file."""
    filename: str = Field(..., description="Name of the ST file")
    content: str = Field(..., description="Source code content")
    domain: str = Field(..., description="Domain/category for the file")
    description: Optional[str] = Field(None, description="Description of the code")
    author: Optional[str] = Field(None, description="Author name")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")


class FileUploadResponse(BaseModel):
    """Response after successful file upload."""
    success: bool
    file_info: CodeFileMetadata
    message: str


class SimilarFilesRequest(BaseModel):
    """Request for finding similar files."""
    reference_file: str = Field(..., description="Reference file to find similar files for")
    domain: Optional[str] = Field(None, description="Domain to search within")
    limit: Optional[int] = Field(5, description="Maximum number of similar files to return")


class SimilarFilesResponse(BaseModel):
    """Response with similar files."""
    reference_file: str
    similar_files: List[CodeFileMetadata]
    

class DomainInfo(BaseModel):
    """Information about a code domain."""
    name: str
    description: str
    file_count: int
    example_files: List[str]


class LibrarySummary(BaseModel):
    """Summary of the entire code library."""
    total_files: int
    total_domains: int
    domains: List[DomainInfo]
    last_updated: str
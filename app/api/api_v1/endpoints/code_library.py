"""Code Library API endpoints for managing ST code samples."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.services.code_library_service import CodeLibraryService
from app.schemas.code_library import (
    LibraryStructure, SearchRequest, SearchResult, FileUploadRequest, 
    FileUploadResponse, CodeFileContent, SimilarFilesRequest, 
    SimilarFilesResponse, LibrarySummary, CodeFileMetadata
)

router = APIRouter()
logger = structlog.get_logger()


@router.get("/", response_model=LibrarySummary)
async def get_library_summary(db: Session = Depends(get_db)):
    """
    Get a summary of the entire code library.
    
    Returns overview with domain counts and file statistics.
    """
    library_service = CodeLibraryService(db)
    structure = library_service.get_library_structure()
    
    total_files = sum(len(domain_info["files"]) for domain_info in structure.values())
    total_domains = len(structure)
    
    domains = []
    for domain_name, domain_info in structure.items():
        domains.append({
            "name": domain_name,
            "description": domain_info["description"],
            "file_count": len(domain_info["files"]),
            "example_files": [f["name"] for f in domain_info["files"][:3]]  # First 3 files as examples
        })
    
    return LibrarySummary(
        total_files=total_files,
        total_domains=total_domains,
        domains=domains,
        last_updated="2024-09-15T00:00:00Z"  # Could be dynamic
    )


@router.get("/structure", response_model=dict)
async def get_library_structure(db: Session = Depends(get_db)):
    """
    Get the complete library directory structure with all files and metadata.
    
    Returns hierarchical structure organized by domains.
    """
    library_service = CodeLibraryService(db)
    structure = library_service.get_library_structure()
    
    logger.info("Library structure requested", domains=len(structure))
    return {"domains": structure}


@router.post("/search", response_model=SearchResult)
async def search_library(
    search_request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search the code library for files matching the query.
    
    - **query**: Search terms to match against filenames, descriptions, and features
    - **domain**: Optional domain filter (e.g., 'motor_control', 'safety_systems')
    - **limit**: Maximum number of results to return
    """
    library_service = CodeLibraryService(db)
    
    results = library_service.search_library(
        query=search_request.query,
        domain=search_request.domain
    )
    
    # Apply limit
    limited_results = results[:search_request.limit] if search_request.limit else results
    
    logger.info("Library search completed", 
               query=search_request.query, 
               results_found=len(results), 
               results_returned=len(limited_results))
    
    return SearchResult(
        files=limited_results,
        total_count=len(results),
        query=search_request.query,
        domain=search_request.domain
    )


@router.get("/browse/{domain}")
async def browse_domain(
    domain: str,
    db: Session = Depends(get_db)
):
    """
    Browse all files in a specific domain.
    
    - **domain**: Domain name (e.g., 'conveyor_systems', 'process_control')
    """
    library_service = CodeLibraryService(db)
    structure = library_service.get_library_structure()
    
    if domain not in structure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{domain}' not found"
        )
    
    domain_info = structure[domain]
    logger.info("Domain browsed", domain=domain, file_count=len(domain_info["files"]))
    
    return {
        "domain": domain,
        "description": domain_info["description"],
        "files": domain_info["files"]
    }


@router.get("/file/{domain}/{filename}", response_model=CodeFileContent)
async def get_file_content(
    domain: str,
    filename: str,
    db: Session = Depends(get_db)
):
    """
    Get the complete content and metadata of a specific ST file.
    
    - **domain**: Domain name where the file is located
    - **filename**: Name of the ST file (with .st extension)
    """
    library_service = CodeLibraryService(db)
    
    try:
        file_content = library_service.get_file_content(domain, filename)
        logger.info("File content retrieved", domain=domain, filename=filename)
        return file_content
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{filename}' not found in domain '{domain}'"
        )


@router.post("/upload", response_model=FileUploadResponse)
async def upload_st_file(
    upload_request: FileUploadRequest,
    db: Session = Depends(get_db)
):
    """
    Upload a new ST code file to the user library.
    
    - **filename**: Name for the ST file
    - **content**: ST source code content
    - **domain**: Domain/category for organization
    - **description**: Optional description of the code
    - **author**: Optional author name
    - **tags**: Optional tags for categorization
    """
    library_service = CodeLibraryService(db)
    
    try:
        file_info = await library_service.upload_user_file(
            filename=upload_request.filename,
            content=upload_request.content,
            domain=upload_request.domain,
            description=upload_request.description,
            author=upload_request.author,
            tags=upload_request.tags
        )
        
        return FileUploadResponse(
            success=True,
            file_info=file_info,
            message=f"File '{upload_request.filename}' uploaded successfully to '{upload_request.domain}'"
        )
        
    except Exception as e:
        logger.error("File upload failed", 
                    filename=upload_request.filename, 
                    domain=upload_request.domain, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post("/upload-file")
async def upload_st_file_multipart(
    file: UploadFile = File(...),
    domain: str = "user_contributions",
    description: Optional[str] = None,
    author: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Upload an ST file via multipart form data.
    
    - **file**: ST file to upload
    - **domain**: Domain/category for organization
    - **description**: Optional description
    - **author**: Optional author name
    """
    if not file.filename.endswith('.st'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .st files are allowed"
        )
    
    library_service = CodeLibraryService(db)
    
    try:
        content = await file.read()
        content_str = content.decode('utf-8')
        
        file_info = await library_service.upload_user_file(
            filename=file.filename,
            content=content_str,
            domain=domain,
            description=description,
            author=author
        )
        
        return FileUploadResponse(
            success=True,
            file_info=file_info,
            message=f"File '{file.filename}' uploaded successfully"
        )
        
    except Exception as e:
        logger.error("Multipart file upload failed", 
                    filename=file.filename, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post("/similar", response_model=SimilarFilesResponse)
async def find_similar_files(
    similar_request: SimilarFilesRequest,
    db: Session = Depends(get_db)
):
    """
    Find files similar to a reference file.
    
    - **reference_file**: Name of the reference file
    - **domain**: Optional domain to search within
    - **limit**: Maximum number of similar files to return
    """
    library_service = CodeLibraryService(db)
    
    similar_files = library_service.get_similar_files(
        reference_file=similar_request.reference_file,
        domain=similar_request.domain,
        limit=similar_request.limit
    )
    
    logger.info("Similar files search completed", 
               reference_file=similar_request.reference_file,
               similar_count=len(similar_files))
    
    return SimilarFilesResponse(
        reference_file=similar_request.reference_file,
        similar_files=similar_files
    )


@router.get("/user-uploads")
async def get_user_uploads(
    domain: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all user-uploaded ST files.
    
    - **domain**: Optional domain filter
    """
    library_service = CodeLibraryService(db)
    uploads = library_service.get_user_uploads(domain)
    
    logger.info("User uploads retrieved", count=len(uploads), domain=domain)
    return {"uploads": uploads}


@router.delete("/user-uploads/{domain}/{filename}")
async def delete_user_file(
    domain: str,
    filename: str,
    db: Session = Depends(get_db)
):
    """
    Delete a user-uploaded file.
    
    - **domain**: Domain where the file is located
    - **filename**: Name of the file to delete
    """
    library_service = CodeLibraryService(db)
    
    success = library_service.delete_user_file(domain, filename)
    
    if success:
        logger.info("User file deleted", domain=domain, filename=filename)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"File '{filename}' deleted successfully"}
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{filename}' not found in domain '{domain}'"
        )


@router.get("/domains")
async def list_domains(db: Session = Depends(get_db)):
    """
    Get a list of all available domains in the library.
    """
    library_service = CodeLibraryService(db)
    structure = library_service.get_library_structure()
    
    domains = [
        {
            "name": domain_name,
            "description": domain_info["description"],
            "file_count": len(domain_info["files"])
        }
        for domain_name, domain_info in structure.items()
    ]
    
    return {"domains": domains}
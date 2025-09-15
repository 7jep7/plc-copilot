"""Document upload and processing endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.models.document import Document, DocumentStatus
from app.services.document_service import DocumentService
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate

router = APIRouter()
logger = structlog.get_logger()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF document (manual, datasheet, specification) for processing.
    
    - **file**: PDF file to upload
    - **description**: Optional description of the document
    - **tags**: Optional comma-separated tags for categorization
    """
    logger.info("Document upload started", filename=file.filename, content_type=file.content_type)
    
    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Create document service instance
    document_service = DocumentService(db)
    
    try:
        # Process the upload
        document = await document_service.create_document(
            file=file,
            description=description,
            tags=tags
        )
        
        logger.info("Document uploaded successfully", document_id=str(document.id))
        return document
        
    except Exception as e:
        logger.error("Document upload failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[DocumentStatus] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of uploaded documents.
    
    - **skip**: Number of documents to skip (for pagination)
    - **limit**: Maximum number of documents to return
    - **status_filter**: Optional filter by document status
    """
    document_service = DocumentService(db)
    documents = document_service.get_documents(
        skip=skip, 
        limit=limit, 
        status_filter=status_filter
    )
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific document by ID.
    
    - **document_id**: UUID of the document to retrieve
    """
    document_service = DocumentService(db)
    document = document_service.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update document metadata.
    
    - **document_id**: UUID of the document to update
    - **document_update**: Updated document information
    """
    document_service = DocumentService(db)
    document = document_service.update_document(document_id, document_update)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    logger.info("Document updated", document_id=document_id)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a document and its associated file.
    
    - **document_id**: UUID of the document to delete
    """
    document_service = DocumentService(db)
    success = document_service.delete_document(document_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    logger.info("Document deleted", document_id=document_id)


@router.post("/{document_id}/process", response_model=DocumentResponse)
async def process_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Trigger processing of an uploaded document to extract technical information.
    
    - **document_id**: UUID of the document to process
    """
    document_service = DocumentService(db)
    document = await document_service.process_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    logger.info("Document processing started", document_id=document_id)
    return document


@router.get("/{document_id}/extracted-data")
async def get_extracted_data(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the extracted structured data from a processed document.
    
    - **document_id**: UUID of the document
    """
    document_service = DocumentService(db)
    extracted_data = document_service.get_extracted_data(document_id)
    
    if extracted_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not processed"
        )
    
    return extracted_data
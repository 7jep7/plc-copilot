"""PLC code generation endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.models.plc_code import PLCCode, PLCLanguage
from app.services.plc_service import PLCService
from app.schemas.plc_code import PLCCodeCreate, PLCCodeResponse, PLCCodeUpdate, PLCGenerationRequest

router = APIRouter()
logger = structlog.get_logger()


@router.post("/generate", response_model=PLCCodeResponse, status_code=status.HTTP_201_CREATED)
async def generate_plc_code(
    request: PLCGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate PLC code from user prompt and optional document context.
    
    - **request**: PLC code generation request with prompt and parameters
    """
    logger.info("PLC code generation started", prompt_length=len(request.user_prompt))
    
    plc_service = PLCService(db)
    
    try:
        plc_code = await plc_service.generate_code(request)
        logger.info("PLC code generated successfully", code_id=str(plc_code.id))
        return plc_code
        
    except Exception as e:
        logger.error("PLC code generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PLC code"
        )


@router.get("/", response_model=List[PLCCodeResponse])
async def list_plc_codes(
    skip: int = 0,
    limit: int = 100,
    language: Optional[PLCLanguage] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of generated PLC codes.
    
    - **skip**: Number of codes to skip (for pagination)
    - **limit**: Maximum number of codes to return
    - **language**: Optional filter by PLC language
    """
    plc_service = PLCService(db)
    codes = plc_service.get_plc_codes(skip=skip, limit=limit, language=language)
    return codes


@router.get("/{code_id}", response_model=PLCCodeResponse)
async def get_plc_code(
    code_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific PLC code by ID.
    
    - **code_id**: UUID of the PLC code to retrieve
    """
    plc_service = PLCService(db)
    code = plc_service.get_plc_code(code_id)
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PLC code not found"
        )
    
    return code


@router.put("/{code_id}", response_model=PLCCodeResponse)
async def update_plc_code(
    code_id: str,
    code_update: PLCCodeUpdate,
    db: Session = Depends(get_db)
):
    """
    Update PLC code metadata or source code.
    
    - **code_id**: UUID of the PLC code to update
    - **code_update**: Updated PLC code information
    """
    plc_service = PLCService(db)
    code = plc_service.update_plc_code(code_id, code_update)
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PLC code not found"
        )
    
    logger.info("PLC code updated", code_id=code_id)
    return code


@router.post("/{code_id}/validate", response_model=dict)
async def validate_plc_code(
    code_id: str,
    db: Session = Depends(get_db)
):
    """
    Validate PLC code syntax and structure.
    
    - **code_id**: UUID of the PLC code to validate
    """
    plc_service = PLCService(db)
    validation_result = await plc_service.validate_code(code_id)
    
    if validation_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PLC code not found"
        )
    
    logger.info("PLC code validation completed", code_id=code_id)
    return validation_result


@router.post("/{code_id}/compile", response_model=dict)
async def compile_plc_code(
    code_id: str,
    db: Session = Depends(get_db)
):
    """
    Compile PLC code for deployment.
    
    - **code_id**: UUID of the PLC code to compile
    """
    plc_service = PLCService(db)
    compilation_result = await plc_service.compile_code(code_id)
    
    if compilation_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PLC code not found"
        )
    
    logger.info("PLC code compilation completed", code_id=code_id)
    return compilation_result


@router.delete("/{code_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plc_code(
    code_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a PLC code.
    
    - **code_id**: UUID of the PLC code to delete
    """
    plc_service = PLCService(db)
    success = plc_service.delete_plc_code(code_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PLC code not found"
        )
    
    logger.info("PLC code deleted", code_id=code_id)
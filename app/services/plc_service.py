"""PLC code generation and management service."""

import structlog
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.plc_code import PLCCode, PLCCodeStatus, PLCLanguage
from app.models.document import Document
from app.schemas.plc_code import PLCGenerationRequest, PLCCodeUpdate
from app.services.openai_service import OpenAIService
from app.services.document_service import DocumentService

logger = structlog.get_logger()


class PLCService:
    """Service for PLC code generation and management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.openai_service = OpenAIService()
        self.document_service = DocumentService(db)
    
    async def generate_code(self, request: PLCGenerationRequest) -> PLCCode:
        """
        Generate PLC code using AI based on user prompt and optional document context.
        
        Args:
            request: PLC generation request
            
        Returns:
            Generated PLC code record
        """
        logger.info("Starting PLC code generation", prompt=request.user_prompt[:100])
        
        # Get document context if provided
        document_context = None
        if request.document_id:
            document_context = self.document_service.get_document(request.document_id)
        
        # Generate code using OpenAI
        generation_result = await self.openai_service.generate_plc_code(request, document_context)
        
        # Create PLC code record
        plc_code = PLCCode(
            name=generation_result["name"],
            description=generation_result["description"],
            language=request.language,
            source_code=generation_result["source_code"],
            user_prompt=request.user_prompt,
            ai_model_used=generation_result["generation_metadata"]["model"],
            generation_parameters=generation_result["generation_metadata"],
            status=PLCCodeStatus.GENERATED,
            document_id=request.document_id,
            input_variables=generation_result.get("input_variables"),
            output_variables=generation_result.get("output_variables")
        )
        
        self.db.add(plc_code)
        self.db.commit()
        self.db.refresh(plc_code)
        
        logger.info("PLC code generated", code_id=str(plc_code.id))
        return plc_code
    
    def get_plc_codes(
        self,
        skip: int = 0,
        limit: int = 100,
        language: Optional[PLCLanguage] = None
    ) -> List[PLCCode]:
        """Get list of PLC codes with optional filtering."""
        query = self.db.query(PLCCode)
        
        if language:
            query = query.filter(PLCCode.language == language.value)
        
        return query.offset(skip).limit(limit).all()
    
    def get_plc_code(self, code_id: str) -> Optional[PLCCode]:
        """Get a specific PLC code by ID."""
        try:
            return self.db.query(PLCCode).filter(PLCCode.id == code_id).first()
        except Exception:
            return None
    
    def update_plc_code(self, code_id: str, update_data: PLCCodeUpdate) -> Optional[PLCCode]:
        """Update PLC code."""
        plc_code = self.get_plc_code(code_id)
        if not plc_code:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(plc_code, field):
                setattr(plc_code, field, value)
        
        self.db.commit()
        self.db.refresh(plc_code)
        return plc_code
    
    def delete_plc_code(self, code_id: str) -> bool:
        """Delete a PLC code."""
        plc_code = self.get_plc_code(code_id)
        if not plc_code:
            return False
        
        self.db.delete(plc_code)
        self.db.commit()
        return True
    
    async def validate_code(self, code_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate PLC code syntax and structure.
        
        Args:
            code_id: ID of the PLC code to validate
            
        Returns:
            Validation results dictionary
        """
        plc_code = self.get_plc_code(code_id)
        if not plc_code:
            return None
        
        # Basic syntax validation (simplified)
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "syntax_score": 95.0,
            "complexity_score": 75.0
        }
        
        # Check for basic syntax issues
        source_code = plc_code.source_code
        
        # Check for required sections
        if "PROGRAM" not in source_code.upper():
            validation_result["errors"].append("Missing PROGRAM declaration")
            validation_result["is_valid"] = False
        
        if "VAR" not in source_code.upper():
            validation_result["warnings"].append("No variable declarations found")
        
        if "END_PROGRAM" not in source_code.upper():
            validation_result["errors"].append("Missing END_PROGRAM statement")
            validation_result["is_valid"] = False
        
        # Update PLC code with validation results
        plc_code.validation_results = validation_result
        if validation_result["is_valid"]:
            plc_code.status = PLCCodeStatus.VALIDATED
        
        self.db.commit()
        
        logger.info("Code validation completed", code_id=code_id, is_valid=validation_result["is_valid"])
        return validation_result
    
    async def compile_code(self, code_id: str) -> Optional[Dict[str, Any]]:
        """
        Compile PLC code for deployment (simplified simulation).
        
        Args:
            code_id: ID of the PLC code to compile
            
        Returns:
            Compilation results dictionary
        """
        plc_code = self.get_plc_code(code_id)
        if not plc_code:
            return None
        
        # Simplified compilation simulation
        compilation_result = {
            "success": True,
            "compiled_code": f"# Compiled version of {plc_code.name}\n{plc_code.source_code}",
            "compilation_errors": [],
            "compilation_warnings": [],
            "binary_size": len(plc_code.source_code) * 2,  # Simplified estimate
            "compilation_time": 0.5  # Simulated compile time
        }
        
        # Check if code was validated first
        if plc_code.status != PLCCodeStatus.VALIDATED:
            compilation_result["compilation_warnings"].append("Code was not validated before compilation")
        
        # Update PLC code with compilation results
        if compilation_result["success"]:
            plc_code.compiled_code = compilation_result["compiled_code"]
            plc_code.status = PLCCodeStatus.TESTED  # Mark as ready for testing
        
        self.db.commit()
        
        logger.info("Code compilation completed", code_id=code_id, success=compilation_result["success"])
        return compilation_result
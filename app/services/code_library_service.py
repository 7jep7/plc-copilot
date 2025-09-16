"""
Code Library Service - Manages ST code samples and user uploads
"""
import os
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import structlog
from datetime import datetime

from app.core.config import settings
from app.models.plc_code import PLCLanguage

logger = structlog.get_logger()


class CodeLibraryService:
    """Service for managing the ST code library and user uploads."""
    
    def __init__(self, db: Session):
        self.db = db
        self.library_base_path = Path(settings.PROJECT_ROOT) / "st_code_library"
        self.user_uploads_path = Path(settings.PROJECT_ROOT) / "user_uploads" / "st_code"
        
        # Ensure directories exist
        self.library_base_path.mkdir(parents=True, exist_ok=True)
        self.user_uploads_path.mkdir(parents=True, exist_ok=True)
    
    def get_library_structure(self) -> Dict[str, Any]:
        """Get the complete library directory structure with metadata."""
        structure = {}
        
        for domain_path in self.library_base_path.iterdir():
            if domain_path.is_dir() and not domain_path.name.startswith('.'):
                domain_name = domain_path.name
                structure[domain_name] = {
                    "path": str(domain_path.relative_to(self.library_base_path)),
                    "files": [],
                    "description": self._get_domain_description(domain_name)
                }
                
                # Get all ST files in this domain
                for file_path in domain_path.rglob("*.st"):
                    file_info = self._get_file_metadata(file_path)
                    structure[domain_name]["files"].append(file_info)
        
        return structure
    
    def search_library(self, query: str, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search the code library for files matching the query."""
        results = []
        search_paths = []
        
        if domain:
            domain_path = self.library_base_path / domain
            if domain_path.exists():
                search_paths.append(domain_path)
        else:
            search_paths = [p for p in self.library_base_path.iterdir() if p.is_dir()]
        
        query_lower = query.lower()
        
        for search_path in search_paths:
            for file_path in search_path.rglob("*.st"):
                file_info = self._get_file_metadata(file_path)
                
                # Search in filename, description, features, and code content
                searchable_text = (
                    file_info["name"] + " " + 
                    file_info.get("description", "") + " " + 
                    " ".join(file_info.get("features", [])) + " " +
                    file_info.get("application", "")
                ).lower()
                
                if query_lower in searchable_text:
                    file_info["relevance_score"] = self._calculate_relevance(query_lower, searchable_text)
                    results.append(file_info)
        
        # Sort by relevance score
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return results
    
    def get_file_content(self, domain: str, filename: str) -> Dict[str, Any]:
        """Get the complete content and metadata of a specific ST file."""
        file_path = self.library_base_path / domain / filename
        
        if not file_path.exists() or not file_path.suffix == '.st':
            raise FileNotFoundError(f"ST file not found: {domain}/{filename}")
        
        file_info = self._get_file_metadata(file_path)
        
        # Add full source code
        with open(file_path, 'r', encoding='utf-8') as f:
            file_info["source_code"] = f.read()
        
        return file_info
    
    async def upload_user_file(
        self, 
        filename: str, 
        content: str, 
        domain: str, 
        description: Optional[str] = None,
        author: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Upload a user-contributed ST code file."""
        
        # Validate filename
        if not filename.endswith('.st'):
            filename += '.st'
        
        # Create domain directory if it doesn't exist
        domain_path = self.user_uploads_path / domain
        domain_path.mkdir(parents=True, exist_ok=True)
        
        # Create unique filename if file already exists
        file_path = domain_path / filename
        counter = 1
        original_stem = file_path.stem
        
        while file_path.exists():
            file_path = domain_path / f"{original_stem}_{counter}.st"
            counter += 1
        
        # Add metadata header to the file
        metadata_header = self._create_metadata_header(
            filename=file_path.name,
            description=description,
            author=author or "User Contribution",
            tags=tags or [],
            upload_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        full_content = metadata_header + "\n" + content
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        logger.info("User ST file uploaded", 
                   filename=str(file_path.relative_to(self.user_uploads_path)),
                   domain=domain)
        
        return self._get_file_metadata(file_path)
    
    def get_user_uploads(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all user-uploaded ST files."""
        results = []
        
        if domain:
            search_paths = [self.user_uploads_path / domain] if (self.user_uploads_path / domain).exists() else []
        else:
            search_paths = [p for p in self.user_uploads_path.iterdir() if p.is_dir()]
        
        for search_path in search_paths:
            for file_path in search_path.rglob("*.st"):
                file_info = self._get_file_metadata(file_path)
                file_info["source"] = "user_upload"
                results.append(file_info)
        
        return results
    
    def get_similar_files(self, reference_file: str, domain: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Find files similar to the reference file (simplified similarity)."""
        # This is a simplified implementation
        # In a full RAG system, this would use vector embeddings
        
        reference_path = None
        
        # Find reference file
        for search_path in [self.library_base_path, self.user_uploads_path]:
            for file_path in search_path.rglob("*.st"):
                if file_path.name == reference_file:
                    reference_path = file_path
                    break
        
        if not reference_path:
            return []
        
        reference_metadata = self._get_file_metadata(reference_path)
        reference_features = set(reference_metadata.get("features", []))
        reference_application = reference_metadata.get("application", "").lower()
        
        similar_files = []
        
        search_paths = [self.library_base_path, self.user_uploads_path]
        
        for search_path in search_paths:
            for file_path in search_path.rglob("*.st"):
                if file_path == reference_path:
                    continue
                
                file_metadata = self._get_file_metadata(file_path)
                file_features = set(file_metadata.get("features", []))
                file_application = file_metadata.get("application", "").lower()
                
                # Calculate similarity score
                feature_overlap = len(reference_features.intersection(file_features))
                application_match = 1 if reference_application in file_application or file_application in reference_application else 0
                
                similarity_score = feature_overlap + application_match
                
                if similarity_score > 0:
                    file_metadata["similarity_score"] = similarity_score
                    similar_files.append(file_metadata)
        
        # Sort by similarity and return top results
        similar_files.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_files[:limit]
    
    def delete_user_file(self, domain: str, filename: str) -> bool:
        """Delete a user-uploaded file."""
        file_path = self.user_uploads_path / domain / filename
        
        if file_path.exists() and file_path.suffix == '.st':
            file_path.unlink()
            logger.info("User ST file deleted", filename=f"{domain}/{filename}")
            return True
        
        return False
    
    def _get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from an ST file."""
        metadata = {
            "name": file_path.name,
            "path": str(file_path.relative_to(file_path.parents[2])),  # Relative to project root
            "domain": file_path.parent.name,
            "size_bytes": file_path.stat().st_size,
            "modified_date": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            "language": "structured_text"
        }
        
        # Parse header comments for metadata
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                metadata.update(self._parse_header_metadata(content))
        except Exception as e:
            logger.warning("Failed to parse file metadata", file=str(file_path), error=str(e))
        
        return metadata
    
    def _parse_header_metadata(self, content: str) -> Dict[str, Any]:
        """Parse metadata from ST file header comments."""
        metadata = {}
        lines = content.split('\n')
        
        in_header = False
        for line in lines:
            line = line.strip()
            
            if line.startswith('(*') or line.startswith('//'):
                in_header = True
            elif line.startswith('*)') or (in_header and not line.startswith('//')):
                in_header = False
                continue
            
            if in_header:
                # Remove comment markers
                clean_line = line.replace('(*', '').replace('*)', '').replace('//', '').strip()
                
                # Parse key-value pairs
                if ':' in clean_line:
                    key, value = clean_line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key in ['description', 'author', 'version', 'date', 'application']:
                        metadata[key] = value
                    elif key == 'features':
                        # Parse features list
                        features = [f.strip('- ').strip() for f in value.split('\n') if f.strip()]
                        metadata['features'] = features
        
        return metadata
    
    def _get_domain_description(self, domain_name: str) -> str:
        """Get description for a code domain."""
        descriptions = {
            "conveyor_systems": "Conveyor belt control, material handling, and transport systems",
            "safety_systems": "Safety controllers, emergency stops, and protective systems",
            "process_control": "Process automation, PID controllers, and regulatory control",
            "motor_control": "Motor drives, VFD control, and motion systems",
            "communication": "Industrial communication protocols and networking",
            "hmi_interface": "Human-machine interface and operator panels",
            "data_handling": "Data logging, SCADA integration, and information systems"
        }
        return descriptions.get(domain_name, f"ST code examples for {domain_name.replace('_', ' ')}")
    
    def _calculate_relevance(self, query: str, text: str) -> float:
        """Calculate relevance score for search results."""
        query_words = query.split()
        text_words = text.split()
        
        matches = sum(1 for word in query_words if word in text_words)
        return matches / len(query_words) if query_words else 0
    
    def _create_metadata_header(self, filename: str, description: str, author: str, tags: List[str], upload_date: str) -> str:
        """Create a metadata header for user-uploaded files."""
        header = f"""(*
====================================================================
FILE: {filename}
Description: {description or 'User-contributed ST code'}
Author: {author}
Upload Date: {upload_date}
Tags: {', '.join(tags) if tags else 'user-contribution'}
Source: User Upload
====================================================================
*)"""
        return header
"""
PDF text extraction service for vector store uploads.
"""

import logging
from typing import Optional, Dict, Any
from io import BytesIO
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import pymupdf  # PyMuPDF for PDF text extraction
    PYMUPDF_AVAILABLE = True
except ImportError:
    try:
        import fitz  # Alternative import name for PyMuPDF
        import fitz as pymupdf
        PYMUPDF_AVAILABLE = True
    except ImportError:
        PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class PDFTextExtractor:
    """Service for extracting text from PDF files."""
    
    def __init__(self):
        self.available_extractors = []
        if PYMUPDF_AVAILABLE:
            self.available_extractors.append("pymupdf")
        if PDFPLUMBER_AVAILABLE:
            self.available_extractors.append("pdfplumber")
        
        logger.info(f"PDF extractors available: {self.available_extractors}")
    
    def extract_text_from_pdf(self, pdf_content: BytesIO, filename: str) -> Optional[Dict[str, Any]]:
        """
        Extract text from PDF content.
        
        Args:
            pdf_content: PDF file content as BytesIO
            filename: Original filename for logging
            
        Returns:
            Dict with extracted text and metadata, or None if extraction fails
        """
        if not self.available_extractors:
            logger.error("No PDF extraction libraries available")
            return None
        
        # Try extractors in order of preference
        for extractor in self.available_extractors:
            try:
                if extractor == "pymupdf":
                    return self._extract_with_pymupdf(pdf_content, filename)
                elif extractor == "pdfplumber":
                    return self._extract_with_pdfplumber(pdf_content, filename)
            except Exception as e:
                logger.warning(f"PDF extraction with {extractor} failed for {filename}: {e}")
                continue
        
        logger.error(f"All PDF extraction methods failed for {filename}")
        return None
    
    def _extract_with_pymupdf(self, pdf_content: BytesIO, filename: str) -> Dict[str, Any]:
        """Extract text using PyMuPDF."""
        pdf_content.seek(0)
        pdf_bytes = pdf_content.read()
        
        # Open PDF from bytes
        doc = pymupdf.open("pdf", pdf_bytes)
        
        extracted_text = []
        metadata = {
            "page_count": len(doc),
            "title": doc.metadata.get("title", ""),
            "subject": doc.metadata.get("subject", ""),
            "author": doc.metadata.get("author", ""),
        }
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                extracted_text.append(f"=== PAGE {page_num + 1} ===\n{text}\n")
        
        doc.close()
        
        full_text = "\n".join(extracted_text)
        
        logger.info(f"PyMuPDF extracted {len(full_text)} characters from {filename} ({metadata['page_count']} pages)")
        
        return {
            "text": full_text,
            "metadata": metadata,
            "extractor": "pymupdf",
            "character_count": len(full_text)
        }
    
    def _extract_with_pdfplumber(self, pdf_content: BytesIO, filename: str) -> Dict[str, Any]:
        """Extract text using pdfplumber with enhanced table detection."""
        pdf_content.seek(0)
        
        extracted_text = []
        metadata = {"page_count": 0, "table_count": 0}
        tables_found = []
        
        with pdfplumber.open(pdf_content) as pdf:
            metadata["page_count"] = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages):
                page_content = []
                page_content.append(f"=== PAGE {page_num + 1} ===\n")
                
                # Extract tables first
                try:
                    tables = page.extract_tables()
                    if tables:
                        metadata["table_count"] += len(tables)
                        for table_num, table in enumerate(tables):
                            if table and len(table) > 0:
                                # Convert table to markdown format
                                markdown_table = self._table_to_markdown(table, page_num + 1, table_num + 1)
                                page_content.append(markdown_table)
                                tables_found.append({
                                    "page": page_num + 1,
                                    "table": table_num + 1,
                                    "rows": len(table),
                                    "cols": len(table[0]) if table[0] else 0
                                })
                except Exception as e:
                    logger.warning(f"Table extraction failed on page {page_num + 1}: {e}")
                
                # Extract regular text
                text = page.extract_text()
                if text and text.strip():
                    # Remove text that's already captured in tables to avoid duplication
                    page_content.append(f"\n## Text Content:\n{text}\n")
                
                extracted_text.append("\n".join(page_content))
        
        full_text = "\n".join(extracted_text)
        
        logger.info(f"pdfplumber extracted {len(full_text)} characters from {filename} ({metadata['page_count']} pages, {metadata['table_count']} tables)")
        
        return {
            "text": full_text,
            "metadata": metadata,
            "extractor": "pdfplumber_enhanced",
            "character_count": len(full_text),
            "tables_found": tables_found
        }
    
    def _table_to_markdown(self, table: list, page_num: int, table_num: int) -> str:
        """Convert a table to markdown format for better readability."""
        
        if not table or len(table) == 0:
            return ""
        
        markdown_lines = []
        markdown_lines.append(f"\n### Table {table_num} (Page {page_num})\n")
        
        # Handle header row
        header_row = table[0]
        if header_row:
            # Clean and format header
            headers = [str(cell).strip() if cell else "" for cell in header_row]
            markdown_lines.append("| " + " | ".join(headers) + " |")
            markdown_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # Handle data rows
        for row in table[1:]:
            if row:
                # Clean and format data cells
                cells = [str(cell).strip() if cell else "" for cell in row]
                # Ensure we have the same number of cells as headers
                while len(cells) < len(headers):
                    cells.append("")
                markdown_lines.append("| " + " | ".join(cells) + " |")
        
        markdown_lines.append("")  # Add blank line after table
        return "\n".join(markdown_lines)
    
    def create_text_file_content(self, extracted_data: Dict[str, Any], original_filename: str) -> str:
        """Create formatted text file content from extracted PDF data."""
        
        text_content = f"""# Extracted from: {original_filename}

## Document Information
- Extractor: {extracted_data.get('extractor', 'unknown')}
- Pages: {extracted_data.get('metadata', {}).get('page_count', 0)}
- Characters: {extracted_data.get('character_count', 0)}
"""
        
        # Add metadata if available
        metadata = extracted_data.get('metadata', {})
        if metadata.get('title'):
            text_content += f"- Title: {metadata['title']}\n"
        if metadata.get('author'):
            text_content += f"- Author: {metadata['author']}\n"
        if metadata.get('subject'):
            text_content += f"- Subject: {metadata['subject']}\n"
        
        # Add table information if available
        if metadata.get('table_count', 0) > 0:
            text_content += f"- Tables Found: {metadata['table_count']}\n"
            
            # List tables found for reference
            tables_found = extracted_data.get('tables_found', [])
            if tables_found:
                text_content += "\n## Tables Summary\n"
                for table_info in tables_found:
                    text_content += f"- Page {table_info['page']}, Table {table_info['table']}: {table_info['rows']} rows × {table_info['cols']} columns\n"
        
        text_content += f"\n## Extracted Text Content\n\n{extracted_data['text']}"
        
        # Add extraction notes
        text_content += f"\n\n## Extraction Notes\n"
        text_content += f"- This document was automatically processed for PLC programming assistance\n"
        text_content += f"- Tables have been converted to markdown format for better structure\n"
        text_content += f"- Technical specifications should be preserved in table format\n"
        
        return text_content
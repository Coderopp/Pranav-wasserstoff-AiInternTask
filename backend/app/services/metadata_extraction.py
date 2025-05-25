import os
import re
from datetime import datetime
from typing import Optional
from fastapi import UploadFile

from app.models.schemas import DocumentMetadata

class MetadataExtractor:
    """Extracts metadata from files"""
    
    @staticmethod
    def extract_from_file(file: UploadFile) -> DocumentMetadata:
        """Extract metadata from uploaded file"""
        # Get file size
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
        
        # Extract filename components
        filename = file.filename
        author = MetadataExtractor._extract_author(filename)
        document_date = MetadataExtractor._extract_date(filename)
        document_type = filename.split('.')[-1].lower()
        
        return DocumentMetadata(
            filename=filename,
            content_type=file.content_type,
            file_size=file_size,
            upload_date=datetime.utcnow().isoformat(),
            author=author,
            document_date=document_date,
            document_type=document_type
        )
    
    @staticmethod
    def _extract_author(filename: str) -> Optional[str]:
        """Extract author from filename pattern"""
        filename_parts = filename.split('_')
        if len(filename_parts) >= 3:
            return filename_parts[0].replace('.', ' ')
        return None
    
    @staticmethod
    def _extract_date(filename: str) -> Optional[str]:
        """Extract date from filename pattern"""
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            return date_match.group(1)
        return None
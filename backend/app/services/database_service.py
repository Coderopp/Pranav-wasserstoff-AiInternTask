import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from app.models.schemas import ProcessedDocument

logger = logging.getLogger(__name__)

class DatabaseService:
    """Simple file-based database for document storage"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.documents_dir = self.data_dir / "documents"
        self.metadata_dir = self.data_dir / "metadata"
        
        # Create directories
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
    
    def save_document(self, document: ProcessedDocument) -> bool:
        """Save processed document to database"""
        try:
            # Convert dataclasses to dict for JSON serialization
            doc_data = {
                "id": document.id,
                "full_text": document.full_text,
                "pages": [
                    {
                        "page_number": page.page_number,
                        "paragraphs": [
                            {
                                "text": para.text,
                                "position": {
                                    "page": para.position.page,
                                    "paragraph_index": para.position.paragraph_index,
                                    "rect": para.position.rect,
                                    "is_ocr": para.position.is_ocr
                                }
                            }
                            for para in page.paragraphs
                        ],
                        "full_text": page.full_text
                    }
                    for page in document.pages
                ],
                "metadata": {
                    "filename": document.metadata.filename,
                    "content_type": document.metadata.content_type,
                    "file_size": document.metadata.file_size,
                    "upload_date": document.metadata.upload_date,
                    "author": document.metadata.author,
                    "document_date": document.metadata.document_date,
                    "document_type": document.metadata.document_type,
                    "processing_status": document.metadata.processing_status,
                    "segment_count": document.metadata.segment_count,
                    "page_count": document.metadata.page_count
                }
            }
            
            # Save to file
            doc_file = self.documents_dir / f"{document.id}.json"
            with open(doc_file, 'w', encoding='utf-8') as f:
                json.dump(doc_data, f, indent=2)
            
            logger.info(f"Successfully saved document {document.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save document {document.id}: {str(e)}")
            return False
    
    def get_document(self, document_id: str) -> Optional[ProcessedDocument]:
        """Retrieve document by ID"""
        try:
            doc_file = self.documents_dir / f"{document_id}.json"
            if not doc_file.exists():
                return None
            
            with open(doc_file, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
            
            # Convert back to dataclass objects
            # This would require proper reconstruction - simplified for example
            return doc_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve document {document_id}: {str(e)}")
            return None
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Retrieve all documents"""
        try:
            documents = []
            for doc_file in self.documents_dir.glob("*.json"):
                with open(doc_file, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
                    documents.append(doc_data)
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to retrieve all documents: {str(e)}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document by ID"""
        try:
            doc_file = self.documents_dir / f"{document_id}.json"
            if doc_file.exists():
                doc_file.unlink()
                logger.info(f"Successfully deleted document {document_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            return False
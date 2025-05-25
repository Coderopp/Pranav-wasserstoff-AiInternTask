import uuid
from typing import Dict, Any, Optional
import logging

from fastapi import UploadFile

from app.models.schemas import ProcessedDocument, DocumentMetadata
from app.services.text_extraction import TextExtractor
from app.services.metadata_extraction import MetadataExtractor
from app.services.vector_store import VectorStoreService
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Main orchestrator for document processing workflow"""
    
    def __init__(self, vector_store: VectorStoreService, database: DatabaseService):
        self.vector_store = vector_store
        self.database = database
        self.text_extractor = TextExtractor()
        self.metadata_extractor = MetadataExtractor()
    
    async def process_document(self, file: UploadFile) -> ProcessedDocument:
        """Process uploaded document through complete workflow"""
        logger.info(f"Starting document processing for: {file.filename}")
        
        try:
            # Extract text and structure from the file
            document = await self.text_extractor.extract_from_file(file)
            document.id = str(uuid.uuid4())
            
            logger.info(f"Extracted {len(document.pages)} pages from {file.filename}")
            
            # Extract metadata from the file
            metadata = self.metadata_extractor.extract_from_file(file)
            document.metadata = metadata
            document.metadata.processing_status = "processed"
            document.metadata.page_count = len(document.pages)
            
            # Save document to database first
            logger.info(f"Saving document {document.id} to database")
            if not self.database.save_document(document):
                raise Exception("Failed to save document to database")
            
            # Now try to index it in the vector store
            logger.info(f"Indexing document {document.id} in vector store")
            
            if self._has_indexable_content(document):
                try:
                    success = self.vector_store.index_document(document)
                    if success:
                        document.metadata.processing_status = "indexed"
                        logger.info(f"Successfully indexed document {document.id}")
                    else:
                        document.metadata.processing_status = "indexing_failed"
                        logger.warning(f"Vector store rejected document {document.id}")
                        
                except Exception as e:
                    document.metadata.processing_status = "indexing_failed"
                    logger.error(f"Indexing failed for {document.id}: {str(e)}")
            else:
                document.metadata.processing_status = "indexing_failed"
                logger.warning(f"Document {document.id} has no content to index")
            
            # Update the final status in database
            self.database.save_document(document)
            
            logger.info(f"Finished processing {document.id} with status: {document.metadata.processing_status}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {str(e)}")
            raise
    
    def _has_indexable_content(self, document: ProcessedDocument) -> bool:
        """Check if document has content worth indexing"""
        if not document.pages:
            return False
        
        # Check if any page has actual text content
        for page in document.pages:
            if hasattr(page, 'content') and page.content and page.content.strip():
                return True
            elif hasattr(page, 'text') and page.text and page.text.strip():
                return True
        
        return False
    
    def retry_indexing(self, document_id: str) -> bool:
        """Retry indexing for a document that failed previously"""
        try:
            logger.info(f"Retrying indexing for document {document_id}")
            
            # Get document from database
            document_data = self.database.get_document(document_id)
            if not document_data:
                logger.error(f"Document {document_id} not found")
                return False
                
            logger.info(f"Retrieved document {document_id} from database")
            
            # Check if we have all the required document structure
            if not document_data.get("id") or not document_data.get("pages") or not document_data.get("metadata"):
                logger.error(f"Document {document_id} has incomplete structure")
                return False
                
            # Convert raw document data to ProcessedDocument if needed
            if not isinstance(document_data, ProcessedDocument):
                try:
                    # Create metadata object
                    metadata_dict = document_data.get("metadata", {})
                    metadata = DocumentMetadata(
                        filename=metadata_dict.get("filename", "unknown"),
                        content_type=metadata_dict.get("content_type", "application/octet-stream"),
                        file_size=metadata_dict.get("file_size", 0),
                        upload_date=metadata_dict.get("upload_date", ""),
                        author=metadata_dict.get("author"),
                        document_date=metadata_dict.get("document_date"),
                        document_type=metadata_dict.get("document_type"),
                        processing_status=metadata_dict.get("processing_status", "pending"),
                        segment_count=metadata_dict.get("segment_count", 0),
                        page_count=metadata_dict.get("page_count", 0)
                    )
                    
                    # Create processed document
                    processed_document = ProcessedDocument(
                        id=document_data.get("id"),
                        full_text=document_data.get("full_text", ""),
                        pages=document_data.get("pages", []),
                        metadata=metadata
                    )
                    
                    logger.info(f"Successfully created ProcessedDocument from raw data for {document_id}")
                    
                except Exception as e:
                    logger.error(f"Error converting document data to ProcessedDocument: {str(e)}")
                    # Continue with raw document data as a fallback
                    processed_document = document_data
                    logger.info("Using raw document data as fallback")
            else:
                processed_document = document_data
            
            # Try indexing again
            logger.info(f"Attempting to index document {document_id}...")
            vector_success = self.vector_store.index_document(processed_document)
            
            if vector_success:
                # Update status in database
                if isinstance(document_data, dict):
                    document_data["metadata"]["processing_status"] = "indexed"
                    self.database.save_document(document_data)
                else:
                    document_data.metadata.processing_status = "indexed"
                    self.database.save_document(document_data)
                    
                logger.info(f"Successfully indexed document {document_id} on retry")
                return True
            else:
                logger.error(f"Failed to index document {document_id} on retry")
                return False
                
        except Exception as e:
            logger.error(f"Error retrying indexing for document {document_id}: {str(e)}")
            return False
    
    def get_document(self, document_id: str) -> Optional[ProcessedDocument]:
        """Get a processed document by ID"""
        document_data = self.database.get_document(document_id)
        if not document_data:
            return None
        
        if isinstance(document_data, dict):
            return self._dict_to_document(document_data)
        
        return document_data
    
    def get_all_documents(self) -> Dict[str, Any]:
        """Get overview of all documents"""
        try:
            documents = self.database.get_all_documents()
            overview = []
            
            for doc in documents:
                overview.append({
                    "id": doc["id"],
                    "filename": doc["metadata"]["filename"],
                    "metadata": doc["metadata"]
                })
            
            return {
                "documents": overview,
                "count": len(overview)
            }
        except Exception as e:
            logger.error(f"Failed to get document overview: {str(e)}")
            return {"documents": [], "count": 0}
    
    def debug_document_content(self, document_id: str) -> Dict[str, Any]:
        """Debug helper to inspect document content structure"""
        doc = self.get_document(document_id)
        if not doc:
            return {"error": "Document not found"}
        
        page_info = []
        total_chars = 0
        
        for i, page in enumerate(doc.pages):
            page_content = ""
            
            # Try different possible content attributes
            if hasattr(page, 'content'):
                page_content = page.content or ""
            elif hasattr(page, 'text'):
                page_content = page.text or ""
            
            page_info.append({
                "page": i + 1,
                "content_length": len(page_content),
                "has_content": bool(page_content.strip()),
                "preview": page_content[:100] if page_content else "No content"
            })
            total_chars += len(page_content)
        
        return {
            "document_id": doc.id,
            "total_pages": len(doc.pages),
            "total_content_chars": total_chars,
            "pages": page_info[:3]  # Show first 3 pages
        }
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document from all systems"""
        try:
            success = self.database.delete_document(document_id)
            if success:
                logger.info(f"Deleted document {document_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            return False
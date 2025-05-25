from fastapi import APIRouter, UploadFile, HTTPException, status, Depends
from typing import Dict, Any, List
import logging

from app.models.schemas import DocumentResponse
from app.core.document_processor import DocumentProcessor

router = APIRouter(prefix="/api/documents", tags=["documents"])

logger = logging.getLogger(__name__)

# This function is replaced during FastAPI initialization via dependency_overrides
def get_document_processor() -> DocumentProcessor:
    """Dependency to get document processor instance"""
    logger.error("Default get_document_processor called - this should be overridden!")
    raise RuntimeError("Document processor dependency not properly configured")

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile,
    processor: DocumentProcessor = Depends(get_document_processor)
) -> Dict[str, Any]:
    """Upload and process a document"""
    
    # Validate file type
    allowed_extensions = {"pdf", "png", "jpg", "jpeg", "tiff"}
    file_ext = file.filename.split('.')[-1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        logger.info(f"Processing document: {file.filename}")
        
        # Add more info logging to debug the issue
        if processor is None:
            logger.error("Document processor is None in upload_document handler")
            raise ValueError("Document processor dependency is None")
            
        document = await processor.process_document(file)
        logger.info(f"Document processed successfully with ID: {document.id}")
        
        return DocumentResponse(
            document_id=document.id,
            status="success",
            filename=document.metadata.filename,
            metadata={
                "filename": document.metadata.filename,
                "content_type": document.metadata.content_type,
                "file_size": document.metadata.file_size,
                "upload_date": document.metadata.upload_date,
                "processing_status": document.metadata.processing_status,
                "page_count": document.metadata.page_count
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )

@router.get("/{document_id}")
async def get_document(
    document_id: str,
    processor: DocumentProcessor = Depends(get_document_processor)
) -> Dict[str, Any]:
    """Retrieve a document by ID"""
    
    try:
        document = processor.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        return {
            "document_id": document["id"],
            "status": "success",
            "filename": document["metadata"]["filename"],
            "metadata": document["metadata"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document {document_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving document: {str(e)}"
        )

@router.get("/")
async def list_documents(
    processor: DocumentProcessor = Depends(get_document_processor)
) -> Dict[str, Any]:
    """List all documents"""
    
    try:
        return processor.get_all_documents()
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    processor: DocumentProcessor = Depends(get_document_processor)
):
    """Delete a document"""
    
    try:
        success = await processor.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )

@router.post("/{document_id}/retry-indexing")
async def retry_document_indexing(
    document_id: str,
    processor: DocumentProcessor = Depends(get_document_processor)
) -> Dict[str, Any]:
    """Retry indexing a document that previously failed"""
    
    try:
        success = processor.retry_indexing(document_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to index document {document_id}"
            )
        
        # Get updated document
        document = processor.get_document(document_id)
        
        return {
            "document_id": document_id,
            "status": "success",
            "message": "Document indexed successfully",
            "processing_status": document["metadata"]["processing_status"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying indexing for {document_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrying indexing: {str(e)}"
        )

# Health check for document services
@router.get("/health")
@router.head("/health")
async def document_service_health(
    processor: DocumentProcessor = Depends(get_document_processor)
) -> Dict[str, Any]:
    """Health check for document services"""
    
    try:
        # Test basic functionality
        documents = processor.get_all_documents()
        return {
            "status": "healthy",
            "service": "document_processor",
            "document_count": documents.get("count", 0)
        }
    except Exception as e:
        logger.error(f"Document service health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "document_processor",
            "error": str(e)
        }
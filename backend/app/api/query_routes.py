from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
import logging

from app.models.schemas import (
    QueryRequest, QueryResponse, EnhancedQueryResponse, 
    ThemeResponse, DocumentListResponse, DocumentSearchRequest, DocumentSearchResponse,
    DocumentSelectionRequest, DocumentSelectionResponse
)
from app.core.query_engine import QueryEngine

router = APIRouter(prefix="/api/queries", tags=["queries"])
logger = logging.getLogger(__name__)

# This function is replaced during FastAPI initialization via dependency_overrides
def get_query_engine() -> QueryEngine:
    """Dependency to get query engine instance"""
    logger.error("Default get_query_engine called - this should be overridden!")
    raise RuntimeError("Query engine dependency not properly configured")

@router.post("/search", response_model=QueryResponse)
async def search_documents(
    request: QueryRequest,
    engine: QueryEngine = Depends(get_query_engine)
) -> QueryResponse:
    """Process a natural language query"""
    
    try:
        # Add more info logging to debug the issue
        if engine is None:
            logger.error("Query engine is None in search_documents handler")
            raise ValueError("Query engine dependency is None")
            
        return engine.process_query(
            request.query, 
            request.filters, 
            request.selected_document_ids
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )

@router.post("/enhanced-search", response_model=EnhancedQueryResponse)
async def search_documents_enhanced(
    request: QueryRequest,
    engine: QueryEngine = Depends(get_query_engine)
) -> EnhancedQueryResponse:
    """Process query with enhanced citations"""
    
    try:
        return engine.process_enhanced_query(
            request.query, 
            request.filters, 
            request.selected_document_ids
        )
    except Exception as e:
        logger.error(f"Error processing enhanced query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing enhanced query: {str(e)}"
        )

@router.get("/themes")
@router.get("/themes/{document_id}")
async def get_themes(
    document_id: str = None,
    engine: QueryEngine = Depends(get_query_engine)
) -> ThemeResponse:
    """Extract themes from documents"""
    
    try:
        if document_id:
            return engine.extract_themes_for_document(document_id)
        else:
            return engine.extract_all_themes()
    except Exception as e:
        logger.error(f"Error extracting themes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting themes: {str(e)}"
        )

@router.post("/documents/search", response_model=DocumentSearchResponse)
async def search_and_filter_documents(
    request: DocumentSearchRequest,
    engine: QueryEngine = Depends(get_query_engine)
) -> DocumentSearchResponse:
    """Search and filter documents based on various criteria"""
    
    try:
        result = engine.search_documents(request)
        return DocumentSearchResponse(**result)
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching documents: {str(e)}"
        )

@router.get("/documents", response_model=DocumentListResponse)
async def list_all_documents(
    engine: QueryEngine = Depends(get_query_engine)
) -> DocumentListResponse:
    """List all documents in the system"""
    
    try:
        return engine.list_all_documents()
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )

@router.post("/documents/select", response_model=DocumentSelectionResponse)
async def validate_document_selection(
    request: DocumentSelectionRequest,
    engine: QueryEngine = Depends(get_query_engine)
) -> DocumentSelectionResponse:
    """Validate and confirm document selection for queries"""
    
    try:
        # Get all documents to validate the selected IDs
        all_docs_result = engine.list_all_documents()
        all_documents = all_docs_result.get("documents", [])
        
        # Create a map of document IDs to documents
        doc_map = {doc["id"]: doc for doc in all_documents}
        
        # Validate selected document IDs
        selected_documents = []
        invalid_ids = []
        
        for doc_id in request.document_ids:
            if doc_id in doc_map:
                selected_documents.append(doc_map[doc_id])
            else:
                invalid_ids.append(doc_id)
        
        if invalid_ids:
            logger.warning(f"Invalid document IDs provided: {invalid_ids}")
            return DocumentSelectionResponse(
                selected_documents=selected_documents,
                count=len(selected_documents),
                status=f"partial_success - {len(invalid_ids)} invalid IDs: {invalid_ids}"
            )
        
        return DocumentSelectionResponse(
            selected_documents=selected_documents,
            count=len(selected_documents),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error validating document selection: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating document selection: {str(e)}"
        )

# Health check for query services
@router.get("/health")
@router.head("/health")
async def query_service_health(
    engine: QueryEngine = Depends(get_query_engine)
) -> Dict[str, Any]:
    """Health check for query services"""
    
    try:
        # Test basic functionality
        test_result = engine.test_connection()
        return {
            "status": "healthy" if test_result else "unhealthy",
            "service": "query_engine",
            "vector_store_connected": test_result
        }
    except Exception as e:
        logger.error(f"Query service health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "query_engine",
            "error": str(e)
        }
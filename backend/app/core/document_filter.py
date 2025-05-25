from typing import List, Dict, Any, Optional
import logging

from app.models.schemas import DocumentChunk

logger = logging.getLogger(__name__)

class DocumentFilter:
    """Filters documents based on criteria"""
    
    @staticmethod
    def apply_filters(chunks: List[DocumentChunk], filters: Optional[Dict[str, Any]]) -> List[DocumentChunk]:
        """Apply filters to document chunks"""
        if not filters:
            return chunks
        
        filtered_chunks = []
        for chunk in chunks:
            if DocumentFilter._should_include_chunk(chunk, filters):
                filtered_chunks.append(chunk)
        
        return filtered_chunks
    
    @staticmethod
    def _should_include_chunk(chunk: DocumentChunk, filters: Dict[str, Any]) -> bool:
        """Check if chunk should be included based on filters"""
        for key, value in filters.items():
            if key == "date_range" and isinstance(value, dict):
                if not DocumentFilter._check_date_range(chunk, value):
                    return False
            elif key == "relevance_threshold" and isinstance(value, (int, float)):
                if chunk.similarity_score < value:
                    return False
            elif key == "document_ids" and isinstance(value, list):
                if chunk.metadata.get("doc_id") not in value:
                    return False
            elif key in chunk.metadata:
                if not DocumentFilter._check_metadata_filter(chunk.metadata[key], value):
                    return False
        
        return True
    
    @staticmethod
    def _check_date_range(chunk: DocumentChunk, date_range: Dict[str, Any]) -> bool:
        """Check if chunk falls within date range"""
        doc_date = chunk.metadata.get("document_date")
        if not doc_date:
            return True
        
        start_date = date_range.get("start")
        end_date = date_range.get("end")
        
        if start_date and doc_date < start_date:
            return False
        if end_date and doc_date > end_date:
            return False
        
        return True
    
    @staticmethod
    def _check_metadata_filter(metadata_value: Any, filter_value: Any) -> bool:
        """Check if metadata value matches filter criteria"""
        if isinstance(filter_value, list):
            return metadata_value in filter_value
        return metadata_value == filter_value
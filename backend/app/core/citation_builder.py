from typing import List
import logging

from app.models.schemas import DocumentChunk, Citation, EnhancedCitation, EmbeddingInfo

logger = logging.getLogger(__name__)

class CitationBuilder:
    """Builds citations from document chunks"""
    
    @staticmethod
    def create_basic_citations(chunks: List[DocumentChunk]) -> List[Citation]:
        """Create basic citations from document chunks"""
        citations = []
        for chunk in chunks:
            citation = Citation(
                doc_id=chunk.metadata.get("doc_id", "Unknown"),
                document_name=chunk.metadata.get("filename", "Unknown"),
                page_number=chunk.metadata.get("page_number"),
                paragraph_number=chunk.metadata.get("paragraph_number"),
                content_snippet=CitationBuilder._create_snippet(chunk.content),
                position_rect=chunk.metadata.get("position", {}).get("rect")
            )
            citations.append(citation)
        return citations
    
    @staticmethod
    def create_enhanced_citations(chunks: List[DocumentChunk], vector_results: List) -> List[EnhancedCitation]:
        """Create enhanced citations with embedding information"""
        citations = []
        for i, chunk in enumerate(chunks):
            embedding_info = None
            if i < len(vector_results):
                result = vector_results[i]
                embedding_info = EmbeddingInfo(
                    vector_id=str(result.id),
                    similarity_score=result.score,
                    dimension=768,  # This should come from config
                    model_name="embedding-model"  # This should come from config
                )
            
            citation = EnhancedCitation(
                doc_id=chunk.metadata.get("doc_id", "Unknown"),
                document_name=chunk.metadata.get("filename", "Unknown"),
                page_number=chunk.metadata.get("page_number"),
                paragraph_number=chunk.metadata.get("paragraph_number"),
                content_snippet=CitationBuilder._create_snippet(chunk.content),
                position_rect=chunk.metadata.get("position", {}).get("rect"),
                embedding_info=embedding_info
            )
            citations.append(citation)
        return citations
    
    @staticmethod
    def _create_snippet(content: str, max_length: int = 200) -> str:
        """Create a content snippet"""
        if len(content) > max_length:
            return content[:max_length] + "..."
        return content
from typing import List, Dict, Any, Optional
import logging

from app.models.schemas import (
    QueryResponse, EnhancedQueryResponse, ThemeResponse, 
    DocumentListResponse, DocumentChunk
)
from app.services.vector_store import VectorStoreService
from app.services.llm_service import LLMService
from app.core.citation_builder import CitationBuilder
from app.core.document_filter import DocumentFilter

logger = logging.getLogger(__name__)

class QueryEngine:
    """Main orchestrator for query processing and search"""
    
    def __init__(self, vector_store: VectorStoreService, llm_service: LLMService):
        self.vector_store = vector_store
        self.llm_service = llm_service
        self.citation_builder = CitationBuilder()
        self.document_filter = DocumentFilter()
    
    def _convert_to_document_chunks(self, langchain_docs) -> List[DocumentChunk]:
        """Convert LangChain Document objects to DocumentChunk objects"""
        chunks = []
        for doc in langchain_docs:
            # Handle both LangChain Document objects and already converted chunks
            if hasattr(doc, 'page_content'):
                # LangChain Document object
                chunk = DocumentChunk(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    similarity_score=0.0
                )
            elif hasattr(doc, 'content'):
                # Already a DocumentChunk
                chunk = doc
            else:
                # Fallback for other types
                logger.warning(f"Unknown document type: {type(doc)}")
                continue
            chunks.append(chunk)
        return chunks
    
    def process_query(self, query: str, filters: Optional[Dict[str, Any]] = None, selected_document_ids: Optional[List[str]] = None) -> QueryResponse:
        """Process a natural language query with citations"""
        logger.info(f"Processing query: {query[:100]}...")
        
        try:
            # Step 1: Search for relevant documents
            raw_results = self.vector_store.similarity_search(query, k=10)
            chunks = self._convert_to_document_chunks(raw_results)
            logger.info(f"Found {len(chunks)} initial results")
            
            # Step 2: Filter by selected documents if provided
            if selected_document_ids:
                chunks = [
                    chunk for chunk in chunks 
                    if chunk.metadata.get("doc_id") in selected_document_ids
                ]
                logger.info(f"After document selection filtering: {len(chunks)} results")
            
            # Step 3: Apply other filters
            filtered_chunks = self.document_filter.apply_filters(chunks, filters)
            logger.info(f"After additional filtering: {len(filtered_chunks)} results")
            
            if not filtered_chunks:
                message = "No relevant documents found matching the criteria."
                if selected_document_ids:
                    message += f" Search was limited to {len(selected_document_ids)} selected documents."
                return QueryResponse(
                    answers=[message],
                    citations=[],
                    metadata={
                        "query": query, 
                        "filters": filters, 
                        "selected_document_ids": selected_document_ids,
                        "total_results": 0
                    }
                )
            
            # Step 4: Generate context and get answer
            context = "\n\n".join([chunk.content for chunk in filtered_chunks])
            answer = self.llm_service.answer_query(query, context)
            
            # Step 5: Create citations
            citations = self.citation_builder.create_basic_citations(filtered_chunks)
            
            return QueryResponse(
                answers=[answer],
                citations=citations,
                metadata={
                    "query": query,
                    "filters": filters,
                    "selected_document_ids": selected_document_ids,
                    "total_results": len(filtered_chunks),
                    "documents_searched": len(selected_document_ids) if selected_document_ids else "all"
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise
    
    def process_enhanced_query(self, query: str, filters: Optional[Dict[str, Any]] = None, selected_document_ids: Optional[List[str]] = None) -> EnhancedQueryResponse:
        """Process query with enhanced citation information"""
        logger.info(f"Processing enhanced query: {query[:100]}...")
        
        try:
            # Similar to process_query but with enhanced citations
            raw_results = self.vector_store.similarity_search(query, k=10)
            chunks = self._convert_to_document_chunks(raw_results)
            
            # Filter by selected documents if provided
            if selected_document_ids:
                chunks = [
                    chunk for chunk in chunks 
                    if chunk.metadata.get("doc_id") in selected_document_ids
                ]
            
            filtered_chunks = self.document_filter.apply_filters(chunks, filters)
            
            if not filtered_chunks:
                message = "No relevant documents found matching the criteria."
                if selected_document_ids:
                    message += f" Search was limited to {len(selected_document_ids)} selected documents."
                return EnhancedQueryResponse(
                    answers=[message],
                    citations=[],
                    metadata={
                        "query": query, 
                        "filters": filters, 
                        "selected_document_ids": selected_document_ids,
                        "total_results": 0
                    }
                )
            
            context = "\n\n".join([chunk.content for chunk in filtered_chunks])
            answer = self.llm_service.answer_query(query, context)
            
            # Create enhanced citations (would need vector results for full implementation)
            enhanced_citations = self.citation_builder.create_enhanced_citations(filtered_chunks, [])
            
            return EnhancedQueryResponse(
                answers=[answer],
                citations=enhanced_citations,
                metadata={
                    "query": query,
                    "filters": filters,
                    "selected_document_ids": selected_document_ids,
                    "total_results": len(filtered_chunks),
                    "documents_searched": len(selected_document_ids) if selected_document_ids else "all"
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing enhanced query: {str(e)}")
            raise
    
    def extract_themes(self, query: str, filters: Optional[Dict[str, Any]] = None) -> ThemeResponse:
        """Extract themes from documents based on query"""
        logger.info(f"Extracting themes for query: {query[:100]}...")
        
        try:
            # Get broader set of documents for theme analysis
            raw_results = self.vector_store.similarity_search(query, k=20)
            chunks = self._convert_to_document_chunks(raw_results)
            filtered_chunks = self.document_filter.apply_filters(chunks, filters)
            
            if not filtered_chunks:
                return ThemeResponse(
                    themes=[],
                    supporting_documents={},
                    detailed_citations={},
                    metadata={"query": query, "filters": filters, "total_results": 0}
                )
            
            # Prepare text for theme extraction
            documents_text = "\n\n".join([
                f"Document {i+1}: {chunk.content[:500]}..."
                for i, chunk in enumerate(filtered_chunks)
            ])
            
            # Extract themes using LLM
            themes_data = self.llm_service.extract_themes(documents_text)
            
            # Organize results
            theme_names = [theme.get("theme_name", "") for theme in themes_data]
            supporting_documents = {}
            detailed_citations = {}
            
            for theme in themes_data:
                theme_name = theme.get("theme_name", "")
                doc_indices = theme.get("document_indices", [])
                
                # Map indices to document IDs
                supporting_docs = []
                theme_chunks = []
                
                for idx in doc_indices:
                    if idx < len(filtered_chunks):
                        chunk = filtered_chunks[idx]
                        doc_id = chunk.metadata.get("doc_id", "Unknown")
                        supporting_docs.append(doc_id)
                        theme_chunks.append(chunk)
                
                supporting_documents[theme_name] = supporting_docs
                detailed_citations[theme_name] = self.citation_builder.create_basic_citations(theme_chunks)
            
            return ThemeResponse(
                themes=theme_names,
                supporting_documents=supporting_documents,
                detailed_citations=detailed_citations,
                metadata={
                    "query": query,
                    "filters": filters,
                    "total_results": len(filtered_chunks)
                }
            )
            
        except Exception as e:
            logger.error(f"Error extracting themes: {str(e)}")
            raise
    
    def list_all_documents(self) -> DocumentListResponse:
        """List all documents in the system"""
        try:
            vector_result = self.vector_store.list_all_documents()
            
            # Convert the vector store format to the format expected by the frontend
            documents_list = []
            
            for doc_id, doc_data in vector_result["documents"].items():
                # Transform to match frontend Document interface
                document = {
                    "id": doc_id,
                    "filename": doc_data.get("filename", "Unknown"),
                    "status": doc_data.get("status", "completed"),
                    "upload_timestamp": doc_data.get("upload_timestamp", "Unknown"),
                    "metadata": doc_data.get("metadata", {})
                }
                documents_list.append(document)
            
            # Return in the format expected by DocumentListResponse but adapted for frontend
            return {
                "documents": documents_list,  # Return as list instead of dict
                "count": len(documents_list)
            }
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return {
                "documents": [],  # Return empty list instead of empty dict
                "count": 0
            }
    
    def test_connection(self) -> bool:
        """Test the connection to underlying services"""
        try:
            # Test vector store connection
            test_result = self.vector_store.health_check()
            return test_result
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    def extract_themes_for_document(self, document_id: str) -> ThemeResponse:
        """Extract themes for a specific document"""
        try:
            # Get chunks for specific document
            raw_chunks = self.vector_store.get_chunks_by_document_id(document_id)
            
            # Convert to DocumentChunk objects
            chunks = []
            for chunk_data in raw_chunks:
                chunk = DocumentChunk(
                    content=chunk_data.get("content", ""),
                    metadata=chunk_data.get("metadata", {}),
                    similarity_score=chunk_data.get("score", 0.0)
                )
                chunks.append(chunk)
            
            if not chunks:
                return ThemeResponse(
                    themes=[],
                    supporting_documents={},
                    detailed_citations={},
                    metadata={"document_id": document_id, "total_results": 0}
                )
            
            # Prepare text for theme extraction
            documents_text = "\n\n".join([
                f"Chunk {i+1}: {chunk.content[:500]}..."
                for i, chunk in enumerate(chunks)
            ])
            
            # Extract themes using LLM
            themes_data = self.llm_service.extract_themes(documents_text)
            
            # Organize results
            theme_names = [theme.get("theme_name", "") for theme in themes_data]
            supporting_documents = {theme_name: [document_id] for theme_name in theme_names}
            detailed_citations = {}
            
            for theme in themes_data:
                theme_name = theme.get("theme_name", "")
                doc_indices = theme.get("document_indices", [])
                
                # Map indices to chunks
                theme_chunks = []
                for idx in doc_indices:
                    if idx < len(chunks):
                        theme_chunks.append(chunks[idx])
                
                detailed_citations[theme_name] = self.citation_builder.create_basic_citations(theme_chunks)
            
            return ThemeResponse(
                themes=theme_names,
                supporting_documents=supporting_documents,
                detailed_citations=detailed_citations,
                metadata={
                    "document_id": document_id,
                    "total_results": len(chunks)
                }
            )
            
        except Exception as e:
            logger.error(f"Error extracting themes for document {document_id}: {str(e)}")
            raise

    def extract_all_themes(self) -> ThemeResponse:
        """Extract themes from all documents in the system"""
        try:
            # Get all documents
            all_docs = self.vector_store.list_all_documents()
            
            if not all_docs.get("documents"):
                return ThemeResponse(
                    themes=[],
                    supporting_documents={},
                    detailed_citations={},
                    metadata={"total_results": 0}
                )
            
            # Get a sample of chunks from all documents
            sample_chunks = []
            for doc_id in list(all_docs["documents"].keys())[:10]:  # Limit to first 10 documents
                raw_chunks = self.vector_store.get_chunks_by_document_id(doc_id)
                # Convert to DocumentChunk objects and take first 2 chunks per document
                for chunk_data in raw_chunks[:2]:
                    chunk = DocumentChunk(
                        content=chunk_data.get("content", ""),
                        metadata=chunk_data.get("metadata", {}),
                        similarity_score=chunk_data.get("score", 0.0)
                    )
                    sample_chunks.append(chunk)
            
            if not sample_chunks:
                return ThemeResponse(
                    themes=[],
                    supporting_documents={},
                    detailed_citations={},
                    metadata={"total_results": 0}
                )
            
            # Prepare text for theme extraction
            documents_text = "\n\n".join([
                f"Document {i+1}: {chunk.content[:500]}..."
                for i, chunk in enumerate(sample_chunks)
            ])
            
            # Extract themes using LLM
            themes_data = self.llm_service.extract_themes(documents_text)
            
            # Organize results
            theme_names = [theme.get("theme_name", "") for theme in themes_data]
            supporting_documents = {}
            detailed_citations = {}
            
            for theme in themes_data:
                theme_name = theme.get("theme_name", "")
                doc_indices = theme.get("document_indices", [])
                
                # Map indices to document IDs and chunks
                supporting_docs = []
                theme_chunks = []
                
                for idx in doc_indices:
                    if idx < len(sample_chunks):
                        chunk = sample_chunks[idx]
                        doc_id = chunk.metadata.get("doc_id", "Unknown")
                        supporting_docs.append(doc_id)
                        theme_chunks.append(chunk)
                
                supporting_documents[theme_name] = list(set(supporting_docs))  # Remove duplicates
                detailed_citations[theme_name] = self.citation_builder.create_basic_citations(theme_chunks)
            
            return ThemeResponse(
                themes=theme_names,
                supporting_documents=supporting_documents,
                detailed_citations=detailed_citations,
                metadata={
                    "total_documents": len(all_docs["documents"]),
                    "total_results": len(sample_chunks)
                }
            )
            
        except Exception as e:
            logger.error(f"Error extracting all themes: {str(e)}")
            raise

    def search_documents(self, search_request) -> Dict[str, Any]:
        """Search and filter documents based on various criteria"""
        try:
            from datetime import datetime
            import re
            import math
            
            # Get all documents first
            all_docs_result = self.vector_store.list_all_documents()
            all_documents = []
            
            # Convert to list format
            for doc_id, doc_data in all_docs_result.get("documents", {}).items():
                document = {
                    "id": doc_id,
                    "filename": doc_data.get("filename", "Unknown"),
                    "status": doc_data.get("status", "completed"),
                    "upload_timestamp": doc_data.get("upload_timestamp", "Unknown"),
                    "metadata": doc_data.get("metadata", {})
                }
                all_documents.append(document)
            
            # Apply filters
            filtered_documents = all_documents.copy()
            filters_applied = {}
            
            # Search term filter (searches in filename and metadata)
            if search_request.search_term:
                search_term = search_request.search_term.lower()
                filtered_documents = [
                    doc for doc in filtered_documents
                    if (search_term in doc["filename"].lower() or
                        search_term in str(doc["metadata"].get("title", "")).lower() or
                        search_term in str(doc["metadata"].get("author", "")).lower())
                ]
                filters_applied["search_term"] = search_request.search_term
            
            # Filename filter
            if search_request.filename_filter:
                filename_pattern = search_request.filename_filter.lower()
                filtered_documents = [
                    doc for doc in filtered_documents
                    if filename_pattern in doc["filename"].lower()
                ]
                filters_applied["filename_filter"] = search_request.filename_filter
            
            # Content type filter
            if search_request.content_type_filter:
                content_type = search_request.content_type_filter.lower()
                filtered_documents = [
                    doc for doc in filtered_documents
                    if content_type in str(doc["metadata"].get("file_type", "")).lower()
                ]
                filters_applied["content_type_filter"] = search_request.content_type_filter
            
            # Author filter
            if search_request.author_filter:
                author_pattern = search_request.author_filter.lower()
                filtered_documents = [
                    doc for doc in filtered_documents
                    if author_pattern in str(doc["metadata"].get("author", "")).lower()
                ]
                filters_applied["author_filter"] = search_request.author_filter
            
            # Status filter
            if search_request.status_filter:
                status = search_request.status_filter.lower()
                filtered_documents = [
                    doc for doc in filtered_documents
                    if status in doc["status"].lower()
                ]
                filters_applied["status_filter"] = search_request.status_filter
            
            # Date range filter
            if search_request.date_from or search_request.date_to:
                def parse_date(date_str):
                    try:
                        # Try different date formats
                        for fmt in ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]:
                            try:
                                return datetime.strptime(date_str, fmt)
                            except ValueError:
                                continue
                        return None
                    except:
                        return None
                
                date_filtered = []
                for doc in filtered_documents:
                    doc_date = parse_date(doc["upload_timestamp"])
                    if doc_date:
                        include = True
                        if search_request.date_from:
                            from_date = parse_date(search_request.date_from)
                            if from_date and doc_date < from_date:
                                include = False
                        if search_request.date_to and include:
                            to_date = parse_date(search_request.date_to)
                            if to_date and doc_date > to_date:
                                include = False
                        if include:
                            date_filtered.append(doc)
                
                filtered_documents = date_filtered
                if search_request.date_from:
                    filters_applied["date_from"] = search_request.date_from
                if search_request.date_to:
                    filters_applied["date_to"] = search_request.date_to
            
            # Sorting
            sort_by = search_request.sort_by or "upload_timestamp"
            sort_order = search_request.sort_order or "desc"
            
            def get_sort_value(doc, sort_field):
                if sort_field == "filename":
                    return doc["filename"].lower()
                elif sort_field == "upload_timestamp":
                    return doc["upload_timestamp"]
                elif sort_field == "pages":
                    return doc["metadata"].get("pages", 0)
                else:
                    return doc["filename"].lower()
            
            filtered_documents.sort(
                key=lambda x: get_sort_value(x, sort_by),
                reverse=(sort_order == "desc")
            )
            
            # Pagination
            page_size = search_request.page_size or 50
            page_number = search_request.page_number or 1
            total_count = len(filtered_documents)
            page_count = math.ceil(total_count / page_size) if total_count > 0 else 1
            
            start_idx = (page_number - 1) * page_size
            end_idx = start_idx + page_size
            paginated_documents = filtered_documents[start_idx:end_idx]
            
            return {
                "documents": paginated_documents,
                "total_count": total_count,
                "page_count": page_count,
                "current_page": page_number,
                "page_size": page_size,
                "filters_applied": filters_applied
            }
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise
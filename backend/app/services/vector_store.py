from typing import List, Dict, Any, Optional
import logging
import traceback

from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from langchain.docstore.document import Document

from app.models.schemas import ProcessedDocument, DocumentChunk
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class VectorStoreService:
    """Manages vector storage and retrieval"""
    
    def __init__(self, qdrant_url: str, collection_name: str, 
                 embedding_service: EmbeddingService, qdrant_api_key: Optional[str] = None):
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.embedding_service = embedding_service
        
        # Initialize Qdrant client
        client_kwargs = {'url': qdrant_url}
        if qdrant_api_key and 'qdrant.io' in qdrant_url:
            client_kwargs['api_key'] = qdrant_api_key
        
        self.client = QdrantClient(**client_kwargs)
        self.vectorstore = Qdrant(
            client=self.client,
            collection_name=collection_name,
            embeddings=self.embedding_service.embeddings
        )
    
    def index_document(self, document: ProcessedDocument) -> bool:
        """Index a document in the vector store"""
        try:
            # Create chunks with more detailed logging
            logger.info(f"Creating chunks for document {document.id}")
            chunks = self._create_chunks(document)
            
            if not chunks:
                logger.error(f"No chunks created from document {document.id}")
                return False
            
            logger.info(f"Created {len(chunks)} chunks for document {document.id}")
            
            # Ensure the collection exists
            try:
                logger.info(f"Ensuring collection {self.collection_name} exists")
                self._ensure_collection_exists()
                logger.info(f"Collection check completed")
            except Exception as e:
                logger.error(f"Failed to create/verify collection: {str(e)}")
                logger.error(traceback.format_exc())
                return False
            
            # Convert to LangChain documents
            langchain_docs = []
            for i, chunk in enumerate(chunks):
                try:
                    doc = Document(
                        page_content=chunk.content,
                        metadata=chunk.metadata
                    )
                    langchain_docs.append(doc)
                except Exception as e:
                    logger.error(f"Error creating document from chunk {i}: {str(e)}")
            
            if not langchain_docs:
                logger.error("No valid LangChain documents created")
                return False
                
            logger.info(f"Converted {len(langchain_docs)} chunks to LangChain documents")
            
            # Try a batch size approach for large documents
            batch_size = 5  # Reduced from 10 to 5 for better handling
            success = True
            
            try:
                for i in range(0, len(langchain_docs), batch_size):
                    batch = langchain_docs[i:i+batch_size]
                    logger.info(f"Processing batch {i//batch_size + 1} with {len(batch)} documents")
                    
                    # Use a more verbose approach with clearer error handling
                    try:
                        # Create a new Qdrant instance just for this batch
                        # to avoid potential issues with the shared instance
                        batch_vectorstore = Qdrant(
                            client=self.client,
                            collection_name=self.collection_name,
                            embeddings=self.embedding_service.embeddings
                        )
                        
                        # Add documents
                        batch_vectorstore.add_documents(batch)
                        logger.info(f"Successfully processed batch {i//batch_size + 1}")
                    except Exception as batch_error:
                        logger.error(f"Error processing batch {i//batch_size + 1}: {str(batch_error)}")
                        logger.error(traceback.format_exc())
                        success = False
                        break
            except Exception as e:
                logger.error(f"Error in batch processing: {str(e)}")
                logger.error(traceback.format_exc())
                success = False
            
            if success:
                logger.info(f"Successfully indexed document {document.id} with {len(chunks)} chunks")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to index document {document.id}: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _create_chunks(self, document: ProcessedDocument) -> List[DocumentChunk]:
        """Create chunks from processed document"""
        chunks = []
        
        for page in document.pages:
            for paragraph in page.paragraphs:
                if not paragraph.text.strip():
                    continue
                
                metadata = {
                    "doc_id": document.id,
                    "filename": document.metadata.filename,
                    "page_number": page.page_number,
                    "paragraph_number": paragraph.position.paragraph_index,
                    "position": {
                        "page": paragraph.position.page,
                        "rect": paragraph.position.rect
                    },
                    "author": document.metadata.author,
                    "document_date": document.metadata.document_date,
                    "document_type": document.metadata.document_type
                }
                
                chunk = DocumentChunk(
                    content=paragraph.text,
                    metadata=metadata
                )
                chunks.append(chunk)
        
        return chunks
    
    def _ensure_collection_exists(self):
        """Ensure the collection exists with correct configuration"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                from qdrant_client.http import models
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.embedding_service.config.dimension,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                # Collection exists, just log info about it
                collection_info = self.client.get_collection(self.collection_name)
                logger.info(f"Collection '{self.collection_name}' already exists")
                
                # More robust handling of collection params for different Qdrant versions
                try:
                    vector_size = None
                    config_params = collection_info.config.params
                    
                    # Method 1: Try accessing vectors dictionary if it exists
                    if hasattr(config_params, 'vectors'):
                        vectors_dict = getattr(config_params, 'vectors')
                        if vectors_dict and vectors_dict:
                            first_vector = next(iter(vectors_dict.values()))
                            if hasattr(first_vector, 'size'):
                                vector_size = first_vector.size
                    
                    # Method 2: Direct vector_size attribute (older versions)
                    if vector_size is None and hasattr(config_params, 'vector_size'):
                        vector_size = config_params.vector_size
                    
                    # Method 3: Direct size attribute
                    if vector_size is None and hasattr(config_params, 'size'):
                        vector_size = config_params.size
                        
                    if vector_size:
                        logger.info(f"Collection vector dimension: {vector_size}")
                        
                        if vector_size != self.embedding_service.config.dimension:
                            logger.warning(f"Dimension mismatch! Collection: {vector_size}, Embedding: {self.embedding_service.config.dimension}")
                            # Update the dimension in our config to match
                            self.embedding_service.config.dimension = vector_size
                            logger.info(f"Updated embedding dimension to {vector_size}")
                    else:
                        logger.warning("Could not determine vector dimension from collection")
                        
                except Exception as e:
                    logger.warning(f"Could not get collection details: {str(e)}")
        except Exception as e:
            logger.error(f"Error checking collection: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def list_documents(self) -> Dict[str, Any]:
        """List documents in the vector store"""
        try:
            logger.info(f"Listing documents from collection '{self.collection_name}'")
            
            # First, check if collection exists and has documents
            try:
                collection_info = self.client.get_collection(self.collection_name)
                points_count = self.client.count(collection_name=self.collection_name).count
                logger.info(f"Collection has {points_count} points")
                
                if points_count == 0:
                    logger.warning("Collection exists but has no documents")
                    return {"documents": {}, "count": 0}
                    
            except Exception as e:
                logger.error(f"Error checking collection: {str(e)}")
                return {"documents": {}, "count": 0}
            
            # Try different approaches to get documents
            documents = {}
            
            # Method 1: Use scroll API to get all points
            try:
                from qdrant_client.http import models
                
                # Scroll through all points in the collection
                scroll_result = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=1000,  # Get up to 1000 documents
                    with_payload=True,
                    with_vectors=False  # We don't need vectors, just metadata
                )
                
                logger.info(f"Scroll returned {len(scroll_result[0])} points")
                
                for point in scroll_result[0]:
                    if point.payload:
                        doc_id = point.payload.get("metadata", {}).get("doc_id")
                        if not doc_id:
                            # Try alternative metadata structure
                            doc_id = point.payload.get("doc_id")
                        
                        if doc_id and doc_id not in documents:
                            # Extract document metadata
                            metadata = point.payload.get("metadata", {})
                            if not metadata:
                                metadata = point.payload
                            
                            # Get content sample
                            content = point.payload.get("page_content", "") or point.payload.get("content", "")
                            sample_content = content[:200] + "..." if len(content) > 200 else content
                            
                            documents[doc_id] = {
                                "id": doc_id,
                                "filename": metadata.get("filename", "Unknown"),
                                "status": "completed",  # Assume completed if in vector store
                                "upload_timestamp": metadata.get("document_date", "Unknown"),
                                "metadata": {
                                    "title": metadata.get("filename", "Unknown"),
                                    "author": metadata.get("author"),
                                    "pages": metadata.get("page_number"),
                                    "file_type": metadata.get("document_type")
                                },
                                "sample_content": sample_content
                            }
                
                logger.info(f"Extracted {len(documents)} unique documents using scroll method")
                
            except Exception as scroll_error:
                logger.warning(f"Scroll method failed: {str(scroll_error)}")
                
                # Method 2: Fallback to similarity search with a generic query
                try:
                    logger.info("Trying fallback method with similarity search")
                    results = self.vectorstore.similarity_search_with_score("document content text", k=1000)
                    
                    for doc, score in results:
                        doc_id = doc.metadata.get("doc_id", "Unknown")
                        if doc_id != "Unknown" and doc_id not in documents:
                            documents[doc_id] = {
                                "id": doc_id,
                                "filename": doc.metadata.get("filename", "Unknown"),
                                "status": "completed",
                                "upload_timestamp": doc.metadata.get("document_date", "Unknown"),
                                "metadata": {
                                    "title": doc.metadata.get("filename", "Unknown"),
                                    "author": doc.metadata.get("author"),
                                    "pages": doc.metadata.get("page_number"),
                                    "file_type": doc.metadata.get("document_type")
                                },
                                "sample_content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                            }
                    
                    logger.info(f"Fallback method found {len(documents)} documents")
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback method also failed: {str(fallback_error)}")
            
            # If still no documents found but collection has points, there might be a metadata issue
            if not documents and points_count > 0:
                logger.warning(f"Collection has {points_count} points but no documents extracted - possible metadata issue")
                
                # Try to get just one document to debug the structure
                try:
                    sample_result = self.client.scroll(
                        collection_name=self.collection_name,
                        limit=1,
                        with_payload=True
                    )
                    
                    if sample_result[0]:
                        logger.info(f"Sample point structure: {sample_result[0][0].payload}")
                except Exception as debug_error:
                    logger.error(f"Could not get sample point for debugging: {str(debug_error)}")
            
            result = {
                "documents": documents,
                "count": len(documents)
            }
            
            logger.info(f"Returning {len(documents)} documents")
            return result
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            logger.error(traceback.format_exc())
            return {"documents": {}, "count": 0}
    
    def list_all_documents(self) -> Dict[str, Any]:
        """
        List all documents in the vector store.
        This is an alias for list_documents() for backward compatibility.
        """
        try:
            logger.info("Called list_all_documents() - using list_documents() implementation")
            return self.list_documents()
        except Exception as e:
            logger.error(f"Error in list_all_documents: {str(e)}")
            logger.error(traceback.format_exc())
            return {"documents": {}, "count": 0}
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the vector store"""
        try:
            # Check if client can connect
            collections = self.client.get_collections()
            
            # Check if our collection exists
            collection_exists = any(c.name == self.collection_name for c in collections.collections)
            
            # Get collection info if it exists
            collection_info = None
            if collection_exists:
                collection_info = self.client.get_collection(self.collection_name)
                points_count = self.client.count(collection_name=self.collection_name).count
            else:
                points_count = 0
            
            return {
                "status": "healthy",
                "collection_exists": collection_exists,
                "collection_name": self.collection_name,
                "points_count": points_count,
                "qdrant_url": self.qdrant_url
            }
        except Exception as e:
            logger.error(f"Vector store health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "collection_name": self.collection_name,
                "qdrant_url": self.qdrant_url
            }
    
    def get_chunks_by_document_id(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document"""
        try:
            # Use filter to get chunks for specific document
            filter_condition = {"doc_id": document_id}
            results = self.vectorstore.similarity_search_with_score(
                "", 
                k=10000,  # Large number to get all chunks
                filter=filter_condition
            )
            
            chunks = []
            for doc, score in results:
                chunk = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                }
                chunks.append(chunk)
            
            logger.info(f"Retrieved {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error getting chunks for document {document_id}: {str(e)}")
            return []
    
    def search_similar(self, query: str, k: int = 10, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            results = self.vectorstore.similarity_search_with_score(
                query, 
                k=k, 
                filter=filter_dict or {}
            )
            
            search_results = []
            for doc, score in results:
                result = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                }
                search_results.append(result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []
    
    def similarity_search(self, query: str, k: int = 10, filter_dict: Optional[Dict] = None):
        """Search for similar documents/chunks using the vector store."""
        try:
            results = self.vectorstore.similarity_search_with_score(
                query, k=k, filter=filter_dict or {}
            )
            return [doc for doc, _ in results]
        except Exception as e:
            logger.error(f"Error in similarity_search: {str(e)}")
            return []
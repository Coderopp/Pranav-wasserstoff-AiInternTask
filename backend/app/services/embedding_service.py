from typing import List
import logging
import time
import traceback

from app.models.schemas import EmbeddingConfig, EmbeddingProvider

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Handles document embeddings"""
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.embeddings = self._create_embedding_provider()
    
    def _create_embedding_provider(self):
        """Create embedding provider based on configuration"""
        if self.config.provider == EmbeddingProvider.GEMINI:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(
                model=self.config.model_name,
                google_api_key=self.config.api_key
            )
        elif self.config.provider == EmbeddingProvider.GOOGLE:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=self.config.api_key
            )
        elif self.config.provider == EmbeddingProvider.OPENAI:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                api_key=self.config.api_key,
                model="text-embedding-ada-002"
            )
        else:
            raise ValueError(f"Unsupported embedding provider: {self.config.provider}")
    
    def embed_query(self, query: str, max_retries: int = 3, retry_delay: int = 2) -> List[float]:
        """Embed a single query with retry mechanism"""
        for attempt in range(max_retries):
            try:
                return self.embeddings.embed_query(query)
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Embedding attempt {attempt+1} failed: {str(e)}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"All embedding attempts failed for query: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise
    
    def embed_documents(self, documents: List[str], max_retries: int = 3, retry_delay: int = 2) -> List[List[float]]:
        """Embed multiple documents with better error handling for large documents"""
        all_embeddings = []
        
        # Process in smaller batches
        batch_size = 5
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            logger.info(f"Embedding batch {i//batch_size + 1} of {(len(documents)-1)//batch_size + 1} ({len(batch)} documents)")
            
            for attempt in range(max_retries):
                try:
                    batch_embeddings = self.embeddings.embed_documents(batch)
                    all_embeddings.extend(batch_embeddings)
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Embedding batch {i//batch_size + 1} attempt {attempt+1} failed: {str(e)}. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"All embedding attempts failed for batch {i//batch_size + 1}: {str(e)}")
                        logger.error(traceback.format_exc())
                        # Try one-by-one embedding as a fallback
                        try:
                            logger.info("Attempting one-by-one embedding as fallback")
                            for doc in batch:
                                try:
                                    single_embedding = self.embed_query(doc)
                                    all_embeddings.append(single_embedding)
                                except Exception as single_error:
                                    logger.error(f"Failed to embed document: {str(single_error)}")
                                    # Add a placeholder embedding with zeros
                                    all_embeddings.append([0.0] * self.config.dimension)
                        except Exception as fallback_error:
                            logger.error(f"Fallback embedding failed: {str(fallback_error)}")
                            raise
        
        if len(all_embeddings) != len(documents):
            logger.error(f"Mismatch between documents ({len(documents)}) and embeddings ({len(all_embeddings)})")
            raise ValueError("Failed to embed all documents")
            
        return all_embeddings
    
    def validate_dimensions(self) -> bool:
        """Validate embedding dimensions"""
        try:
            test_embedding = self.embed_query("Test query")
            actual_dimension = len(test_embedding)
            
            if actual_dimension != self.config.dimension:
                logger.warning(f"Dimension mismatch: expected {self.config.dimension}, got {actual_dimension}")
                # Update the dimension to match actual value
                self.config.dimension = actual_dimension
                logger.info(f"Updated embedding dimension to {actual_dimension}")
            
            return True
            
        except Exception as e:
            logger.error(f"Dimension validation failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise
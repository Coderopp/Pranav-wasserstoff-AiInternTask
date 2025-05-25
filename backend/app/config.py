from pydantic_settings import BaseSettings
from typing import Optional
import os

from app.models.schemas import EmbeddingConfig, EmbeddingProvider

class Settings(BaseSettings):
    """Application configuration"""
    
    # Database settings
    DATA_DIR: str = "data"
    
    # Railway deployment settings
    PORT: int = int(os.getenv("PORT", "8000"))
    RAILWAY_ENVIRONMENT: Optional[str] = None
    
    # Vector store settings
    QDRANT_URL: str = "https://98d48a76-767d-4679-8373-777ef2d36207.us-west-2-0.aws.cloud.qdrant.io:6333"
    QDRANT_COLLECTION: str = "vectorstore"
    QDRANT_API_KEY: Optional[str] = None
    
    # Embedding settings
    EMBEDDING_PROVIDER: str = "gemini"  # Options: "gemini", "google", "openai"
    EMBEDDING_MODEL: str = "models/embedding-001"
    EMBEDDING_DIMENSION: int = 768
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # LLM settings
    GROQ_API_KEY: Optional[str] = None
    LLM_MODEL: str = "llama3-70b-8192"
    
    # CORS settings for Railway deployment
    ALLOWED_ORIGINS: list = ["*"]  # Configure appropriately for production
    
    model_config = {
        "env_file": ".env"
    }

def get_settings() -> Settings:
    """Get application settings"""
    return Settings()

def get_embedding_config() -> EmbeddingConfig:
    """Create embedding configuration from settings"""
    settings = get_settings()
    
    if settings.EMBEDDING_PROVIDER.lower() == "gemini":
        api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY required for Gemini embeddings")
        
        return EmbeddingConfig(
            provider=EmbeddingProvider.GEMINI,
            model_name=settings.EMBEDDING_MODEL,
            api_key=api_key,
            dimension=settings.EMBEDDING_DIMENSION
        )
    
    elif settings.EMBEDDING_PROVIDER.lower() == "google":
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY required for Google embeddings")
        
        return EmbeddingConfig(
            provider=EmbeddingProvider.GOOGLE,
            model_name="models/embedding-001",
            api_key=settings.GOOGLE_API_KEY,
            dimension=settings.EMBEDDING_DIMENSION
        )
    
    elif settings.EMBEDDING_PROVIDER.lower() == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY required for OpenAI embeddings")
        
        return EmbeddingConfig(
            provider=EmbeddingProvider.OPENAI,
            model_name="text-embedding-ada-002",
            api_key=settings.OPENAI_API_KEY,
            dimension=settings.EMBEDDING_DIMENSION
        )
    
    else:
        raise ValueError(f"Unsupported embedding provider: {settings.EMBEDDING_PROVIDER}")
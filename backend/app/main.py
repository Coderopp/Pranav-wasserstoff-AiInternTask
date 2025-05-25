from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import time

from app.config import get_settings, get_embedding_config
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.services.llm_service import LLMService
from app.services.database_service import DatabaseService
from app.core.document_processor import DocumentProcessor
from app.core.query_engine import QueryEngine
from app.api import document_routes, query_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Document Processing System",
    description="Modular document processing and query system",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service containers - will be populated during startup
services = {
    "document_processor": None,
    "query_engine": None
}

def initialize_services():
    """Initialize all services with dependency injection"""
    try:
        logger.info("Starting service initialization...")
        settings = get_settings()
        
        # Ensure data directories exist
        os.makedirs(os.path.join(settings.DATA_DIR, "documents"), exist_ok=True)
        os.makedirs(os.path.join(settings.DATA_DIR, "metadata"), exist_ok=True)
        
        # Initialize embedding service
        logger.info("Initializing embedding service...")
        embedding_config = get_embedding_config()
        embedding_service = EmbeddingService(embedding_config)
        embedding_service.validate_dimensions()
        logger.info("Embedding service initialized successfully")
        
        # Initialize vector store
        logger.info("Initializing vector store...")
        vector_store = VectorStoreService(
            qdrant_url=settings.QDRANT_URL,
            collection_name=settings.QDRANT_COLLECTION,
            embedding_service=embedding_service,
            qdrant_api_key=settings.QDRANT_API_KEY
        )
        logger.info("Vector store initialized successfully")
        
        # Initialize database service
        logger.info("Initializing database service...")
        database_service = DatabaseService(settings.DATA_DIR)
        logger.info("Database service initialized successfully")
        
        # Initialize LLM service
        logger.info("Initializing LLM service...")
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required")
        
        llm_service = LLMService(
            groq_api_key=settings.GROQ_API_KEY,
            model=settings.LLM_MODEL
        )
        logger.info("LLM service initialized successfully")
        
        # Initialize orchestrators
        logger.info("Initializing document processor and query engine...")
        document_processor = DocumentProcessor(vector_store, database_service)
        query_engine = QueryEngine(vector_store, llm_service)
        
        # Store in services dict
        services["document_processor"] = document_processor
        services["query_engine"] = query_engine
        
        logger.info("All services initialized successfully")
        
        return True
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}", exc_info=True)
        return False

# Dependency providers
def get_document_processor() -> DocumentProcessor:
    """Dependency provider for DocumentProcessor"""
    processor = services.get("document_processor")
    if processor is None:
        logger.error("Document processor is None! Services were not initialized correctly.")
        raise RuntimeError("Document processor not initialized")
    return processor

def get_query_engine() -> QueryEngine:
    """Dependency provider for QueryEngine"""
    engine = services.get("query_engine") 
    if engine is None:
        raise RuntimeError("Query engine not initialized")
    return engine

# Setup dependency overrides
app.dependency_overrides[document_routes.get_document_processor] = get_document_processor
app.dependency_overrides[query_routes.get_query_engine] = get_query_engine

# Include routers
app.include_router(document_routes.router)
app.include_router(query_routes.router)

@app.middleware("http")
async def check_services_initialized(request: Request, call_next):
    """Middleware to check if services are initialized before handling requests"""
    if not any(services.values()) and request.url.path not in ['/', '/health', '/docs', '/openapi.json', '/redoc']:
        logger.warning(f"Request to {request.url.path} received but services not initialized. Trying to initialize...")
        initialize_services()
        if not any(services.values()):
            return {"error": "Service initialization failed. Check server logs."}
    
    response = await call_next(request)
    return response

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Request to {request.url.path} processed in {process_time:.4f} seconds")
    return response

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error occurred. Please try again."}
        )

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Application startup event triggered")
    success = initialize_services()
    
    if success:
        logger.info("Services initialized successfully in startup event")
    else:
        logger.error("Failed to initialize services in startup event")

@app.get("/")
async def root():
    """Root endpoint for the API"""
    return {
        "message": "Document AI API",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/health")
@app.head("/health")
async def detailed_health_check():
    """Detailed health check endpoint - supports both GET and HEAD methods"""
    return {
        "status": "healthy" if all(services.values()) else "unhealthy",
        "services": {
            "document_processor": services["document_processor"] is not None,
            "query_engine": services["query_engine"] is not None
        },
        "api_keys": {
            "gemini_api_key": bool(get_settings().GEMINI_API_KEY),
            "groq_api_key": bool(get_settings().GROQ_API_KEY),
            "qdrant_api_key": bool(get_settings().QDRANT_API_KEY)
        }
    }

@app.get("/api/health-check")
@app.head("/api/health-check")
async def simple_health_check():
    """Simple health check endpoint - supports both GET and HEAD methods"""
    return {"status": "ok", "message": "API is running"}

@app.get("/api/status")
async def api_status():
    """Extended API status endpoint with more details"""
    try:
        settings = get_settings()
        return {
            "status": "running",
            "version": "1.0.0",
            "services_initialized": all(services.values()),
            "environment": {
                "data_dir_exists": os.path.exists(settings.DATA_DIR),
                "qdrant_url": settings.QDRANT_URL,
                "llm_model": settings.LLM_MODEL
            },
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "health": "/health",
                "health_check": "/api/health-check"
            }
        }
    except Exception as e:
        logger.error(f"Error in status endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
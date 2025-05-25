from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class DocumentMetadata:
    """Document metadata container"""
    filename: str
    content_type: str
    file_size: int
    upload_date: str
    author: Optional[str] = None
    document_date: Optional[str] = None
    document_type: Optional[str] = None
    processing_status: str = "pending"
    segment_count: int = 0
    page_count: int = 0

@dataclass
class TextPosition:
    """Text position information"""
    page: int
    paragraph_index: Optional[int] = None
    rect: Optional[List[float]] = None  # [x0, y0, x1, y1]
    is_ocr: bool = False

@dataclass
class DocumentParagraph:
    """Single paragraph with position"""
    text: str
    position: TextPosition

@dataclass
class DocumentPage:
    """Single document page"""
    page_number: int
    paragraphs: List[DocumentParagraph]
    full_text: str

@dataclass
class ProcessedDocument:
    """Complete processed document"""
    id: str
    full_text: str
    pages: List[DocumentPage]
    metadata: DocumentMetadata

@dataclass
class DocumentChunk:
    """Document chunk for vector storage"""
    content: str
    metadata: Dict[str, Any]
    similarity_score: float = 0.0

@dataclass
class Citation:
    """Citation information"""
    doc_id: str
    document_name: str
    page_number: Optional[int]
    paragraph_number: Optional[int]
    content_snippet: str
    position_rect: Optional[List[float]] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None

@dataclass
class EmbeddingInfo:
    """Embedding metadata"""
    vector_id: str
    similarity_score: float
    dimension: int
    model_name: str

@dataclass
class EnhancedCitation(Citation):
    """Citation with embedding information"""
    embedding_info: Optional[EmbeddingInfo] = None

# ============================================================================
# CONFIGURATION MODELS
# ============================================================================

class EmbeddingProvider(Enum):
    GEMINI = "gemini"
    GOOGLE = "google"
    OPENAI = "openai"

@dataclass
class EmbeddingConfig:
    """Embedding provider configuration"""
    provider: EmbeddingProvider
    model_name: str
    api_key: str
    dimension: int

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class QueryRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    advanced_filters: Optional[Dict[str, Any]] = None
    selected_document_ids: Optional[List[str]] = None  # New field for document selection

class DocumentSearchRequest(BaseModel):
    """Request model for document search and filtering"""
    search_term: Optional[str] = None
    filename_filter: Optional[str] = None
    content_type_filter: Optional[str] = None
    author_filter: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    status_filter: Optional[str] = None
    page_size: Optional[int] = 50
    page_number: Optional[int] = 1
    sort_by: Optional[str] = "upload_timestamp"  # filename, upload_timestamp, pages
    sort_order: Optional[str] = "desc"  # asc, desc

class DocumentSearchResponse(BaseModel):
    """Response model for document search results"""
    documents: List[Dict[str, Any]]
    total_count: int
    page_count: int
    current_page: int
    page_size: int
    filters_applied: Dict[str, Any]

class QueryResponse(BaseModel):
    answers: List[str]
    citations: List[Citation]
    metadata: Dict[str, Any]

class EnhancedQueryResponse(BaseModel):
    answers: List[str]
    citations: List[EnhancedCitation]
    metadata: Dict[str, Any]

class ThemeResponse(BaseModel):
    themes: List[str]
    supporting_documents: Dict[str, List[str]]
    detailed_citations: Dict[str, List[Citation]]
    metadata: Dict[str, Any]

class DocumentListResponse(BaseModel):
    documents: List[Dict[str, Any]]  # Changed from Dict[str, Dict[str, Any]] to List[Dict[str, Any]]
    count: int

class DocumentResponse(BaseModel):
    document_id: str
    status: str
    filename: str
    metadata: Dict[str, Any]

class DocumentSelectionRequest(BaseModel):
    """Request model for selecting documents for queries"""
    document_ids: List[str]
    
class DocumentSelectionResponse(BaseModel):
    """Response model for document selection confirmation"""
    selected_documents: List[Dict[str, Any]]
    count: int
    status: str
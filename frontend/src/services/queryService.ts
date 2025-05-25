import axios, { AxiosResponse } from 'axios';

// Create axios instance with base URL and timeout settings
// Use relative path for production deployment with nginx proxy
const axiosInstance = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL as string) || '/api',
  timeout: 30000, // 30 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add retry functionality with exponential backoff
const retryRequest = async (fn: () => Promise<AxiosResponse>, maxRetries = 3): Promise<AxiosResponse> => {
  let retries = 0;
  while (retries <= maxRetries) {
    try {
      return await fn();
    } catch (error: any) {
      if (retries === maxRetries) {
        throw error;
      }
      
      // Only retry on network errors or 5xx errors
      if (error.code === 'ECONNREFUSED' || 
          error.code === 'NETWORK_ERROR' || 
          (error.response && error.response.status >= 500)) {
        const delay = Math.pow(2, retries) * 1000; // 1s, 2s, 4s, etc.
        console.log(`Retrying request in ${delay}ms... (${retries + 1}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, delay));
        retries++;
      } else {
        throw error;
      }
    }
  }
  throw new Error('Max retries exceeded');
};

// Add a response interceptor for global error handling
axiosInstance.interceptors.response.use(
  response => response,
  error => {
    let errorMessage = 'An unexpected error occurred';
    
    if (error.response) {
      // Server responded with an error status
      switch (error.response.status) {
        case 404:
          errorMessage = 'The requested resource was not found';
          break;
        case 405:
          errorMessage = 'Method not allowed for this endpoint';
          break;
        case 500:
          errorMessage = error.response.data?.detail || 'Internal server error occurred';
          break;
        default:
          errorMessage = error.response.data?.detail || `Server error: ${error.response.status}`;
      }
    } else if (error.request) {
      // Request was made but no response received
      if (error.code === 'ECONNREFUSED') {
        errorMessage = 'Cannot connect to the server. Please ensure the backend is running on the correct port.';
      } else if (error.code === 'NETWORK_ERROR') {
        errorMessage = 'Network error occurred. Please check your connection.';
      } else {
        errorMessage = 'Could not connect to the server. Please ensure the backend is running.';
      }
    } else {
      // Something else happened while setting up the request
      errorMessage = error.message || errorMessage;
    }
    
    // Log the error for debugging
    console.error('API Error:', error);
    
    return Promise.reject({ ...error, friendlyMessage: errorMessage });
  }
);

export interface SearchResult {
  answer: string;
  citations: Array<{
    document_id: string;
    document_name: string;
    text: string;
    score: number;
    page?: number;
  }>;
}

// Enhanced citation interface to match backend response
export interface EnhancedSearchResult {
  answers: string[];
  citations: Array<{
    doc_id: string;
    document_name: string;
    page_number?: number;
    paragraph_number?: number;
    content_snippet: string;
    position_rect?: number[];
    start_offset?: number;
    end_offset?: number;
    embedding_info?: {
      vector_id: string;
      similarity_score: number;
      dimension: number;
      model_name: string;
    };
  }>;
  metadata: Record<string, any>;
}

export interface QueryRequest {
  query: string;
  filters?: Record<string, any>;
  selected_document_ids?: string[];  // Add support for document selection
}

const queryService = {
  // Check backend connection status
  checkConnection: async (): Promise<boolean> => {
    try {
      await retryRequest(() => axiosInstance.head('/health-check'));
      return true;
    } catch (err) {
      console.error('Backend connection check failed:', err);
      return false;
    }
  },

  // Basic search functionality with document selection
  search: async (query: string, filters?: Record<string, any>, selectedDocumentIds?: string[]): Promise<SearchResult> => {
    const requestData: QueryRequest = {
      query,
      filters,
      selected_document_ids: selectedDocumentIds
    };
    
    const response = await retryRequest(() => 
      axiosInstance.post('/queries/search', requestData)
    );
    return response.data;
  },

  // Enhanced search with better citations and document selection
  enhancedSearch: async (query: string, filters?: Record<string, any>, selectedDocumentIds?: string[]): Promise<SearchResult> => {
    try {
      const requestData: QueryRequest = {
        query,
        filters,
        selected_document_ids: selectedDocumentIds
      };
      
      const response = await retryRequest(() => 
        axiosInstance.post('/queries/enhanced-search', requestData)
      );
      
      const data: EnhancedSearchResult = response.data;
      
      // Transform the backend response to match frontend expectations
      const transformedResult: SearchResult = {
        answer: Array.isArray(data.answers) ? data.answers.join('\n\n') : data.answers || '',
        citations: (data.citations || []).map(citation => ({
          document_id: citation.doc_id || '',
          document_name: citation.document_name || 'Unknown Document',
          text: citation.content_snippet || '',
          score: citation.embedding_info?.similarity_score || 0.5,
          page: citation.page_number
        }))
      };
      
      return transformedResult;
    } catch (error: any) {
      console.error('Enhanced search error:', error);
      // If enhanced search fails, fallback to regular search
      console.log('Falling back to regular search...');
      return queryService.search(query, filters, selectedDocumentIds);
    }
  },

  // Validate document selection
  validateDocumentSelection: async (documentIds: string[]) => {
    const response = await retryRequest(() => 
      axiosInstance.post('/queries/documents/select', { document_ids: documentIds })
    );
    return response.data;
  },

  // Extract themes from documents
  extractThemes: async (query?: string, filters?: Record<string, any>) => {
    const response = await retryRequest(() => 
      axiosInstance.get('/queries/themes', { params: { query, ...filters } })
    );
    return response.data;
  },

  // Get all documents from the query service
  getDocuments: async () => {
    const response = await retryRequest(() => 
      axiosInstance.get('/queries/documents')
    );
    return response.data;
  },

  // Health check for query services
  checkQueryServiceHealth: async () => {
    const response = await retryRequest(() => 
      axiosInstance.get('/queries/health')
    );
    return response.data;
  }
};

export default queryService;
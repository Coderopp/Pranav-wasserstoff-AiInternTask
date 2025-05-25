import axios from 'axios';
import { toast } from 'react-toastify';

// Create axios instance with base URL and timeout settings
const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000, // 30 second timeout
});

// Add a response interceptor for global error handling
axiosInstance.interceptors.response.use(
  response => response,
  error => {
    let errorMessage = 'An unexpected error occurred';
    
    if (error.response) {
      // Server responded with an error status
      errorMessage = error.response.data?.detail || `Server error: ${error.response.status}`;
    } else if (error.request) {
      // Request was made but no response received
      errorMessage = 'Could not connect to the server. Please ensure the backend is running.';
    } else {
      // Something else happened while setting up the request
      errorMessage = error.message || errorMessage;
    }
    
    // Log the error for debugging
    console.error('API Error:', error);
    
    return Promise.reject({ ...error, friendlyMessage: errorMessage });
  }
);

export interface Document {
  id: string;
  filename: string;
  status: string;
  upload_timestamp: string;
  metadata: {
    title?: string;
    author?: string;
    pages?: number;
    file_type?: string;
    [key: string]: any;
  };
}

export interface DocumentDetail extends Document {
  content?: string;
  chunks?: Array<{
    id: string;
    text: string;
    metadata?: any;
  }>;
}

export interface DocumentSearchRequest {
  search_term?: string;
  filename_filter?: string;
  content_type_filter?: string;
  author_filter?: string;
  date_from?: string;
  date_to?: string;
  status_filter?: string;
  page_size?: number;
  page_number?: number;
  sort_by?: string;
  sort_order?: string;
}

export interface DocumentSearchResponse {
  documents: Document[];
  total_count: number;
  page_count: number;
  current_page: number;
  page_size: number;
  filters_applied: Record<string, any>;
}

const documentService = {
  // Check backend connection status
  checkConnection: async (): Promise<boolean> => {
    try {
      await axiosInstance.head('/health-check');
      return true;
    } catch (err) {
      console.error('Backend connection check failed:', err);
      return false;
    }
  },

  // Get all documents with retry mechanism
  getDocuments: async (maxRetries = 2): Promise<Document[]> => {
    let retries = 0;
    while (retries <= maxRetries) {
      try {
        const response = await axiosInstance.get('/queries/documents');
        // Extract the documents array from the response
        const data = response.data;
        if (data && Array.isArray(data.documents)) {
          return data.documents;
        } else if (Array.isArray(data)) {
          // Fallback: if response.data is already an array
          return data;
        } else {
          console.error('Unexpected response format:', data);
          return [];
        }
      } catch (err: any) {
        if (retries === maxRetries) {
          // If all retries failed, throw the error
          throw err;
        }
        
        // Exponential backoff
        const delay = Math.pow(2, retries) * 1000; // 1s, 2s, 4s, etc.
        console.log(`Retrying getDocuments in ${delay}ms... (${retries + 1}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, delay));
        retries++;
      }
    }
    
    throw new Error('Could not fetch documents after multiple retries');
  },

  // Get a single document by ID
  getDocument: async (id: string): Promise<DocumentDetail> => {
    const response = await axiosInstance.get(`/documents/${id}`);
    return response.data;
  },

  // Upload a new document
  uploadDocument: async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axiosInstance.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        // Optional progress tracking
        const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
        console.log(`Upload progress: ${percentCompleted}%`);
      },
    });
    return response.data;
  },

  // Delete a document
  deleteDocument: async (id: string): Promise<void> => {
    await axiosInstance.delete(`/documents/${id}`);
  },

  // Search and filter documents
  searchDocuments: async (searchRequest: DocumentSearchRequest): Promise<DocumentSearchResponse> => {
    const response = await axiosInstance.post('/queries/documents/search', searchRequest);
    return response.data;
  },

  // Retry processing a document
  retryProcessing: async (id: string): Promise<void> => {
    await axiosInstance.post(`/documents/${id}/retry-indexing`);
  }
};

export default documentService;
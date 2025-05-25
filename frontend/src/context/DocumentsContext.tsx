import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import documentService, { Document } from '../services/documentService';
import { toast } from 'react-toastify';

interface DocumentsContextType {
  documents: Document[];
  loading: boolean;
  error: string | null;
  selectedDocuments: string[];  // New: Array of selected document IDs
  fetchDocuments: () => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;
  retryProcessing: (id: string) => Promise<void>;
  refreshDocuments: () => Promise<void>;
  checkBackendConnection: () => Promise<boolean>;
  // New document selection methods
  selectDocument: (id: string) => void;
  unselectDocument: (id: string) => void;
  selectAllDocuments: () => void;
  clearSelection: () => void;
  toggleDocumentSelection: (id: string) => void;
  isDocumentSelected: (id: string) => boolean;
  getSelectedDocuments: () => Document[];
}

const DocumentsContext = createContext<DocumentsContextType | undefined>(undefined);

export function useDocuments() {
  const context = useContext(DocumentsContext);
  if (!context) {
    throw new Error('useDocuments must be used within a DocumentsProvider');
  }
  return context;
}

export function DocumentsProvider({ children }: { children: ReactNode }) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(true);
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]); // Track selected document IDs

  const checkBackendConnection = async (): Promise<boolean> => {
    try {
      const connected = await documentService.checkConnection();
      setIsConnected(connected);
      return connected;
    } catch (err) {
      setIsConnected(false);
      return false;
    }
  };

  const fetchDocuments = async () => {
    if (!isConnected && !(await checkBackendConnection())) {
      setError('Cannot connect to the backend server. Please ensure it is running.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const docs = await documentService.getDocuments();
      setDocuments(docs);
    } catch (err: any) {
      console.error('Error fetching documents:', err);
      setError(err.friendlyMessage || 'Failed to fetch documents. Please try again later.');
      
      // Show toast for better UX
      toast.error(err.friendlyMessage || 'Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  };

  const deleteDocument = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      await documentService.deleteDocument(id);
      setDocuments(documents.filter(doc => doc.id !== id));
      toast.success('Document deleted successfully');
    } catch (err: any) {
      console.error(`Error deleting document ${id}:`, err);
      setError(err.friendlyMessage || 'Failed to delete document. Please try again later.');
      toast.error(err.friendlyMessage || 'Failed to delete document');
    } finally {
      setLoading(false);
    }
  };

  const retryProcessing = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      await documentService.retryProcessing(id);
      // Update the status in the local state
      setDocuments(
        documents.map(doc => 
          doc.id === id ? { ...doc, status: 'processing' } : doc
        )
      );
      toast.info('Document processing restarted');
    } catch (err: any) {
      console.error(`Error retrying processing for document ${id}:`, err);
      setError(err.friendlyMessage || 'Failed to retry processing. Please try again later.');
      toast.error(err.friendlyMessage || 'Failed to retry processing');
    } finally {
      setLoading(false);
    }
  };

  const refreshDocuments = async () => {
    await fetchDocuments();
  };

  // New document selection methods
  const selectDocument = (id: string) => {
    setSelectedDocuments(prevSelected => [...prevSelected, id]);
  };

  const unselectDocument = (id: string) => {
    setSelectedDocuments(prevSelected => prevSelected.filter(docId => docId !== id));
  };

  const selectAllDocuments = () => {
    setSelectedDocuments(documents.map(doc => doc.id));
  };

  const clearSelection = () => {
    setSelectedDocuments([]);
  };

  const toggleDocumentSelection = (id: string) => {
    setSelectedDocuments(prevSelected => 
      prevSelected.includes(id) 
        ? prevSelected.filter(docId => docId !== id) 
        : [...prevSelected, id]
    );
  };

  const isDocumentSelected = (id: string) => {
    return selectedDocuments.includes(id);
  };

  const getSelectedDocuments = () => {
    return documents.filter(doc => selectedDocuments.includes(doc.id));
  };

  useEffect(() => {
    const initializeContext = async () => {
      await checkBackendConnection();
      await fetchDocuments();
    };
    
    initializeContext();
    
    // Set up periodic connection checks
    const connectionCheckInterval = setInterval(async () => {
      const connected = await checkBackendConnection();
      
      // If we've regained connection after being disconnected, refresh documents
      if (connected && !isConnected) {
        fetchDocuments();
      }
    }, 30000); // Check every 30 seconds
    
    return () => {
      clearInterval(connectionCheckInterval);
    };
  }, []);

  return (
    <DocumentsContext.Provider 
      value={{ 
        documents, 
        loading, 
        error, 
        fetchDocuments, 
        deleteDocument, 
        retryProcessing, 
        refreshDocuments,
        checkBackendConnection,
        selectedDocuments, // Expose selectedDocuments state
        selectDocument,
        unselectDocument,
        selectAllDocuments,
        clearSelection,
        toggleDocumentSelection,
        isDocumentSelected,
        getSelectedDocuments
      }}
    >
      {children}
    </DocumentsContext.Provider>
  );
}
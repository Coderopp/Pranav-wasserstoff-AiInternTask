import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Divider,
  Chip,
  FormControlLabel,
  Switch,
  useTheme,
  Collapse,
  AlertTitle,
} from '@mui/material';
import {
  Search as SearchIcon,
  FormatQuote as FormatQuoteIcon,
  KeyboardArrowDown as KeyboardArrowDownIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  Refresh as RefreshIcon,
  FilterList as FilterListIcon,
} from '@mui/icons-material';
import { Link } from 'react-router-dom';
import queryService, { SearchResult } from '../services/queryService';
import { useDocuments } from '../context/DocumentsContext';
import DocumentSelector from '../components/DocumentSelector';

const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useEnhanced, setUseEnhanced] = useState(true);
  const [expandedCitations, setExpandedCitations] = useState<Record<number, boolean>>({});
  const [backendConnected, setBackendConnected] = useState(true);
  const [showDocumentSelector, setShowDocumentSelector] = useState(false);
  const theme = useTheme();
  const { 
    checkBackendConnection, 
    selectedDocuments, 
    getSelectedDocuments, 
    clearSelection 
  } = useDocuments();

  const selectedDocs = getSelectedDocuments();

  useEffect(() => {
    // Check connection status when component mounts
    const checkConnection = async () => {
      try {
        const connected = await queryService.checkConnection();
        setBackendConnected(connected);
      } catch (err) {
        setBackendConnected(false);
      }
    };
    
    checkConnection();
    
    // Set up periodic connection checks
    const connectionCheckInterval = setInterval(async () => {
      try {
        const connected = await checkBackendConnection();
        setBackendConnected(connected);
        
        // Clear error if we regained connection
        if (connected && error?.includes('connect to the backend')) {
          setError(null);
        }
      } catch (err) {
        setBackendConnected(false);
      }
    }, 30000); // Check every 30 seconds
    
    return () => {
      clearInterval(connectionCheckInterval);
    };
  }, [error, checkBackendConnection]);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    // Check connection first
    if (!backendConnected) {
      try {
        const connected = await checkBackendConnection();
        if (!connected) {
          setError('Cannot connect to the backend server. Please ensure it is running.');
          return;
        }
        setBackendConnected(true);
        setError(null);
      } catch (err) {
        setError('Cannot connect to the backend server. Please ensure it is running.');
        return;
      }
    }
    
    setLoading(true);
    setError(null);
    setSearchResults(null); // Clear previous results
    
    try {
      // Pass selected document IDs to the search service
      const selectedDocumentIds = selectedDocuments.length > 0 ? selectedDocuments : undefined;
      
      const result = useEnhanced
        ? await queryService.enhancedSearch(query, undefined, selectedDocumentIds)
        : await queryService.search(query, undefined, selectedDocumentIds);
      
      // Validate the result structure
      if (!result || typeof result !== 'object') {
        throw new Error('Invalid response format from server');
      }
      
      if (!result.answer && (!result.citations || result.citations.length === 0)) {
        const scopeMessage = selectedDocuments.length > 0 
          ? ` in the ${selectedDocuments.length} selected documents`
          : '';
        setError(`No results found${scopeMessage}. Please try a different search query.`);
        return;
      }
      
      // Ensure answer is a string
      if (typeof result.answer !== 'string') {
        result.answer = String(result.answer || 'No answer available');
      }
      
      // Validate citations array
      if (result.citations && Array.isArray(result.citations)) {
        result.citations = result.citations.filter(citation => 
          citation && 
          typeof citation === 'object' && 
          citation.document_id && 
          citation.text
        );
      } else {
        result.citations = [];
      }
      
      setSearchResults(result);
    } catch (err: any) {
      console.error('Error performing search:', err);
      
      // More specific error handling
      let errorMessage = 'Failed to perform search. Please try again later.';
      
      if (err.friendlyMessage) {
        errorMessage = err.friendlyMessage;
      } else if (err.message) {
        if (err.message.includes('Invalid response format')) {
          errorMessage = 'Received invalid data from server. Please try again or contact support.';
        } else if (err.message.includes('timeout')) {
          errorMessage = 'Search request timed out. Please try again with a shorter query.';
        } else {
          errorMessage = err.message;
        }
      }
      
      setError(errorMessage);
      
      // Check if it's a connection error and update the connection status
      if (errorMessage.includes('connect to the server') || errorMessage.includes('network')) {
        setBackendConnected(false);
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleCitation = (index: number) => {
    setExpandedCitations(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  // Function to highlight query terms in the text
  const highlightText = (text: string) => {
    if (!query.trim()) return text;
    
    // Simple approach for highlighting the search terms
    const terms = query.toLowerCase().split(/\s+/).filter(term => term.length > 3);
    let highlighted = text;
    
    terms.forEach(term => {
      const regex = new RegExp(`(${term})`, 'gi');
      highlighted = highlighted.replace(regex, '<span class="highlight">$1</span>');
    });
    
    return highlighted;
  };

  const retryConnection = async () => {
    setError(null);
    try {
      const connected = await checkBackendConnection();
      setBackendConnected(connected);
      if (!connected) {
        setError('Still cannot connect to the backend server. Please ensure it is running.');
      }
    } catch (err) {
      setBackendConnected(false);
      setError('Failed to check connection status. Please ensure the backend is running.');
    }
  };

  const handleDocumentSelectionConfirm = (selectedIds: string[]) => {
    // Document selection is handled in context, just show feedback
    const message = selectedIds.length > 0 
      ? `${selectedIds.length} documents selected for search`
      : 'No documents selected - will search all documents';
    console.log(message);
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Search Documents
      </Typography>
      
      {!backendConnected && (
        <Alert 
          severity="warning"
          sx={{ mb: 3 }}
          icon={<WifiOffIcon />}
          action={
            <Button 
              color="inherit" 
              size="small" 
              onClick={retryConnection}
              startIcon={<RefreshIcon />}
            >
              Retry
            </Button>
          }
        >
          <AlertTitle>Backend Connection Issue</AlertTitle>
          Cannot connect to the backend server. Please ensure it is running.
          {error && <Typography variant="body2" sx={{ mt: 1 }}>{error}</Typography>}
        </Alert>
      )}

      {/* Document Selection Section */}
      <Paper elevation={2} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" color="primary">
            Document Selection
          </Typography>
          <Box>
            <Button
              variant="outlined"
              size="small"
              startIcon={<FilterListIcon />}
              onClick={() => setShowDocumentSelector(true)}
              disabled={!backendConnected}
              sx={{ mr: 1 }}
            >
              Select Documents
            </Button>
            {selectedDocuments.length > 0 && (
              <Button
                variant="text"
                size="small"
                onClick={clearSelection}
                color="secondary"
              >
                Clear ({selectedDocuments.length})
              </Button>
            )}
          </Box>
        </Box>

        {selectedDocuments.length > 0 ? (
          <Box>
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                Search will be limited to {selectedDocuments.length} selected documents
              </Typography>
            </Alert>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {selectedDocs.slice(0, 5).map((doc) => (
                <Chip
                  key={doc.id}
                  label={doc.filename}
                  size="small"
                  color="primary"
                  variant="outlined"
                  sx={{ maxWidth: 250 }}
                />
              ))}
              {selectedDocs.length > 5 && (
                <Chip
                  label={`+${selectedDocs.length - 5} more documents`}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No documents selected - search will include all available documents
          </Typography>
        )}
      </Paper>
      
      <Paper elevation={3} sx={{ p: 3, mt: 3, borderRadius: 2 }}>
        <Box component="form" onSubmit={(e) => { e.preventDefault(); handleSearch(); }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2 }}>
            <TextField
              label="Ask a question about your documents"
              variant="outlined"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              fullWidth
              autoFocus
              sx={{ flexGrow: 1 }}
              placeholder="e.g., What are the main themes in the document?"
              disabled={!backendConnected}
            />
            <Button
              variant="contained"
              color="primary"
              onClick={handleSearch}
              disabled={loading || !query.trim() || !backendConnected}
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
              sx={{ height: 56 }}
            >
              Search
            </Button>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 2, justifyContent: 'space-between' }}>
            <FormControlLabel
              control={
                <Switch
                  checked={useEnhanced}
                  onChange={(e) => setUseEnhanced(e.target.checked)}
                  color="primary"
                  disabled={!backendConnected}
                />
              }
              label="Use enhanced search with better citations"
            />
            {backendConnected && (
              <Chip 
                icon={<WifiIcon />} 
                label="Backend Connected" 
                color="success" 
                size="small" 
              />
            )}
          </Box>
        </Box>
      </Paper>

      {/* Document Selector Dialog */}
      <DocumentSelector
        open={showDocumentSelector}
        onClose={() => setShowDocumentSelector(false)}
        onConfirm={handleDocumentSelectionConfirm}
        title="Select Documents for Search"
        description="Choose which documents to include in your search. Your question will only be answered using content from the selected documents."
      />
      
      {error && !error.includes('backend server') && (
        <Alert severity="error" sx={{ mt: 3 }}>
          {error}
        </Alert>
      )}
      
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      )}
      
      {searchResults && !loading && (
        <Box sx={{ mt: 4 }}>
          <Card elevation={2} sx={{ borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Answer
              </Typography>
              <Typography 
                variant="body1" 
                sx={{ 
                  whiteSpace: 'pre-wrap',
                  '& .highlight': {
                    backgroundColor: 'rgba(255, 255, 0, 0.3)',
                    borderRadius: '2px',
                    padding: '2px 0'
                  }
                }}
                dangerouslySetInnerHTML={{ __html: searchResults.answer }}
              />
            </CardContent>
          </Card>
          
          {searchResults.citations && searchResults.citations.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                Citations & Sources
              </Typography>
              <Box sx={{ mt: 2 }}>
                {searchResults.citations.map((citation, index) => (
                  <Card 
                    key={`${citation.document_id}-${index}`}
                    variant="outlined" 
                    sx={{ mb: 2, borderLeft: `4px solid ${theme.palette.primary.main}` }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <Box>
                          <Typography variant="subtitle1" component={Link} to={`/documents/${citation.document_id}`} sx={{ textDecoration: 'none', color: theme.palette.primary.main }}>
                            {citation.document_name}
                          </Typography>
                          {citation.page && (
                            <Chip 
                              size="small" 
                              label={`Page ${citation.page}`} 
                              sx={{ ml: 1 }} 
                            />
                          )}
                        </Box>
                        <Button
                          size="small"
                          endIcon={expandedCitations[index] ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
                          onClick={() => toggleCitation(index)}
                        >
                          {expandedCitations[index] ? 'Hide' : 'Show'} citation
                        </Button>
                      </Box>
                      
                      <Collapse in={expandedCitations[index]} timeout="auto" unmountOnExit>
                        <Box sx={{ mt: 2, p: 2, bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.03)', borderRadius: 1 }}>
                          <Typography 
                            variant="body2" 
                            component="div" 
                            sx={{
                              whiteSpace: 'pre-wrap',
                              '& .highlight': {
                                backgroundColor: 'rgba(255, 255, 0, 0.3)',
                                borderRadius: '2px',
                                padding: '2px 0'
                              }
                            }}
                            dangerouslySetInnerHTML={{ __html: highlightText(citation.text) }}
                          />
                          
                          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
                            <Chip 
                              size="small"
                              icon={<FormatQuoteIcon />} 
                              label={`Relevance: ${(citation.score * 100).toFixed(0)}%`} 
                              variant="outlined"
                            />
                          </Box>
                        </Box>
                      </Collapse>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            </Box>
          )}
        </Box>
      )}
      
      {!searchResults && !loading && !error && (
        <Box 
          sx={{ 
            mt: 4, 
            p: 3, 
            textAlign: 'center', 
            bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
            borderRadius: 2
          }}
        >
          <Typography variant="body1" color="text.secondary">
            Enter a question above to search through your documents.
          </Typography>
          <Divider sx={{ my: 2 }} />
          <Typography variant="body2" color="text.secondary">
            Example questions:
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Chip 
              label="What are the main themes discussed in the documents?" 
              onClick={() => setQuery("What are the main themes discussed in the documents?")}
              sx={{ m: 0.5 }}
              disabled={!backendConnected}
            />
            <Chip 
              label="Summarize the key points in the latest report" 
              onClick={() => setQuery("Summarize the key points in the latest report")}
              sx={{ m: 0.5 }}
              disabled={!backendConnected}
            />
            <Chip 
              label="What recommendations are made in the documents?" 
              onClick={() => setQuery("What recommendations are made in the documents?")}
              sx={{ m: 0.5 }}
              disabled={!backendConnected}
            />
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default SearchPage;
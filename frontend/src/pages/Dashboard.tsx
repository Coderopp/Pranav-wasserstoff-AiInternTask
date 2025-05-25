import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  IconButton,
  Chip,
  Skeleton,
  Alert,
  useTheme,
  Pagination,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as HourglassIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useDocuments } from '../context/DocumentsContext';
import DocumentSearch from '../components/DocumentSearch';
import { DocumentSearchResponse } from '../services/documentService';
import { format } from 'date-fns';

const Dashboard: React.FC = () => {
  const { documents, loading, error, deleteDocument, retryProcessing, refreshDocuments } = useDocuments();
  const navigate = useNavigate();
  const theme = useTheme();

  // State for search functionality
  const [searchResults, setSearchResults] = useState<DocumentSearchResponse | null>(null);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  // Determine which documents to display
  const displayDocuments = isSearchMode && searchResults 
    ? searchResults.documents 
    : Array.isArray(documents) ? documents : [];

  // Format the date in a readable format
  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return format(date, 'MMM d, yyyy HH:mm');
    } catch (err) {
      return dateStr;
    }
  };

  // Get status chip based on document status
  const getStatusChip = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return (
          <Chip
            icon={<CheckCircleIcon fontSize="small" />}
            label="Completed"
            color="success"
            size="small"
            variant="outlined"
          />
        );
      case 'processing':
        return (
          <Chip
            icon={<HourglassIcon fontSize="small" />}
            label="Processing"
            color="warning"
            size="small"
            variant="outlined"
          />
        );
      case 'failed':
        return (
          <Chip
            icon={<ErrorIcon fontSize="small" />}
            label="Failed"
            color="error"
            size="small"
            variant="outlined"
          />
        );
      default:
        return (
          <Chip
            label={status}
            size="small"
            variant="outlined"
          />
        );
    }
  };

  // Handle delete confirmation
  const handleDelete = async (id: string, filename: string) => {
    if (window.confirm(`Are you sure you want to delete "${filename}"?`)) {
      await deleteDocument(id);
    }
  };

  // Handle search results
  const handleSearchResults = (results: DocumentSearchResponse) => {
    setSearchResults(results);
    setIsSearchMode(true);
    setCurrentPage(results.current_page);
  };

  // Handle clearing search
  const handleClearSearch = () => {
    setSearchResults(null);
    setIsSearchMode(false);
    setCurrentPage(1);
  };

  // Handle page change for search results
  const handlePageChange = async (event: React.ChangeEvent<unknown>, value: number) => {
    if (isSearchMode && searchResults) {
      // Get the current search request and update page number
      setCurrentPage(value);
      // You could implement pagination here by calling the search again with new page number
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Documents
        </Typography>
        <Button 
          variant="contained" 
          startIcon={<RefreshIcon />}
          onClick={() => refreshDocuments()}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <DocumentSearch 
        onSearchResults={handleSearchResults}
        onClearSearch={handleClearSearch}
      />

      <Grid container spacing={3}>
        {loading ? (
          // Show loading skeletons
          Array.from(new Array(4)).map((_, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Skeleton variant="text" width="60%" height={32} />
                  <Skeleton variant="text" width="40%" />
                  <Box sx={{ mt: 2 }}>
                    <Skeleton variant="text" width="30%" />
                    <Skeleton variant="text" width="80%" />
                    <Skeleton variant="text" width="50%" />
                  </Box>
                </CardContent>
                <CardActions>
                  <Skeleton variant="rectangular" width={100} height={36} />
                </CardActions>
              </Card>
            </Grid>
          ))
        ) : displayDocuments.length === 0 ? (
          // Show message when no documents
          <Grid item xs={12}>
            <Alert severity="info">
              No documents found. Upload a document to get started.
            </Alert>
          </Grid>
        ) : (
          // Show document cards - using safeDocuments instead of documents
          displayDocuments.map((document) => (
            <Grid item xs={12} sm={6} md={4} key={document.id}>
              <Card 
                sx={{ 
                  height: '100%', 
                  display: 'flex', 
                  flexDirection: 'column',
                  transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 6px 20px rgba(0, 0, 0, 0.15)'
                  }
                }}
                className="document-card"
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" component="div" noWrap>
                    {document.metadata?.title || document.filename || 'Unknown Document'}
                  </Typography>
                  <Box sx={{ mt: 1 }}>
                    {getStatusChip(document.status || 'unknown')}
                  </Box>
                  <Box sx={{ mt: 2 }}>
                    {document.metadata?.author && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Author: {document.metadata.author}
                      </Typography>
                    )}
                    {document.metadata?.pages && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Pages: {document.metadata.pages}
                      </Typography>
                    )}
                    <Typography variant="body2" color="text.secondary">
                      Uploaded: {formatDate(document.upload_timestamp || new Date().toISOString())}
                    </Typography>
                  </Box>
                </CardContent>
                <CardActions>
                  <Button 
                    size="small" 
                    startIcon={<VisibilityIcon />} 
                    onClick={() => navigate(`/documents/${document.id}`)}
                  >
                    View
                  </Button>
                  {document.status === 'failed' && (
                    <Button 
                      size="small" 
                      startIcon={<RefreshIcon />}
                      color="warning"
                      onClick={() => retryProcessing(document.id)}
                    >
                      Retry
                    </Button>
                  )}
                  <Box sx={{ ml: 'auto' }}>
                    <IconButton 
                      size="small" 
                      color="error"
                      onClick={() => handleDelete(document.id, document.filename || 'Unknown Document')}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                </CardActions>
              </Card>
            </Grid>
          ))
        )}
      </Grid>

      {isSearchMode && searchResults && (
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Pagination
            count={searchResults.page_count}
            page={currentPage}
            onChange={handlePageChange}
            variant="outlined"
            shape="rounded"
            sx={{ justifyContent: 'center', display: 'flex' }}
          />
        </Box>
      )}

      {documents && documents.length > 0 && !isSearchMode && (
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Button 
            variant="outlined" 
            onClick={() => navigate('/upload')}
            sx={{ mr: 2 }}
          >
            Upload New Document
          </Button>
          <Button 
            variant="outlined" 
            onClick={() => navigate('/search')}
          >
            Search Documents
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default Dashboard;
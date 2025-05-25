import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Grid,
  Paper,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Collapse,
  IconButton,
  Chip,
  Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  FilterList as FilterListIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import documentService, { DocumentSearchRequest, DocumentSearchResponse } from '../services/documentService';
import { toast } from 'react-toastify';
import { useDocuments } from '../context/DocumentsContext';
import DocumentSelector from './DocumentSelector';

interface DocumentSearchProps {
  onSearchResults: (results: DocumentSearchResponse) => void;
  onClearSearch: () => void;
}

const DocumentSearch: React.FC<DocumentSearchProps> = ({ onSearchResults, onClearSearch }) => {
  const { selectedDocuments, getSelectedDocuments, clearSelection } = useDocuments();
  const [searchRequest, setSearchRequest] = useState<DocumentSearchRequest>({
    search_term: '',
    filename_filter: '',
    author_filter: '',
    status_filter: '',
    sort_by: 'upload_timestamp',
    sort_order: 'desc',
    page_size: 20,
    page_number: 1
  });
  
  const [isSearching, setIsSearching] = useState(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [showDocumentSelector, setShowDocumentSelector] = useState(false);

  const selectedDocs = getSelectedDocuments();

  const handleSearch = async () => {
    if (!searchRequest.search_term && !searchRequest.filename_filter && 
        !searchRequest.author_filter && !searchRequest.status_filter) {
      toast.warning('Please enter at least one search criteria');
      return;
    }

    setIsSearching(true);
    try {
      const results = await documentService.searchDocuments(searchRequest);
      onSearchResults(results);
      
      const searchScope = selectedDocuments.length > 0 
        ? ` (limited to ${selectedDocuments.length} selected documents)` 
        : '';
      toast.success(`Found ${results.total_count} documents${searchScope}`);
    } catch (error: any) {
      console.error('Search error:', error);
      toast.error(error.friendlyMessage || 'Failed to search documents');
    } finally {
      setIsSearching(false);
    }
  };

  const handleClearSearch = () => {
    setSearchRequest({
      search_term: '',
      filename_filter: '',
      author_filter: '',
      status_filter: '',
      sort_by: 'upload_timestamp',
      sort_order: 'desc',
      page_size: 20,
      page_number: 1
    });
    onClearSearch();
  };

  const handleClearDocumentSelection = () => {
    clearSelection();
    toast.info('Document selection cleared - now searching all documents');
  };

  const handleDocumentSelectionConfirm = (selectedIds: string[]) => {
    const message = selectedIds.length > 0 
      ? `${selectedIds.length} documents selected for search`
      : 'No documents selected - will search all documents';
    toast.success(message);
  };

  const updateSearchRequest = (field: keyof DocumentSearchRequest, value: any) => {
    setSearchRequest(prev => ({
      ...prev,
      [field]: field === 'page_size' ? parseInt(value) : value
    }));
  };

  return (
    <>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">Search Documents</Typography>
          <Button
            variant="text"
            size="small"
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            endIcon={showAdvancedFilters ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          >
            {showAdvancedFilters ? 'Hide Filters' : 'Advanced Filters'}
          </Button>
        </Box>

        {/* Document Selection Section */}
        <Box sx={{ mb: 3, p: 2, bgcolor: 'primary.50', borderRadius: 1, border: '1px solid', borderColor: 'primary.200' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="subtitle2" color="primary">
              Document Selection
            </Typography>
            <Box>
              <Button
                variant="outlined"
                size="small"
                startIcon={<FilterListIcon />}
                onClick={() => setShowDocumentSelector(true)}
                sx={{ mr: 1 }}
              >
                Select Documents
              </Button>
              {selectedDocuments.length > 0 && (
                <Button
                  variant="text"
                  size="small"
                  startIcon={<ClearIcon />}
                  onClick={handleClearDocumentSelection}
                  color="secondary"
                >
                  Clear Selection
                </Button>
              )}
            </Box>
          </Box>

          {selectedDocuments.length > 0 ? (
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <CheckCircleIcon color="success" fontSize="small" />
                <Typography variant="body2" color="success.main">
                  Search will be limited to {selectedDocuments.length} selected documents
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {selectedDocs.slice(0, 3).map((doc) => (
                  <Chip
                    key={doc.id}
                    label={doc.filename}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ maxWidth: 200 }}
                  />
                ))}
                {selectedDocs.length > 3 && (
                  <Chip
                    label={`+${selectedDocs.length - 3} more`}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                )}
              </Box>
            </Box>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No documents selected - search will include all documents
            </Typography>
          )}
        </Box>

        <Divider sx={{ mb: 3 }} />

        {/* Basic Search */}
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Search Term"
              placeholder="Search in filename, title, author..."
              value={searchRequest.search_term || ''}
              onChange={(e) => updateSearchRequest('search_term', e.target.value)}
              variant="outlined"
              size="small"
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Filename Filter"
              placeholder="Filter by filename..."
              value={searchRequest.filename_filter || ''}
              onChange={(e) => updateSearchRequest('filename_filter', e.target.value)}
              variant="outlined"
              size="small"
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Sort By</InputLabel>
              <Select
                value={searchRequest.sort_by || 'upload_timestamp'}
                onChange={(e) => updateSearchRequest('sort_by', e.target.value)}
                label="Sort By"
              >
                <MenuItem value="upload_timestamp">Upload Date</MenuItem>
                <MenuItem value="filename">Filename</MenuItem>
                <MenuItem value="pages">Page Count</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        {/* Advanced Filters */}
        <Collapse in={showAdvancedFilters}>
          <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1, mb: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Author Filter"
                  placeholder="Filter by author..."
                  value={searchRequest.author_filter || ''}
                  onChange={(e) => updateSearchRequest('author_filter', e.target.value)}
                  variant="outlined"
                  size="small"
                />
              </Grid>

              <Grid item xs={12} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel>Status Filter</InputLabel>
                  <Select
                    value={searchRequest.status_filter || ''}
                    onChange={(e) => updateSearchRequest('status_filter', e.target.value)}
                    label="Status Filter"
                  >
                    <MenuItem value="">All Statuses</MenuItem>
                    <MenuItem value="completed">Completed</MenuItem>
                    <MenuItem value="processing">Processing</MenuItem>
                    <MenuItem value="failed">Failed</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel>Sort Order</InputLabel>
                  <Select
                    value={searchRequest.sort_order || 'desc'}
                    onChange={(e) => updateSearchRequest('sort_order', e.target.value)}
                    label="Sort Order"
                  >
                    <MenuItem value="desc">Descending</MenuItem>
                    <MenuItem value="asc">Ascending</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel>Results Per Page</InputLabel>
                  <Select
                    value={searchRequest.page_size || 20}
                    onChange={(e) => updateSearchRequest('page_size', e.target.value)}
                    label="Results Per Page"
                  >
                    <MenuItem value={10}>10</MenuItem>
                    <MenuItem value={20}>20</MenuItem>
                    <MenuItem value={50}>50</MenuItem>
                    <MenuItem value={100}>100</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Box>
        </Collapse>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<SearchIcon />}
            onClick={handleSearch}
            disabled={isSearching}
          >
            {isSearching ? 'Searching...' : 'Search Documents'}
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<ClearIcon />}
            onClick={handleClearSearch}
          >
            Clear & Show All
          </Button>
        </Box>
      </Paper>

      {/* Document Selector Dialog */}
      <DocumentSelector
        open={showDocumentSelector}
        onClose={() => setShowDocumentSelector(false)}
        onConfirm={handleDocumentSelectionConfirm}
        title="Select Documents for Search"
        description="Choose which documents to include in your search. Only selected documents will be searched for answers."
      />
    </>
  );
};

export default DocumentSearch;
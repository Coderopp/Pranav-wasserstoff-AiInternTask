import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Button,
  Divider,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Grid,
  Card,
  CardContent,
  useTheme,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Description as DescriptionIcon,
  DataObject as DataObjectIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as HourglassIcon,
} from '@mui/icons-material';
import documentService, { DocumentDetail } from '../services/documentService';
import { format } from 'date-fns';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`document-tabpanel-${index}`}
      aria-labelledby={`document-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const DocumentView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const navigate = useNavigate();
  const theme = useTheme();

  useEffect(() => {
    const fetchDocument = async () => {
      if (!id) return;
      
      setLoading(true);
      setError(null);
      try {
        const documentData = await documentService.getDocument(id);
        setDocument(documentData);
      } catch (err) {
        console.error(`Error fetching document ${id}:`, err);
        setError('Failed to load document. It may have been deleted or there was a server error.');
      } finally {
        setLoading(false);
      }
    };

    fetchDocument();
  }, [id]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleDelete = async () => {
    if (!document || !id) return;
    
    if (window.confirm(`Are you sure you want to delete "${document.filename}"?`)) {
      try {
        await documentService.deleteDocument(id);
        navigate('/');
      } catch (err) {
        console.error(`Error deleting document ${id}:`, err);
        setError('Failed to delete document. Please try again later.');
      }
    }
  };

  const handleRetryProcessing = async () => {
    if (!id) return;
    
    try {
      await documentService.retryProcessing(id);
      // Update the document status locally
      setDocument(document => document ? { ...document, status: 'processing' } : null);
    } catch (err) {
      console.error(`Error retrying processing for document ${id}:`, err);
      setError('Failed to retry processing. Please try again later.');
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return format(date, 'MMM d, yyyy HH:mm');
    } catch (err) {
      return dateStr;
    }
  };

  const getStatusChip = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return (
          <Chip
            icon={<CheckCircleIcon />}
            label="Completed"
            color="success"
            variant="outlined"
          />
        );
      case 'processing':
        return (
          <Chip
            icon={<HourglassIcon />}
            label="Processing"
            color="warning"
            variant="outlined"
          />
        );
      case 'failed':
        return (
          <Chip
            icon={<ErrorIcon />}
            label="Failed"
            color="error"
            variant="outlined"
          />
        );
      default:
        return (
          <Chip
            label={status}
            variant="outlined"
          />
        );
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ mt: 2 }}>
        <Alert 
          severity="error" 
          action={
            <Button color="inherit" size="small" onClick={() => navigate('/')}>
              Go Back
            </Button>
          }
        >
          {error}
        </Alert>
      </Box>
    );
  }

  if (!document) {
    return null;
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/')}
          sx={{ mr: 2 }}
        >
          Back to Documents
        </Button>
        <Box sx={{ flexGrow: 1 }} />
        {document.status === 'failed' && (
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            color="warning"
            onClick={handleRetryProcessing}
            sx={{ mr: 2 }}
          >
            Retry Processing
          </Button>
        )}
        <Tooltip title="Delete document">
          <IconButton color="error" onClick={handleDelete}>
            <DeleteIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Paper elevation={3} sx={{ p: 3, borderRadius: 2 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            {document.metadata?.title || document.filename}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1, mb: 2 }}>
            {getStatusChip(document.status)}
            {document.metadata?.file_type && (
              <Chip label={document.metadata.file_type} size="small" />
            )}
          </Box>
          <Divider sx={{ my: 2 }} />
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="body2" color="text.secondary">
                Uploaded: {formatDate(document.upload_timestamp)}
              </Typography>
            </Grid>
            {document.metadata?.author && (
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="body2" color="text.secondary">
                  Author: {document.metadata.author}
                </Typography>
              </Grid>
            )}
            {document.metadata?.pages && (
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="body2" color="text.secondary">
                  Pages: {document.metadata.pages}
                </Typography>
              </Grid>
            )}
          </Grid>
        </Box>

        <Box sx={{ width: '100%' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={tabValue} 
              onChange={handleTabChange} 
              aria-label="document tabs"
              variant="scrollable"
              scrollButtons="auto"
            >
              <Tab icon={<DescriptionIcon fontSize="small" />} iconPosition="start" label="Content" />
              <Tab icon={<DataObjectIcon fontSize="small" />} iconPosition="start" label="Metadata" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            {document.content ? (
              <Box 
                className="document-content" 
                sx={{ 
                  whiteSpace: 'pre-wrap', 
                  p: 2, 
                  borderRadius: 1,
                  bgcolor: theme.palette.background.default,
                  maxHeight: '60vh',
                  overflow: 'auto'
                }}
              >
                {document.content}
              </Box>
            ) : document.chunks && document.chunks.length > 0 ? (
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Document Chunks:
                </Typography>
                <Box sx={{ maxHeight: '60vh', overflow: 'auto' }}>
                  {document.chunks.map((chunk, index) => (
                    <Card 
                      key={chunk.id || index} 
                      variant="outlined" 
                      sx={{ mb: 2 }}
                    >
                      <CardContent>
                        <Typography variant="body2">
                          {chunk.text}
                        </Typography>
                        {chunk.metadata && (
                          <Box sx={{ mt: 1 }}>
                            {chunk.metadata.page && (
                              <Chip 
                                size="small" 
                                label={`Page ${chunk.metadata.page}`} 
                                sx={{ mr: 1, mt: 1 }} 
                              />
                            )}
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              </Box>
            ) : (
              <Alert severity="info">
                No content available for this document.
              </Alert>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Box sx={{ maxHeight: '60vh', overflow: 'auto' }}>
              {Object.entries(document.metadata || {}).length > 0 ? (
                <Grid container spacing={2}>
                  {Object.entries(document.metadata || {}).map(([key, value]) => (
                    <Grid item xs={12} sm={6} md={4} key={key}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="caption" color="text.secondary">
                            {key}
                          </Typography>
                          <Typography variant="body1">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Alert severity="info">
                  No metadata available for this document.
                </Alert>
              )}
            </Box>
          </TabPanel>
        </Box>
      </Paper>
    </Box>
  );
};

export default DocumentView;
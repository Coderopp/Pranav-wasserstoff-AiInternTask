import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  Button,
  Paper,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Divider,
  useTheme,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  InsertDriveFile as FileIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import documentService from '../services/documentService';

const DocumentUpload: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const navigate = useNavigate();
  const theme = useTheme();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Add only files that are not already added
    setFiles(prevFiles => {
      const newFiles = acceptedFiles.filter(
        newFile => !prevFiles.some(file => file.name === newFile.name)
      );
      return [...prevFiles, ...newFiles];
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc', '.docx'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxSize: 50 * 1024 * 1024, // 50 MB
  });

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;
    
    setUploading(true);
    setUploadProgress(0);
    setError(null);
    
    const uploadedFileNames: string[] = [];
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        await documentService.uploadDocument(file);
        uploadedFileNames.push(file.name);
        setUploadProgress(((i + 1) / files.length) * 100);
      } catch (err: any) {
        console.error(`Error uploading ${file.name}:`, err);
        
        // Enhanced error handling
        let errorMessage = `Failed to upload ${file.name}.`;
        
        if (err.response) {
          // Server responded with an error status code
          if (err.response.data && err.response.data.detail) {
            errorMessage += ` ${err.response.data.detail}`;
          } else {
            errorMessage += ` Server error: ${err.response.status}`;
          }
        } else if (err.request) {
          // No response received from server
          errorMessage += " Could not connect to the server. Please ensure the backend is running.";
        } else {
          // Something else went wrong
          errorMessage += " An unexpected error occurred.";
        }
        
        setError(errorMessage);
        break;
      }
    }
    
    setUploading(false);
    
    if (uploadedFileNames.length > 0) {
      setUploadedFiles(uploadedFileNames);
      setFiles([]);
      
      const message = uploadedFileNames.length === 1
        ? `Successfully uploaded ${uploadedFileNames[0]}`
        : `Successfully uploaded ${uploadedFileNames.length} files`;
      
      toast.success(message);
    }
  };

  const goToDashboard = () => {
    navigate('/');
  };

  // Helper function to check backend connection
  const checkBackendConnection = async () => {
    try {
      // Making a simple HEAD request to check if the backend is accessible
      await fetch('/api/health-check', { method: 'HEAD' });
      return true;
    } catch (err) {
      console.error('Backend connection check failed:', err);
      return false;
    }
  };

  // Handle retry when there's a connection error
  const handleRetry = async () => {
    setError(null);
    const isConnected = await checkBackendConnection();
    
    if (isConnected) {
      uploadFiles();
    } else {
      setError("Cannot connect to the backend server. Please ensure it is running.");
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Upload Documents
      </Typography>
      
      <Paper
        elevation={3}
        sx={{
          p: 4,
          mt: 3,
          borderRadius: 2,
          backgroundColor: theme.palette.background.paper,
        }}
      >
        <Box
          {...getRootProps()}
          sx={{
            border: `2px dashed ${theme.palette.divider}`,
            borderRadius: 2,
            p: 6,
            mb: 3,
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'background-color 0.3s ease',
            '&:hover': {
              backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
            },
            backgroundColor: isDragActive
              ? theme.palette.mode === 'dark'
                ? 'rgba(255, 255, 255, 0.08)'
                : 'rgba(0, 0, 0, 0.04)'
              : 'transparent',
          }}
        >
          <input {...getInputProps()} />
          <CloudUploadIcon sx={{ fontSize: 48, color: theme.palette.primary.main, mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Drag & drop files here
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Or click to select files
          </Typography>
          <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 1 }}>
            Supported formats: PDF, DOC, DOCX, TXT (Max: 50MB)
          </Typography>
        </Box>
        
        {files.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Selected Files ({files.length}):
            </Typography>
            <List>
              {files.map((file, index) => (
                <React.Fragment key={`${file.name}-${index}`}>
                  <ListItem
                    secondaryAction={
                      <Button 
                        size="small" 
                        color="error" 
                        onClick={() => removeFile(index)}
                        disabled={uploading}
                      >
                        Remove
                      </Button>
                    }
                  >
                    <ListItemAvatar>
                      <Avatar>
                        <FileIcon />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={file.name}
                      secondary={`${(file.size / 1024 / 1024).toFixed(2)} MB`}
                    />
                  </ListItem>
                  {index < files.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
            <Box sx={{ mt: 2 }}>
              <Button
                variant="contained"
                color="primary"
                onClick={uploadFiles}
                disabled={uploading}
                sx={{ mr: 2 }}
              >
                Upload {files.length > 1 ? `${files.length} Files` : 'File'}
              </Button>
              <Button
                variant="outlined"
                onClick={() => setFiles([])}
                disabled={uploading}
              >
                Clear All
              </Button>
            </Box>
          </Box>
        )}
        
        {uploading && (
          <Box sx={{ width: '100%', mt: 2 }}>
            <Typography variant="body2" gutterBottom>
              Uploading... {Math.round(uploadProgress)}%
            </Typography>
            <LinearProgress variant="determinate" value={uploadProgress} />
          </Box>
        )}
        
        {error && (
          <Alert 
            severity="error" 
            sx={{ mt: 2 }}
            action={
              <Button color="inherit" size="small" onClick={handleRetry}>
                Retry
              </Button>
            }
          >
            {error}
          </Alert>
        )}
        
        {uploadedFiles.length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Alert 
              icon={<CheckCircleIcon />} 
              severity="success" 
              sx={{ mb: 2 }}
            >
              <Typography variant="body1">
                {uploadedFiles.length === 1
                  ? `Successfully uploaded ${uploadedFiles[0]}`
                  : `Successfully uploaded ${uploadedFiles.length} files`}
              </Typography>
            </Alert>
            <Typography variant="body2" paragraph>
              The document{uploadedFiles.length !== 1 ? 's' : ''} will be processed automatically. You can view the status on the dashboard.
            </Typography>
            <Button
              variant="contained"
              onClick={goToDashboard}
              sx={{ mr: 2 }}
            >
              Go to Dashboard
            </Button>
            <Button
              variant="outlined"
              onClick={() => {
                setUploadedFiles([]);
                setFiles([]);
              }}
            >
              Upload More Files
            </Button>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default DocumentUpload;
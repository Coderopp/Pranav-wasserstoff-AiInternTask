import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Checkbox,
  TextField,
  Box,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  FormControlLabel,
  Switch
} from '@mui/material';
import {
  Search as SearchIcon,
  SelectAll as SelectAllIcon,
  Clear as ClearIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { useDocuments } from '../context/DocumentsContext';

interface DocumentSelectorProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (selectedIds: string[]) => void;
  title?: string;
  description?: string;
}

export default function DocumentSelector({
  open,
  onClose,
  onConfirm,
  title = "Select Documents",
  description = "Choose which documents to include in your search"
}: DocumentSelectorProps) {
  const {
    documents,
    selectedDocuments,
    selectDocument,
    unselectDocument,
    selectAllDocuments,
    clearSelection,
    toggleDocumentSelection,
    isDocumentSelected
  } = useDocuments();

  const [searchTerm, setSearchTerm] = useState('');
  const [showSelectedOnly, setShowSelectedOnly] = useState(false);

  // Filter documents based on search term and show selected only toggle
  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.metadata?.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.metadata?.author?.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (showSelectedOnly) {
      return matchesSearch && isDocumentSelected(doc.id);
    }
    
    return matchesSearch;
  });

  const handleSelectAll = () => {
    selectAllDocuments();
  };

  const handleClearAll = () => {
    clearSelection();
  };

  const handleConfirm = () => {
    onConfirm(selectedDocuments);
    onClose();
  };

  const handleClose = () => {
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { height: '80vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">{title}</Typography>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
        {description && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {description}
          </Typography>
        )}
      </DialogTitle>

      <DialogContent dividers>
        {/* Selection Summary */}
        <Box sx={{ mb: 2 }}>
          <Box display="flex" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
            <Typography variant="subtitle2" color="primary">
              {selectedDocuments.length} of {documents.length} documents selected
            </Typography>
            <Box>
              <Tooltip title="Select All">
                <IconButton onClick={handleSelectAll} size="small">
                  <SelectAllIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Clear Selection">
                <IconButton onClick={handleClearAll} size="small">
                  <ClearIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>

          {/* Selected documents chips */}
          {selectedDocuments.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
              {selectedDocuments.slice(0, 5).map(docId => {
                const doc = documents.find(d => d.id === docId);
                return doc ? (
                  <Chip
                    key={docId}
                    label={doc.filename}
                    size="small"
                    onDelete={() => unselectDocument(docId)}
                    sx={{ maxWidth: 200 }}
                  />
                ) : null;
              })}
              {selectedDocuments.length > 5 && (
                <Chip
                  label={`+${selectedDocuments.length - 5} more`}
                  size="small"
                  variant="outlined"
                />
              )}
            </Box>
          )}
        </Box>

        {/* Search and Filter Controls */}
        <Box sx={{ mb: 2 }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search documents by filename, title, or author..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
            }}
            sx={{ mb: 1 }}
          />
          
          <FormControlLabel
            control={
              <Switch
                checked={showSelectedOnly}
                onChange={(e) => setShowSelectedOnly(e.target.checked)}
                size="small"
              />
            }
            label="Show selected only"
          />
        </Box>

        {/* Documents List */}
        <List dense>
          {filteredDocuments.length === 0 ? (
            <Box textAlign="center" py={4}>
              <Typography color="text.secondary">
                {searchTerm ? 'No documents match your search' : 'No documents available'}
              </Typography>
            </Box>
          ) : (
            filteredDocuments.map((doc) => (
              <ListItem
                key={doc.id}
                button
                onClick={() => toggleDocumentSelection(doc.id)}
                sx={{
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 1,
                  mb: 1,
                  backgroundColor: isDocumentSelected(doc.id) ? 'action.selected' : 'background.paper'
                }}
              >
                <ListItemIcon>
                  <Checkbox
                    edge="start"
                    checked={isDocumentSelected(doc.id)}
                    tabIndex={-1}
                    disableRipple
                  />
                </ListItemIcon>
                <ListItemText
                  primary={doc.filename}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Status: {doc.status} | 
                        Uploaded: {new Date(doc.upload_timestamp).toLocaleDateString()}
                      </Typography>
                      {doc.metadata?.title && (
                        <Typography variant="body2" color="text.secondary">
                          Title: {doc.metadata.title}
                        </Typography>
                      )}
                      {doc.metadata?.author && (
                        <Typography variant="body2" color="text.secondary">
                          Author: {doc.metadata.author}
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))
          )}
        </List>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={handleClose} color="inherit">
          Cancel
        </Button>
        <Button
          onClick={handleConfirm}
          variant="contained"
          disabled={selectedDocuments.length === 0}
        >
          Use Selected Documents ({selectedDocuments.length})
        </Button>
      </DialogActions>
    </Dialog>
  );
}
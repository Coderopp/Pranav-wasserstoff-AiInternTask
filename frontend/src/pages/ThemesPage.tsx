import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Divider,
  Chip,
  TextField,
  Grid,
  useTheme,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  Category as CategoryIcon,
  Description as DescriptionIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { Link } from 'react-router-dom';
import queryService, { ThemeResult } from '../services/queryService';

const ThemesPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [themeResults, setThemeResults] = useState<ThemeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const theme = useTheme();

  const handleExtractThemes = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await queryService.extractThemes(query || undefined);
      setThemeResults(result);
    } catch (err) {
      console.error('Error extracting themes:', err);
      setError('Failed to extract themes. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  // Function to get a color based on relevance score
  const getRelevanceColor = (score: number) => {
    if (score >= 0.8) return theme.palette.success.main;
    if (score >= 0.5) return theme.palette.info.main;
    return theme.palette.text.secondary;
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Document Themes
      </Typography>
      
      <Paper elevation={3} sx={{ p: 3, mt: 3, borderRadius: 2 }}>
        <Box component="form" onSubmit={(e) => { e.preventDefault(); handleExtractThemes(); }}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body1" paragraph>
              Analyze your documents to extract common themes and topics. You can optionally provide a focus query to guide the theme extraction.
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2 }}>
            <TextField
              label="Optional focus query"
              variant="outlined"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              fullWidth
              sx={{ flexGrow: 1 }}
              placeholder="e.g., Focus on environmental aspects"
              helperText="Leave blank to extract general themes across all documents"
            />
            <Button
              variant="contained"
              color="primary"
              onClick={handleExtractThemes}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <CategoryIcon />}
              sx={{ height: 56 }}
            >
              Extract Themes
            </Button>
          </Box>
        </Box>
      </Paper>
      
      {error && (
        <Alert severity="error" sx={{ mt: 3 }}>
          {error}
        </Alert>
      )}
      
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      )}
      
      {themeResults && !loading && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h5" gutterBottom>
            Identified Themes ({themeResults.themes.length})
          </Typography>
          
          <Grid container spacing={3}>
            {themeResults.themes.map((theme, index) => (
              <Grid item xs={12} md={6} key={`theme-${index}`}>
                <Card 
                  elevation={2} 
                  sx={{ 
                    height: '100%',
                    borderRadius: 2,
                    transition: 'transform 0.2s ease-in-out',
                    '&:hover': {
                      transform: 'translateY(-4px)'
                    },
                  }}
                  className="document-card"
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                      <CategoryIcon sx={{ mr: 1, color: theme.palette.primary.main }} />
                      <Typography variant="h6" component="h3">
                        {theme.name}
                      </Typography>
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {theme.description}
                    </Typography>
                    
                    <Divider sx={{ my: 2 }} />
                    
                    <Typography variant="subtitle2" gutterBottom>
                      Relevant Documents:
                    </Typography>
                    
                    <List dense disablePadding>
                      {theme.documents.map((doc) => (
                        <ListItem 
                          key={doc.document_id} 
                          component={Link} 
                          to={`/documents/${doc.document_id}`}
                          sx={{ 
                            textDecoration: 'none', 
                            color: 'inherit',
                            borderRadius: 1,
                            '&:hover': {
                              backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.03)'
                            }
                          }}
                        >
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            <DescriptionIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText 
                            primary={doc.document_name} 
                            primaryTypographyProps={{ noWrap: true }} 
                          />
                          <Chip 
                            icon={<TrendingUpIcon fontSize="small" />}
                            label={`${(doc.relevance * 100).toFixed(0)}%`}
                            size="small"
                            sx={{ 
                              ml: 1, 
                              color: getRelevanceColor(doc.relevance),
                              borderColor: getRelevanceColor(doc.relevance)
                            }}
                            variant="outlined"
                          />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
      
      {!themeResults && !loading && (
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
            Click the "Extract Themes" button to analyze your documents and identify common themes.
          </Typography>
          <Divider sx={{ my: 2 }} />
          <Typography variant="body2" color="text.secondary">
            Theme extraction helps you understand the key topics and connections between your documents.
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default ThemesPage;
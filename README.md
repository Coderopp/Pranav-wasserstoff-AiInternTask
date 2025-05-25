# Document Analysis and Query System

A full-stack document processing and intelligent query system built with FastAPI, React, and vector embeddings. This application allows users to upload documents, process them using OCR and NLP techniques, and perform intelligent semantic search with AI-powered responses.

## 🚀 Features

- **Document Upload & Processing**: Support for PDF, images, and text documents
- **OCR Integration**: Extract text from images and scanned documents using Tesseract
- **Vector Embeddings**: Generate semantic embeddings using Google's Gemini or OpenAI models
- **Intelligent Search**: Semantic search with AI-generated responses and citations
- **Modern UI**: React-based frontend with Material-UI components
- **Containerized Deployment**: Docker-ready with unified frontend/backend container
- **Vector Database**: Qdrant integration for efficient similarity search

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Vite + Material-UI
- **Backend**: FastAPI + Python 3.11
- **Vector Database**: Qdrant
- **AI Models**: Google Gemini, OpenAI, Groq
- **Document Processing**: PyMuPDF, Tesseract OCR, NLTK
- **Deployment**: Docker + Nginx

## 📋 Prerequisites

- Docker and Docker Compose
- Git
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd wasserstoff-AiInternTask
```

2. Create environment file:
```bash
cp backend/.env.example backend/.env
# Edit the .env file with your API keys
```

3. Start the application:
```bash
docker-compose up --build
```

4. Access the application:
- Frontend: http://localhost
- Backend API: http://localhost/api
- API Documentation: http://localhost/api/docs

### Local Development

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```env
# AI API Keys
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optional_api_key

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### API Keys Setup

1. **Groq API**: Sign up at [console.groq.com](https://console.groq.com)
2. **Google Gemini**: Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. **OpenAI** (optional): Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)

## 📁 Project Structure

```
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # Reusable React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API service layers
│   │   └── styles/         # CSS and styling
│   └── package.json
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Business logic
│   │   ├── models/         # Data models and schemas
│   │   └── services/       # External service integrations
│   └── requirements.txt
├── data/                   # Document storage (gitignored)
├── logs/                   # Application logs (gitignored)
├── Dockerfile             # Unified container build
├── docker-compose.yml     # Multi-service orchestration
├── nginx.conf             # Nginx configuration
└── requirements.txt       # Root-level Python dependencies
```

## 🔄 API Endpoints

### Document Management
- `POST /api/documents/upload` - Upload a new document
- `GET /api/documents` - List all documents
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete a document

### Query & Search
- `POST /api/queries/search` - Basic semantic search
- `POST /api/queries/enhanced-search` - Enhanced search with citations
- `GET /api/queries/documents` - Get searchable documents
- `GET /api/health-check` - Health check endpoint

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Integration Tests
```bash
cd backend
python integration_test.py
```

## 🚢 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build -d

# Or build individual container
docker build -t document-analysis-app .
docker run -p 80:80 -p 8000:8000 document-analysis-app
```

### Cloud Deployment
The application is ready for deployment on:
- Azure Container Instances
- AWS ECS/Fargate
- Google Cloud Run
- DigitalOcean App Platform
- Any Docker-compatible hosting service

## 🔍 Usage Examples

### Upload and Process Document
1. Navigate to the upload page
2. Select a PDF or image file
3. Wait for processing to complete
4. Document will appear in the documents list

### Perform Intelligent Search
1. Go to the search page
2. Enter your query (e.g., "What are the main benefits mentioned?")
3. Optionally select specific documents to search
4. View AI-generated response with citations

## 🛠️ Development

### Adding New Features
1. Backend changes: Add routes in `backend/app/api/`
2. Frontend changes: Add components in `frontend/src/components/`
3. Update tests and documentation

### Database Schema
Documents are stored with metadata including:
- Document ID, filename, upload timestamp
- Processing status and content type
- Extracted text and embeddings
- Vector representations for similarity search

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework for Python
- [React](https://reactjs.org/) - Frontend library
- [Qdrant](https://qdrant.tech/) - Vector similarity search engine
- [LangChain](https://langchain.com/) - LLM application framework
- [Material-UI](https://mui.com/) - React UI component library

## 📞 Support

For support, please open an issue in the GitHub repository or contact the development team.

---

**Built with ❤️ By Pranav**

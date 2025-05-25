from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
from typing import List, Dict, Any

app = FastAPI(title="Document Processing System - Simplified")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Document AI API - Simplified", "version": "1.0.0"}

@app.get("/api/health-check")
@app.head("/api/health-check")
async def health_check():
    return {"status": "ok", "message": "API is running"}

@app.get("/api/queries/documents")
async def list_documents():
    """List all documents - simplified version that reads from the data directory"""
    try:
        data_dir = "/home/pranav/Desktop/Assignment-final/wasserstoff-AiInternTask/backend/data/documents"
        
        if not os.path.exists(data_dir):
            return {"documents": [], "count": 0}
        
        documents = []
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(data_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        doc_data = json.load(f)
                    
                    # Extract document info and format for frontend
                    doc_id = doc_data.get('id', filename.replace('.json', ''))
                    metadata = doc_data.get('metadata', {})
                    
                    document = {
                        "id": doc_id,
                        "filename": metadata.get('filename', 'Unknown Document'),
                        "status": "completed",  # Assume completed since it's in data dir
                        "upload_timestamp": metadata.get('upload_date', 'Unknown'),
                        "metadata": {
                            "title": metadata.get('filename', 'Unknown Document'),
                            "author": metadata.get('author'),
                            "pages": metadata.get('page_count'),
                            "file_type": metadata.get('content_type')
                        }
                    }
                    documents.append(document)
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
                    continue
        
        print(f"Returning {len(documents)} documents")
        return {"documents": documents, "count": len(documents)}
        
    except Exception as e:
        print(f"Error listing documents: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to list documents: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
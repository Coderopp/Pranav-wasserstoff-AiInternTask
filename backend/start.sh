#!/bin/bash
set -e

echo "Starting FastAPI application..."
echo "Python path: $PYTHONPATH"
echo "Current directory: $(pwd)"
echo "User: $(whoami)"

# Ensure data directories exist and have proper permissions
mkdir -p /app/data/documents /app/data/metadata /app/data/embeddings /app/logs

# Verify the app module can be imported
python -c "from app.main import app; print('App import successful')"

# Check if we can connect to any required external services
echo "Checking application health..."

# Start the server with optimized settings for document selection feature
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --loop uvloop \
    --http httptools \
    --access-log \
    --log-level info
#!/bin/bash
set -e

echo "Starting unified Document Analysis System..."
echo "Python path: $PYTHONPATH"
echo "Current directory: $(pwd)"
echo "User: $(whoami)"

# Ensure data directories exist and have proper permissions
mkdir -p /app/data/documents /app/data/metadata /app/data/embeddings /app/logs

# Start nginx in background
echo "Starting nginx..."
nginx -t  # Test nginx configuration
nginx &
NGINX_PID=$!

# Wait a moment for nginx to start
sleep 2

# Verify the backend app module can be imported
echo "Checking backend application..."
cd /app/backend
python -c "from app.main import app; print('Backend app import successful')"

# Start the FastAPI backend
echo "Starting FastAPI backend on port 8000..."
exec uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 1 \
    --loop uvloop \
    --http httptools \
    --access-log \
    --log-level info &

BACKEND_PID=$!

# Function to handle shutdown
cleanup() {
    echo "Shutting down services..."
    kill $NGINX_PID 2>/dev/null || true
    kill $BACKEND_PID 2>/dev/null || true
    exit 0
}

# Trap signals to cleanup processes
trap cleanup SIGTERM SIGINT

echo "All services started successfully!"
echo "Frontend available at: http://localhost"
echo "Backend API available at: http://localhost/api"
echo "Health check available at: http://localhost/health-check"

# Wait for both processes
wait
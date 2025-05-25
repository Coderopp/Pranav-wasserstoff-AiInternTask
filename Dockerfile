# Multi-stage Dockerfile for combined frontend and backend deployment
# Stage 1: Build Frontend
FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./
RUN npm ci --only=production

# Copy frontend source code
COPY frontend/ ./

# Build the frontend
RUN npm run build

# Stage 2: Backend Builder
FROM python:3.11-slim as backend-builder

WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy root-level requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Production Runtime
FROM python:3.11-slim

# Copy virtual environment from builder stage
COPY --from=backend-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/data/documents \
    /app/data/metadata \
    /app/data/embeddings \
    /app/logs \
    /var/log/nginx \
    && chmod -R 755 /app/data \
    && chmod -R 755 /app/logs

# Create a non-root user
RUN adduser --disabled-password --gecos "" appuser

# Copy frontend build from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Copy backend application code with proper ownership
COPY --chown=appuser:appuser backend/ /app/backend/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy unified startup script
COPY start-unified.sh /app/start-unified.sh
RUN chmod +x /app/start-unified.sh && chown appuser:appuser /app/start-unified.sh

# Ensure the appuser owns the application directory
RUN chown -R appuser:appuser /app

# Expose ports (80 for nginx, 8000 for backend)
EXPOSE 80 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/backend
ENV ENVIRONMENT=production

# Add health check for better container management
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/health-check || exit 1

# Run the unified startup script
CMD ["/app/start-unified.sh"]
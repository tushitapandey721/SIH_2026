# ==============================================================================
# IP-SAKTI Sahayak — Backend Dockerfile (FastAPI + PyTorch / HuggingFace)
# Fully compatible with: Hugging Face Spaces (16GB Free Tier), Render, Railway, Docker Compose
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=7860

WORKDIR /app

# Install minimal system dependencies for PyMuPDF and C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source code, configuration, and data assets
COPY app/ ./app/
COPY data/ ./data/

# Create runtime directories for SQLite and Qdrant with universal write permissions
# (Required for Hugging Face Spaces non-root user 1000)
RUN mkdir -p /app/qdrant_data /app/data && \
    chmod -R 777 /app/data /app/qdrant_data

# Default environment variables
ENV APP_HOST=0.0.0.0 \
    DATABASE_PATH=/app/data/ip_sakti.db \
    QDRANT_PATH=/app/qdrant_data

# Expose Hugging Face standard port (7860) and standard HTTP port (8000)
EXPOSE 7860
EXPOSE 8000

# Start Uvicorn ASGI server dynamically binding to $PORT (defaults to 7860 on HF Spaces or 8000 locally)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]

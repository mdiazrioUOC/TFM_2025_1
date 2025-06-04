# Base image
FROM python:3.11-slim

# Set environment variables (example, you can override with --env)
ENV PROJECT_DIR=/app

# Set working directory
WORKDIR $PROJECT_DIR

# Install system dependencies (optional but often needed for pip packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only necessary folders, excluding notebooks
# We'll use a .dockerignore to skip notebooks
COPY src/ ./src/
COPY resources/ ./resources/

# Copy requirements if available
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install chromadb==1.0.8
# Default command (adjust to your main app script)
CMD ["python", "src/app.py"]

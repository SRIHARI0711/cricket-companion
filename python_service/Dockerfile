# Python FastAPI Microservice Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy requirements definition first for caching layer
COPY requirements.txt ./

# Install Python packages (pre-built wheels from PyPI)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files and trained ML model artifacts
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI server with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

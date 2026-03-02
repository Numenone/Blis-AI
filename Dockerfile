FROM python:3.11-slim

WORKDIR /app

# Install build dependencies (needed for some python packages like chroma/hnswlib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 1. Copy only pyproject.toml first to cache dependencies
COPY pyproject.toml .

# 2. Install dependencies (this layer won't re-run unless pyproject.toml changes)
RUN pip install --no-cache-dir .

# 3. Copy the rest of the application
COPY app/ ./app/
COPY data/ ./data/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Run FastAPI app with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

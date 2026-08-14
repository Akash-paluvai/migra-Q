FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY pyproject.toml .

# Install Python packages
RUN pip install --no-cache-dir -e .

# Copy application source
COPY backend /app/backend
COPY datasets /app/datasets
COPY docs /app/docs

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

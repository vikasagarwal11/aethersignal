# Dockerfile for Social AE API
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY api/requirements.txt /app/api/requirements.txt
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r api/requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run the API
CMD ["cd", "api", "&&", "uvicorn", "social_api:app", "--host", "0.0.0.0", "--port", "8000"]


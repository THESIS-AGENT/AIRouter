FROM python:3.11-slim

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update --allow-releaseinfo-change || (apt-get clean && apt-get update --allow-releaseinfo-change) && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the API port
EXPOSE 8000

# Set environment variables
ENV MAX_WINDOW_SIZE=100
ENV PYTHONPATH=/app

# Command to run the FastAPI app with uvicorn
CMD ["uvicorn", "CheckHealthy:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "error"] 
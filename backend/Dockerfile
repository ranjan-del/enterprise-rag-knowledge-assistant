# Backend image for the Enterprise RAG Knowledge Assistant (FastAPI).
# NOTE: scaffolding only — image is not built during scaffolding.
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source.
COPY . .

EXPOSE 8000

# TODO: run DB migrations before starting in production.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

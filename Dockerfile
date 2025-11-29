# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# System deps (for pip, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports:
# 8000 = FastAPI backend
# 8501 = Streamlit frontend
EXPOSE 8000
EXPOSE 8501

# Default command: start FastAPI + Streamlit in same container
CMD sh -c "uvicorn backend:app --reload --host 0.0.0.0 --port 8000 & \
           streamlit run app.py --server.port=8501 --server.address=0.0.0.0"

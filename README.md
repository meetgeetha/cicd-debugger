# 🛠️ AI CI/CD Debugger — AWS ECS Deployment Guide

This project includes:
- Streamlit UI (port 8501)
- FastAPI backend (port 8000)
- Fargate ECS deployment
- Secure AWS Secrets Manager integration

---
docker build -t cicd-debugger:latest .
docker run --rm -e OPENAI_API_KEY=<openai-api-key> -p 8501:8501 -p 8000:8000 cicd-debugger:latest
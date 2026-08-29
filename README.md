# ATLAS Platform

Enterprise Hybrid Retrieval-Augmented Generation (RAG) Platform.

## Repository Architecture

```text
/atlas
  /backend     # FastAPI Python microservices & RAG engine
  /frontend    # Next.js TypeScript web application
```

## Quick Start Guide

### 1. Backend Setup

```bash
cd backend

# Start local infrastructure (PostgreSQL, Qdrant, Redis)
docker compose -f deploy/docker-compose.yml up -d

# Setup virtual environment & install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .

# Start FastAPI application
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

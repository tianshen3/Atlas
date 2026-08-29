# ATLAS Backend

FastAPI Enterprise Hybrid Retrieval-Augmented Generation (RAG) Platform.

## Quick Start

```bash
# 1. Start local infrastructure services (PostgreSQL, Qdrant, Redis)
docker compose -f deploy/docker-compose.yml up -d

# 2. Setup virtual environment & install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .

# 3. Run FastAPI Web Server
uvicorn app.main:app --reload --port 8000
```

## Stack

* **API Gateway**: FastAPI & Uvicorn
* **Database**: PostgreSQL & Alembic
* **Vector DB**: Qdrant (Dense + BM25 Sparse)
* **Background Tasks**: Celery & Redis
* **Embeddings & Reranker**: FastEmbed (`bge-small-en-v1.5`) & Cross-Encoder (`ms-marco-MiniLM-L-6-v2`)
* **LLM Engine**: OpenAI (`gpt-4o`)

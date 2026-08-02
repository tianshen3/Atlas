import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ATLAS Enterprise Hybrid RAG",
    description="Enterprise-grade Hybrid Retrieval-Augmented Generation Platform",
    version="1.0.0",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "project": "ATLAS Enterprise Hybrid RAG",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/healthz")
async def healthz():
    return {
        "status": "HEALTHY",
        "components": {
            "api": "UP",
        },
    }


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

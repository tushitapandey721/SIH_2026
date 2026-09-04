import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("IP-SAKTI.Server")

from app.api.routes import router as api_router
from app.retrieval.retrieve import get_default_retriever

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler for eager model initialization and CUDA warmup."""
    logger.info("=" * 80)
    logger.info("[STARTUP] Eagerly loading IP-SAKTI Legal Retrieval Models (BGE-M3 + BGE-Reranker-v2-M3)...")
    logger.info("=" * 80)
    
    # 1. Eagerly instantiate the singleton LegalRetriever
    retriever = get_default_retriever()
    device = retriever.device.upper()
    
    embed_dtype = next(retriever.embed_model.parameters()).dtype if hasattr(retriever.embed_model, "parameters") else "unknown"
    rerank_dtype = next(retriever.rerank_model.model.parameters()).dtype if hasattr(retriever.rerank_model, "model") else "unknown"
    num_docs = sum(len(docs) for docs in retriever.bm25_index.docs_by_jurisdiction.values()) if hasattr(retriever.bm25_index, "docs_by_jurisdiction") else 0
    
    logger.info(f"[STARTUP] Dense Embedding Model : BAAI/bge-m3 (dtype={embed_dtype}) on Device: '{device}'")
    logger.info(f"[STARTUP] CrossEncoder Model    : BAAI/bge-reranker-v2-m3 (dtype={rerank_dtype}) on Device: '{device}'")
    logger.info(f"[STARTUP] In-Memory BM25 Corpus : {num_docs} statutory chunks indexed from Qdrant '{retriever.collection_name}'")
    
    # 2. Execute GPU / CPU warmup pass so PyTorch CUDA kernels & JIT caches are pre-compiled
    logger.info("[STARTUP] Running initial CUDA warmup inference pass...")
    t_warm_start = time.perf_counter()
    warmup_results, _ = retriever.retrieve("What does Section 3(p) of the Patents Act prohibit?", jurisdiction="national")
    t_warm_ms = (time.perf_counter() - t_warm_start) * 1000
    
    logger.info(f"[STARTUP] Warmup pass completed in {t_warm_ms:.1f}ms (Top-1: {warmup_results[0].get('section', '') if warmup_results else 'None'})")
    logger.info(f"[STARTUP READY] Both embedding and reranker models successfully loaded on '{device}'. Server is ready for instant user queries.")
    logger.info("=" * 80)
    
    yield
    
    logger.info("[SHUTDOWN] Shutting down IP-SAKTI Sahayak backend.")

app = FastAPI(
    title="IP-SAKTI Sahayak API",
    description="Multilingual, Citation-Grounded RAG Assistant for Ayurvedic IP and Regulatory Affairs (National & International)",
    version="1.0.0",
    lifespan=lifespan,
)

# Custom validation exception handler returning clean 400 Bad Request
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    if errors:
        first_err = errors[0]
        field = " -> ".join([str(loc) for loc in first_err.get("loc", []) if loc != "body"])
        msg = first_err.get("msg", "Invalid input value")
        detail = f"Missing or invalid field '{field}': {msg}" if field else msg
    else:
        detail = "Invalid request payload."
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": detail},
    )

# Enable CORS for frontend and API clients
cors_env = os.getenv("CORS_ORIGINS")
if cors_env:
    origins = [orig.strip() for orig in cors_env.split(",") if orig.strip()]
else:
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/", tags=["System"])
async def root():
    """Root endpoint providing service information."""
    return {
        "service": "IP-SAKTI Sahayak Backend",
        "status": "online",
        "documentation": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

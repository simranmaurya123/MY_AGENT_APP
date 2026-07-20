import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from src.schemas import (
    ClassificationRequest,
    ClassificationResponse,
    QueryRequest,
    QueryResponse,
    UploadResponse
)
from src.orchestrator import RAGOrchestrator
from src.classifier import SUPPORTED_DOMAINS

# Global orchestrator instance loaded at startup
orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifespan events."""
    global orchestrator
    print("[API-INIT] Starting up FastAPI Application...")
    
    # Resolve directories
    model_dir = os.getenv("DISTILBERT_MODEL_DIR", "workspace/models/distilbert_model")
    kb_dir = os.getenv("KNOWLEDGE_BASE_DIR", "workspace/data/knowledge_base")
    memory_dir = os.getenv("MEMORY_DIR", "memory")
    
    print(f"[API-INIT] Initializing RAG Orchestrator (Model: {model_dir}, KB: {kb_dir})...")
    orchestrator = RAGOrchestrator(model_dir=model_dir, kb_dir=kb_dir, memory_dir=memory_dir)
    
    yield
    print("[API-SHUTDOWN] Shutting down FastAPI Application...")

app = FastAPI(
    title="Domain-Specific Educational AI Agent API",
    description="FastAPI service integrating a fine-tuned DistilBERT domain classifier with RAG-based answer generation.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Verify backend and classifier service health status."""
    global orchestrator
    classifier_status = "uninitialized"
    classifier_backend = "none"
    kb_chunks = 0
    openai_enabled = False
    
    if orchestrator is not None:
        classifier_status = "loaded"
        classifier_backend = orchestrator.classifier.backend
        kb_chunks = len(orchestrator.retriever.chunks)
        openai_enabled = orchestrator.client is not None

    return {
        "status": "healthy",
        "classifier": {
            "status": classifier_status,
            "backend": classifier_backend
        },
        "retriever": {
            "indexed_chunks": kb_chunks
        },
        "openai_enabled": openai_enabled
    }

@app.post("/classify", response_model=ClassificationResponse, status_code=status.HTTP_200_OK)
async def classify_query(request: ClassificationRequest):
    """
    Route queries to classify them into educational domains.
    Returns: Predicted domain name, confidence score, and classification backend.
    """
    global orchestrator
    if orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator model is currently loading or uninitialized."
        )
    
    try:
        domain, confidence, backend = orchestrator.classifier.classify(request.query)
        return ClassificationResponse(
            query=request.query,
            domain=domain,
            confidence=confidence,
            backend=backend
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification runtime error: {str(e)}"
        )

@app.post("/chat", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def chat_query(request: QueryRequest):
    """
    Runs classification, retrieves matching domain material, and calls LLM to generate answers.
    """
    global orchestrator
    if orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator agent is currently loading or uninitialized."
        )
        
    try:
        response_data = orchestrator.run_query(request.query, request.session_id)
        return QueryResponse(
            query=response_data["query"],
            domain=response_data["domain"],
            confidence=response_data["confidence"],
            answer=response_data["answer"],
            sources=response_data["sources"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration runtime error: {str(e)}"
        )

@app.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="The PDF document to upload."),
    domain: str = Form(..., description="The target educational domain (AI, ML, DL, NLP, RL, CV).")
):
    """
    Accepts PDF file uploads, saves them under the domain subfolder in the knowledge base,
    chunks the text, generates embeddings, and inserts them into the FAISS index.
    """
    global orchestrator
    if orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator agent is currently loading or uninitialized."
        )
        
    domain_upper = domain.strip().upper()
    if domain_upper not in SUPPORTED_DOMAINS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported domain: '{domain}'. Supported domains are: {', '.join(SUPPORTED_DOMAINS)}"
        )
        
    filename = file.filename
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF file uploads are supported currently."
        )
        
    try:
        # Save file to domain subdirectory in knowledge base
        kb_dir = Path(orchestrator.retriever.kb_dir)
        target_dir = kb_dir / domain_upper
        target_dir.mkdir(parents=True, exist_ok=True)
        
        target_path = target_dir / filename
        with open(target_path, "wb") as f:
            f.write(await file.read())
            
        # Parse and index the saved PDF dynamically
        chunks_added = orchestrator.retriever.add_document(target_path, domain_upper)
        
        return UploadResponse(
            filename=filename,
            domain=domain_upper,
            status="success",
            chunks_indexed=chunks_added
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and index PDF: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

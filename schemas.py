from pydantic import BaseModel, Field
from typing import List, Optional

class ClassificationRequest(BaseModel):
    query: str = Field(..., description="The query/question text to be classified.")

class ClassificationResponse(BaseModel):
    query: str = Field(..., description="The original query text.")
    domain: str = Field(..., description="The predicted domain (e.g. AI, ML, CV, DL, NLP, RL, or UNKNOWN).")
    confidence: float = Field(..., description="The classification confidence score (0.0 to 1.0).")
    backend: str = Field(..., description="The classification backend used (distilbert, llm, or error).")

class QueryRequest(BaseModel):
    query: str = Field(..., description="The student/user question.")
    session_id: Optional[str] = Field(None, description="Optional session/conversation identifier for maintaining chat history.")

class QueryResponse(BaseModel):
    query: str = Field(..., description="The original question asked.")
    domain: str = Field(..., description="The predicted domain routed by the classifier.")
    confidence: float = Field(..., description="Classification confidence score.")
    answer: str = Field(..., description="The generated educational answer grounded in the retrieved context.")
    sources: List[str] = Field(default=[], description="List of source file excerpts and pages used to generate the answer.")

class UploadResponse(BaseModel):
    filename: str = Field(..., description="Name of the uploaded file.")
    domain: str = Field(..., description="The domain subfolder where the file was saved.")
    status: str = Field(..., description="Status of the upload operation (e.g., success, error).")
    chunks_indexed: int = Field(0, description="The number of document chunks extracted and indexed.")

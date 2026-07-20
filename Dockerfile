# ==============================================================================
# Base Stage: Install standard system dependencies
# ==============================================================================
FROM python:3.10-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

# Install system dependencies (build tools for PyTorch/Transformers if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ==============================================================================
# Builder Stage: Install wheels
# ==============================================================================
FROM base AS builder

COPY requirements.txt .

# Install dependencies into a wheels directory to avoid compiling in runtime image
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ==============================================================================
# Runtime Stage: Copy workspace files and execute
# ==============================================================================
FROM base AS runtime

# Copy wheels from builder and install them
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy the application source code
COPY . .

# Create necessary directories for local model output, data and memory persistence
RUN mkdir -p workspace/models/distilbert_model \
             workspace/data/knowledge_base/AI \
             workspace/data/knowledge_base/ML \
             workspace/data/knowledge_base/DL \
             workspace/data/knowledge_base/NLP \
             workspace/data/knowledge_base/RL \
             workspace/data/knowledge_base/CV \
             workspace/models/faiss_index \
             memory/daily\ logs

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000
EXPOSE 8501

# Default command starts the FastAPI server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

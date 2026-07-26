import os
import re
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterable
from pypdf import PdfReader
from sklearn.feature_extraction.text import HashingVectorizer

SUPPORTED_DOMAINS = ["AI", "ML", "DL", "NLP", "RL", "CV"]
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

class TfidfEmbedder:
    """Computes sparse feature vectors normalized to unit length for Cosine Similarity search using HashingVectorizer."""
    def __init__(self):
        self.vectorizer = HashingVectorizer(n_features=5000, alternate_sign=False)
        self.dimension = 5000
        self.is_fitted = True  # Hashing vectorizer is stateless and doesn't require fitting

    def fit(self, texts: List[str]):
        """Stateless fit, no-op for compatibility."""
        self.is_fitted = True

    def embed_texts(self, texts: List[str], is_query: bool = False) -> np.ndarray:
        """Transforms input texts into L2-normalized float32 vectors using hashing."""
        sparse_vecs = self.vectorizer.transform(texts)
        dense_vecs = sparse_vecs.toarray().astype(np.float32)
        
        # Calculate L2 norms
        norms = np.linalg.norm(dense_vecs, axis=1, keepdims=True)
        # Prevent division by zero
        norms = np.where(norms == 0, 1.0, norms)
        return dense_vecs / norms


class FAISSRetriever:
    """Coordinates local text extraction, offline TF-IDF embedding generation, and FAISS vector search."""
    def __init__(
        self, 
        knowledge_base_dir: Optional[str] = None, 
        index_dir: str = "workspace/models/faiss_index"
    ):
        self.kb_dir = Path(knowledge_base_dir) if knowledge_base_dir else Path("workspace/data/knowledge_base")
        self.index_dir = Path(index_dir)
        
        self.embedder = TfidfEmbedder()
        self.index = None
        self.chunks: List[Dict[str, Any]] = []
        
        # Check if faiss is available
        try:
            import faiss
            self.faiss_available = True
        except ImportError:
            self.faiss_available = False
            print("[RETRIEVER-WARN] FAISS library not found. Vector retrieval will be unavailable.")
            
        # Ensure directories exist
        os.makedirs(self.kb_dir, exist_ok=True)
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Initialize domain folders if missing
        for dom in SUPPORTED_DOMAINS:
            os.makedirs(self.kb_dir / dom, exist_ok=True)

        if self.faiss_available:
            self.load_or_build_index()

    def load_or_build_index(self):
        """Load FAISS index and local TF-IDF model from disk, or rebuild from scratch."""
        if not self.faiss_available:
            return
            
        index_path = self.index_dir / "index.faiss"
        metadata_path = self.index_dir / "metadata.json"
        embedder_path = self.index_dir / "tfidf_embedder.pkl"
        
        if index_path.exists() and metadata_path.exists() and embedder_path.exists():
            try:
                import faiss
                print(f"[RETRIEVER] Loading FAISS index from {index_path}...")
                self.index = faiss.read_index(str(index_path))
                self.embedder = joblib.load(str(embedder_path))
                with open(metadata_path, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                print(f"[RETRIEVER] Index loaded successfully with {len(self.chunks)} chunks.")
                return
            except Exception as e:
                print(f"[RETRIEVER-WARN] Failed to load index from disk: {e}. Rebuilding...")

        # Rebuild if files are missing or loading failed
        self.rebuild_index()

    def rebuild_index(self):
        """Parse KB files and index them in FAISS file-by-file incrementally."""
        if not self.faiss_available:
            print("[RETRIEVER-WARN] FAISS is not available. Cannot rebuild index.")
            return
            
        import faiss
        print("[RETRIEVER] Rebuilding index from scratch...")
        self.chunks = []
        self.embedder = TfidfEmbedder()
        self.index = faiss.IndexFlatIP(self.embedder.dimension)
        
        # Scan knowledge base folders
        for domain_dir in sorted(self.kb_dir.iterdir()):
            if not domain_dir.is_dir():
                continue
            
            domain = domain_dir.name.upper()
            if domain not in SUPPORTED_DOMAINS:
                continue

            for file_path in sorted(domain_dir.rglob("*")):
                if not file_path.is_file():
                    continue
                
                # Parse and chunk this specific file
                start_count = len(self.chunks)
                self._parse_and_chunk_file(file_path, domain)
                new_chunks = self.chunks[start_count:]
                
                if new_chunks:
                    print(f"   [EMBEDDING] Vectorizing and adding {len(new_chunks)} chunks for {file_path.name} to RAG...")
                    new_texts = [chunk["text"] for chunk in new_chunks]
                    embeddings = self.embedder.embed_texts(new_texts)
                    self.index.add(embeddings)
                    # Save index incrementally
                    self.save_index()

        if not self.chunks:
            print("[RETRIEVER-WARN] Knowledge base is empty. Creating default blank index.")
            # Fetch a dummy embedding to resolve dimension
            self.embedder.embed_texts(["dummy"])
            self.index = faiss.IndexFlatIP(self.embedder.dimension)
            self.save_index()
            return
            
        print(f"[RETRIEVER] Rebuild complete. Dimensions: {self.index.d}, total chunks: {self.index.ntotal}")

    def save_index(self):
        """Save FAISS index, metadata, and the fitted TF-IDF vectorizer to disk."""
        if not self.faiss_available:
            return
            
        import faiss
        self.index_dir.mkdir(parents=True, exist_ok=True)
        index_path = self.index_dir / "index.faiss"
        metadata_path = self.index_dir / "metadata.json"
        embedder_path = self.index_dir / "tfidf_embedder.pkl"
        
        faiss.write_index(self.index, str(index_path))
        joblib.dump(self.embedder, str(embedder_path))
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=True, indent=2)
        print(f"[RETRIEVER] Index files written to {self.index_dir}.")

    def add_document(self, file_path: Path, domain: str) -> int:
        """Add a newly uploaded document to the index dynamically."""
        if not self.faiss_available:
            print("[RETRIEVER-WARN] FAISS is not available. Cannot add document.")
            return 0
            
        import faiss
        domain = domain.upper()
        if domain not in SUPPORTED_DOMAINS:
            raise ValueError(f"Unsupported domain: {domain}")
        
        start_count = len(self.chunks)
        self._parse_and_chunk_file(file_path, domain)
        new_chunks = self.chunks[start_count:]
        
        if not new_chunks:
            return 0
            
        print(f"[RETRIEVER] Adding {len(new_chunks)} new chunks to FAISS index...")
        texts = [chunk["text"] for chunk in new_chunks]
        
        # If the embedder hasn't been fitted on a corpus yet, fit it now
        if not self.embedder.is_fitted:
            self.rebuild_index()
            return len(self.chunks)
            
        embeddings = self.embedder.embed_texts(texts)
        
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.embedder.dimension)
            
        self.index.add(embeddings)
        self.save_index()
        return len(new_chunks)

    def retrieve(self, query: str, domain: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Query vector database and retrieve filtered, matching chunks."""
        if not self.faiss_available:
            print("[RETRIEVER-WARN] FAISS is not available. Skipping retrieval.")
            return []
            
        if not self.chunks or self.index is None or self.index.ntotal == 0 or not self.embedder.is_fitted:
            return []

        import faiss
        # Vectorize search query using local TF-IDF
        query_vector = self.embedder.embed_texts([query], is_query=True)
        
        # Search all index vectors
        k_search = min(self.index.ntotal, top_k * 5)
        distances, indices = self.index.search(query_vector, k_search)
        
        scores = distances[0]
        idxs = indices[0]
        
        target_domains = {domain.upper(), "AI"} if domain.upper() in SUPPORTED_DOMAINS else {domain.upper()}
        results = []
        
        for idx, score in zip(idxs, scores):
            if idx < 0 or idx >= len(self.chunks):
                continue
                
            chunk = self.chunks[idx]
            
            # Domain filter check (universal AI wildcard matches everything)
            if chunk["domain"] in target_domains:
                match = chunk.copy()
                match["score"] = float(score)
                results.append(match)
                
            if len(results) >= top_k:
                break
                
        return results

    def _chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 150) -> Iterable[str]:
        """Split text into chunks."""
        # Strip lone Unicode surrogates to prevent encoding/JSON errors
        text = re.sub(r'[\ud800-\udfff]', '', text)
        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned:
            return
            
        if len(cleaned) <= chunk_size:
            yield cleaned
            return
            
        start = 0
        while start < len(cleaned):
            end = min(len(cleaned), start + chunk_size)
            yield cleaned[start:end]
            if end >= len(cleaned):
                break
            start = max(0, end - overlap)

    def _parse_and_chunk_file(self, file_path: Path, domain: str):
        suffix = file_path.suffix.lower()
        # Skip files known to hang or run extremely slowly in pypdf text extraction
        slow_keywords = ["PyTorch Computer Vision Cookbook", "The Hundred Page Machine Learning BOOK"]
        if any(kw in file_path.name for kw in slow_keywords):
            print(f"   [SKIPPED] Skipping slow file to prevent indexing hang: {file_path.name}")
            return
        
        print(f"   [PARSING] Processing: {file_path.name} [{domain}]...")
        start_chunks = len(self.chunks)
        try:
            if suffix == ".pdf":
                self._parse_pdf(file_path, domain)
            elif suffix == ".csv":
                self._parse_csv(file_path, domain)
            elif suffix in {".xlsx", ".xls"}:
                self._parse_excel(file_path, domain)
            elif suffix in {".md", ".txt"}:
                self._parse_text(file_path, domain)
            
            new_chunks = len(self.chunks) - start_chunks
            print(f"   [PARSED] Finished: {file_path.name} -> Generated {new_chunks} chunks.")
        except Exception as e:
            print(f"[RETRIEVER-WARN] Failed parsing {file_path}: {e}")

    def _parse_pdf(self, file_path: Path, domain: str):
        reader = PdfReader(str(file_path))
        num_pages = len(reader.pages)
        for page_idx, page in enumerate(reader.pages, start=1):
            if page_idx % 20 == 0 or page_idx == 1 or page_idx == num_pages:
                print(f"      [PARSING] Page {page_idx}/{num_pages}...")
            try:
                text = page.extract_text() or ""
                for chunk_idx, chunk in enumerate(self._chunk_text(text), start=1):
                    self.chunks.append({
                        "domain": domain,
                        "source": f"{file_path.name} | Page {page_idx} | Chunk {chunk_idx}",
                        "text": chunk
                    })
            except Exception as e:
                print(f"      [PAGE-WARN] Error parsing page {page_idx}: {e}")

    def _parse_text(self, file_path: Path, domain: str):
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for chunk_idx, chunk in enumerate(self._chunk_text(text), start=1):
            self.chunks.append({
                "domain": domain,
                "source": f"{file_path.name} | Chunk {chunk_idx}",
                "text": chunk
            })

    def _parse_csv(self, file_path: Path, domain: str):
        import pandas as pd
        df = pd.read_csv(file_path)
        self._parse_dataframe(df, file_path, domain)

    def _parse_excel(self, file_path: Path, domain: str):
        import pandas as pd
        sheets = pd.read_excel(file_path, sheet_name=None)
        for sheet_name, df in sheets.items():
            self._parse_dataframe(df, file_path, domain, sheet_name=sheet_name)

    def _parse_dataframe(self, df: pd.DataFrame, file_path: Path, domain: str, sheet_name: Optional[str] = None):
        if df.empty:
            return
        subset = df.head(50).fillna("")
        rows = []
        for _, row in subset.iterrows():
            pieces = [f"{col}: {row[col]}" for col in subset.columns]
            rows.append("; ".join(pieces))
            
        header = f"Tabular Data: {file_path.name}"
        if sheet_name:
            header += f" | Sheet: {sheet_name}"
            
        content = header + "\n" + "\n".join(rows)
        for chunk_idx, chunk in enumerate(self._chunk_text(content, chunk_size=1000), start=1):
            self.chunks.append({
                "domain": domain,
                "source": f"{file_path.name} | Table Chunk {chunk_idx}",
                "text": chunk
            })

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

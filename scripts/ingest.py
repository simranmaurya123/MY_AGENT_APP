import os
import sys
import time
from pathlib import Path

# Add root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.retriever import FAISSRetriever

def main():
    print("==================================================")
    print("[INFO] Starting Knowledge Base Ingestion Pipeline...")
    print("==================================================")

    # Resolve default paths
    kb_dir = Path("workspace/data/knowledge_base")
    index_dir = Path("workspace/models/faiss_index")

    if not kb_dir.exists():
        print(f"[ERROR] Knowledge base directory not found at: {kb_dir.absolute()}")
        sys.exit(1)

    print(f"[INFO] Scanning files inside: {kb_dir.absolute()}")
    
    # Pre-scan domain folders and log document counts
    found_any = False
    for domain_folder in sorted(kb_dir.iterdir()):
        if domain_folder.is_dir():
            files = list(domain_folder.rglob("*"))
            files = [f for f in files if f.is_file() and not f.name.startswith(".")]
            if files:
                found_any = True
                print(f"   Domain [{domain_folder.name}]: Found {len(files)} file(s)")
                for f in files:
                    print(f"      - {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    
    if not found_any:
        print("[WARNING] No documents found in the domain folders. Index will be initialized empty.")

    print("\n[INFO] Initializing FAISS Retriever and Rebuilding Index...")
    start_time = time.time()
    
    # Initialize retriever
    retriever = FAISSRetriever(knowledge_base_dir=str(kb_dir), index_dir=str(index_dir))
    
    # Explicitly force a rebuild of the index to ingest all files afresh
    retriever.rebuild_index()
    
    elapsed = time.time() - start_time
    print("\n==================================================")
    print("[SUCCESS] Ingestion Pipeline Finished Successfully!")
    print("==================================================")
    print(f"Time Elapsed: {elapsed:.2f} seconds")
    print(f"Total Chunks Indexed: {retriever.chunk_count}")
    print(f"Index Location: {index_dir.absolute()}")
    print("==================================================")

if __name__ == "__main__":
    main()

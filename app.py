import streamlit as st
import requests
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

# FastAPI Backend Base URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page Config
st.set_page_config(
    page_title="Cognitive RAG Enterprise Agent",
    page_icon="🤖",
    layout="wide",
)

# Custom High-Fidelity CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');
    
    /* Apply custom font across app elements */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Outfit', sans-serif;
    }
    
    code, pre, [class*="code"] {
        font-family: 'Fira Code', monospace !important;
        font-size: 0.9rem !important;
    }

    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(20, 15, 45, 0.95) 0%, rgba(8, 10, 24, 0.99) 90%), #020617;
        color: #f1f5f9;
    }
    
    /* Hero header with premium gradients */
    .hero {
        padding: 3rem;
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.6) 100%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(16px);
        margin-bottom: 2.5rem;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        text-align: center;
    }
    .hero h1 {
        font-size: 3.5rem;
        margin: 0;
        background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -0.04em;
    }
    .hero p {
        margin-top: 1.25rem;
        color: #94a3b8;
        font-size: 1.30rem;
        line-height: 1.6;
        font-weight: 300;
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Grid cards */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        margin-bottom: 3rem;
    }
    
    .feature-card {
        background: rgba(15, 23, 42, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 1.75rem;
        backdrop-filter: blur(12px);
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.25);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .feature-card:hover {
        border-color: rgba(139, 92, 246, 0.4);
        transform: translateY(-4px);
        box-shadow: 0 20px 40px rgba(139, 92, 246, 0.15);
    }
    .feature-card h3 {
        margin-top: 0;
        color: #60a5fa;
        font-weight: 700;
        font-size: 1.35rem;
        margin-bottom: 0.75rem;
    }
    .feature-card p {
        color: #94a3b8;
        font-size: 0.95rem;
        line-height: 1.6;
        margin: 0;
    }
    
    /* Technical layout visualizer list */
    .tree-node {
        font-family: 'Fira Code', monospace;
        background: rgba(15, 23, 42, 0.7);
        border-left: 3px solid #8b5cf6;
        padding: 0.75rem 1.25rem;
        margin-bottom: 0.6rem;
        border-radius: 0 10px 10px 0;
        font-size: 0.9rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }
    
    /* Premium glowing badges for sources */
    .source-tag {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        margin: 0.25rem;
        border-radius: 8px;
        background: rgba(139, 92, 246, 0.12);
        border: 1px solid rgba(139, 92, 246, 0.25);
        font-family: 'Fira Code', monospace;
        font-size: 0.8rem;
        color: #c084fc;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .source-tag:hover {
        background: rgba(139, 92, 246, 0.2);
        border-color: rgba(139, 92, 246, 0.4);
        color: #e9d5ff;
        transform: scale(1.02);
    }

    .meta-tag {
        display: inline-block;
        padding: 0.25rem 0.55rem;
        margin: 0.2rem;
        border-radius: 6px;
        background: rgba(52, 211, 153, 0.12);
        border: 1px solid rgba(52, 211, 153, 0.3);
        font-size: 0.8rem;
        color: #34d399;
        font-weight: 600;
    }
    
    /* Custom style for Streamlit buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 22px rgba(139, 92, 246, 0.45) !important;
    }
    
    /* Secondary Back navigation button */
    div.stButton > button[key="back_home_btn"] {
        background: transparent !important;
        color: #a78bfa !important;
        border: 1px solid rgba(139, 92, 246, 0.4) !important;
        box-shadow: none !important;
    }
    
    .status-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        backdrop-filter: blur(12px);
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.25);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Fetch backend status
def get_backend_status():
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

backend_status = get_backend_status()

# Initialize Navigation / Pages State
if "page" not in st.session_state:
    st.session_state.page = "Landing Page"

# Initialize Chat Sessions Map
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}

# Initialize Current Active Session ID
if "current_session_id" not in st.session_state:
    # Create default first session
    first_session_id = "Initial_Session"
    st.session_state.current_session_id = first_session_id
    st.session_state.chat_sessions[first_session_id] = [
        {
            "role": "assistant",
            "content": (
                "Hello! Ask me any question about AI, ML, DL, NLP, RL, or CV. "
                "I will classify your query, retrieve relevant documentation, and synthesize a grounded answer."
            ),
            "domain": None,
            "confidence": None,
            "sources": []
        }
    ]

# Render Page Views
if st.session_state.page == "Landing Page":
    # ==========================================
    # VIEW A: ENTERPRISE LANDING PORTAL
    # ==========================================
    
    st.markdown(
        """
        <div class="hero">
            <h1>Cognitive RAG: Enterprise AI Orchestrator</h1>
            <p>
                A high-performance educational agent built for technical demonstration. It leverages a fine-tuned 
                local sequence classifier for prompt routing, combined with structured SQL database retrieval and 
                FAISS semantic search indexes.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Navigation to dashboard
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Launch Agent Console ⚡", use_container_width=True):
            st.session_state.page = "Dashboard"
            st.rerun()
            
    st.markdown("---")
    
    # Section: Core Features Grid
    st.header("🔑 Key Technical Pillars")
    st.markdown(
        """
        <div class="feature-grid">
            <div class="feature-card">
                <h3>1. local Sequence Router</h3>
                <p>Features a custom fine-tuned <b>DistilBERT</b> text classifier trained locally on CPU. It routes questions dynamically into appropriate educational namespaces (AI, ML, DL, NLP, RL, CV) with deterministic probability maps.</p>
            </div>
            <div class="feature-card">
                <h3>2. Dense Vector Indexing</h3>
                <p>Extracts text segments from curriculum PDF textbooks and publications, builds dense embedding spaces, and queries them using a local <b>FAISS</b> vector search database for dense passage retrieval.</p>
            </div>
            <div class="feature-card">
                <h3>3. SQL database query tool</h3>
                <p>Features an automated natural-language-to-SQL converter powered by <b>DuckDB</b>. It queries tabular datasets (e.g. Passenger records) on-the-fly and processes records dynamically.</p>
            </div>
            <div class="feature-card">
                <h3>4. Guardrails & Audit Logging</h3>
                <p>Performs input validation constraints, monitors tokens bandwidth limits, checks response consistency, and writes daily audits to persistent markdown documents.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Section: Architecture workflow and File Tree
    col_arch, col_tree = st.columns([1.1, 0.9], gap="large")
    
    with col_arch:
        st.subheader("🛠 Architecture Workflow Diagram")
        st.markdown(
            """
            ```
             [ User Input Query ]
                      │
                      ▼
            ┌───────────────────┐
            │   DistilBERT      │  ==> Classifies Domain namespace (e.g. "NLP")
            │   Domain Router   │      (confidence floor threshold check >= 0.60)
            └─────────┬─────────┘
                      │
             ┌────────┴────────┐
             ▼                 ▼
     [ Supported Domain ]  [ Out of Scope ] ==> Return "UNKNOWN" Rejection
             │
             ├───────────────┐
             ▼               ▼
      (RAG Pipeline)   (SQL Query Tool)
      Search FAISS     DuckDB Schema Auto-detector
      Retrieve chunks  Execute queries on CSV
             │               │
             └───────┬───────┘
                     ▼
            ┌───────────────────┐
            │   LLM Synthesis   │  ==> Grounded OpenAI chat completions
            │  (gpt-4o-mini)    │      incorporates local facts and citations
            └───────────────────┘
            ```
            """,
            unsafe_allow_html=True,
        )
        
    with col_tree:
        st.subheader("📂 Codebase Folder Structure")
        st.markdown(
            """
            <div class="tree-node">📁 src/ ── Contains core RAG & Classifier packages
                 ├── __init__.py 
                 ├── classifier.py ── DistilBERT inference wrapper
                 ├── retriever.py ── FAISS chunk retriever & PDF indexer
                 ├── orchestrator.py ── LLM tool coordination agent
                 ├── schemas.py ── Pydantic structures for API validation
                 ├── memory.py ── Memory logger and loader
                 └── query.py ── DuckDB SQL querying & schema detection</div>
            <div class="tree-node">📁 scripts/ ── Classifier training and database ingestors
                 ├── train.py ── fine-tunes DistilBERT on CPU dataset
                 └── ingest.py ── builds and writes index.faiss database</div>
            <div class="tree-node">📁 tests/ ── API unit test suites
                 └── test_api.py ── checks router endpoints & lifespan checks</div>
            <div class="tree-node">📁 ui/ ── Visual HTML dashboards and RAG pipeline visualizer</div>
            <div class="tree-node">📄 main.py ── Interactive CLI terminal interface entrypoint</div>
            <div class="tree-node">📄 api.py ── FastAPI backend services exposure server</div>
            <div class="tree-node">📄 app.py ── Streamlit multi-view frontend entrypoint</div>
            """,
            unsafe_allow_html=True,
        )

else:
    # ==========================================
    # VIEW B: CHATGPT-STYLE AGENT DASHBOARD
    # ==========================================
    
    # Sidebar layout (Persistent navigation)
    with st.sidebar:
        st.markdown("### 🛠 Navigation")
        if st.button("🏠 Back to Info Portal", key="back_home_btn", use_container_width=True):
            st.session_state.page = "Landing Page"
            st.rerun()
            
        st.markdown("---")
        st.markdown("### 💬 Active Conversations")
        
        # New session trigger button
        if st.button("➕ New Chat Session", use_container_width=True):
            new_id = f"session_{uuid.uuid4().hex[:8]}"
            st.session_state.chat_sessions[new_id] = [
                {
                    "role": "assistant",
                    "content": (
                        "Hello! Ask me any question about AI, ML, DL, NLP, RL, or CV. "
                        "I will classify your query, retrieve relevant documentation, and synthesize a grounded answer."
                    ),
                    "domain": None,
                    "confidence": None,
                    "sources": []
                }
            ]
            st.session_state.current_session_id = new_id
            st.rerun()
            
        # List recent sessions
        st.write("")
        for sess_id in list(st.session_state.chat_sessions.keys()):
            # Label sessions nicely
            first_msg = st.session_state.chat_sessions[sess_id][1]["content"][:25] + "..." if len(st.session_state.chat_sessions[sess_id]) > 1 else "Empty Chat"
            btn_label = f"💬 {first_msg}"
            
            # Highlight currently selected session
            is_active = (sess_id == st.session_state.current_session_id)
            if st.button(btn_label, key=f"sess_{sess_id}", use_container_width=True, disabled=is_active):
                st.session_state.current_session_id = sess_id
                st.rerun()
                
        st.markdown("---")
        
        # Ingestion File Uploaders Panel
        st.markdown("### 📤 Upload Center")
        
        # File selector type
        upload_type = st.radio("File Type:", ["PDF Document", "CSV Dataset"], horizontal=True)
        
        if upload_type == "PDF Document":
            pdf_file = st.file_uploader("Upload PDF curriculum material", type=["pdf"])
            pdf_domain = st.selectbox("Route Domain Namespace:", ["AI", "ML", "DL", "NLP", "RL", "CV"])
            
            if pdf_file is not None:
                if st.button("Index PDF Material", use_container_width=True):
                    if not backend_status:
                        st.error("Upload failed: Backend API server is offline.")
                    else:
                        with st.spinner("Chunking PDF and building embeddings..."):
                            try:
                                files = {"file": (pdf_file.name, pdf_file.getvalue(), "application/pdf")}
                                data = {"domain": pdf_domain}
                                response = requests.post(f"{API_URL}/upload", files=files, data=data)
                                
                                if response.status_code == 201:
                                    res_json = response.json()
                                    st.success(f"Successfully indexed {res_json['chunks_indexed']} chunks from {pdf_file.name}!")
                                    backend_status = get_backend_status()
                                else:
                                    st.error(f"Failed to process PDF: {response.json().get('detail', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"Connection failed: {e}")
                                
        else:
            csv_file = st.file_uploader("Upload CSV database file", type=["csv"])
            
            if csv_file is not None:
                if st.button("Upload CSV Dataset", use_container_width=True):
                    if not backend_status:
                        st.error("Upload failed: Backend API server is offline.")
                    else:
                        with st.spinner("Saving dataset & auto-detecting schema..."):
                            try:
                                files = {"file": (csv_file.name, csv_file.getvalue(), "text/csv")}
                                response = requests.post(f"{API_URL}/upload-csv", files=files)
                                
                                if response.status_code == 201:
                                    st.success(f"Success! {csv_file.name} saved as the active query database.")
                                else:
                                    st.error(f"Failed to save CSV: {response.json().get('detail', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"Connection failed: {e}")
                                
        st.markdown("---")
        # System Health Card
        if backend_status:
            st.caption(f"🟢 Connected | Classifier: {backend_status['classifier']['backend']}")
        else:
            st.caption("🔴 Disconnected from API Server")

    # Main Agent Workspace
    active_sess_id = st.session_state.current_session_id
    messages_list = st.session_state.chat_sessions[active_sess_id]
    
    st.markdown(
        """
        <h2 style='margin-top: 0; background: linear-gradient(90deg, #a78bfa, #60a5fa); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            🤖 Cognitive Agent Console
        </h2>
        """,
        unsafe_allow_html=True,
    )
    
    # Render conversation log
    for idx, message in enumerate(messages_list):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Metadata elements for assistant responses
            if message["role"] == "assistant":
                if message.get("domain") and message["domain"] != "UNKNOWN":
                    st.markdown(
                        f"""
                        <div style='margin-top: 0.5rem;'>
                            <span class='meta-tag'>Routed Domain: {message['domain']}</span>
                            <span class='meta-tag' style='background: rgba(96, 165, 250, 0.12); border-color: rgba(96, 165, 250, 0.3); color: #60a5fa;'>Confidence: {message['confidence']:.2f}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                if message.get("sources"):
                    sources_html = "".join([f'<span class="source-tag">{src}</span>' for src in message["sources"]])
                    st.markdown(f"<div style='margin-top:0.4rem;'><b>Sources:</b> {sources_html}</div>", unsafe_allow_html=True)

    # Chat Input block
    user_question = st.chat_input("Ask a question about AI, ML, DL, NLP, RL, or CV")
    
    if user_question:
        # Append user message to active session
        messages_list.append({
            "role": "user",
            "content": user_question,
            "domain": None,
            "confidence": None,
            "sources": []
        })
        
        with st.chat_message("user"):
            st.markdown(user_question)
            
        # Get response from API backend
        with st.chat_message("assistant"):
            if not backend_status:
                error_msg = "I'm sorry, I cannot process your request. The FastAPI backend server is currently offline."
                st.markdown(error_msg)
                messages_list.append({
                    "role": "assistant",
                    "content": error_msg,
                    "domain": None,
                    "confidence": None,
                    "sources": []
                })
            else:
                with st.spinner("Classifying query and searching vector space..."):
                    try:
                        payload = {"query": user_question}
                        response = requests.post(f"{API_URL}/chat", json=payload)
                        
                        if response.status_code == 200:
                            data = response.json()
                            answer = data["answer"]
                            domain = data["domain"]
                            confidence = data["confidence"]
                            sources = data["sources"]
                            
                            st.markdown(answer)
                            if domain and domain != "UNKNOWN":
                                st.markdown(
                                    f"""
                                    <div style='margin-top: 0.5rem;'>
                                        <span class='meta-tag'>Routed Domain: {domain}</span>
                                        <span class='meta-tag' style='background: rgba(96, 165, 250, 0.12); border-color: rgba(96, 165, 250, 0.3); color: #60a5fa;'>Confidence: {confidence:.2f}</span>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                            if sources:
                                sources_html = "".join([f'<span class="source-tag">{src}</span>' for src in sources])
                                st.markdown(f"<div style='margin-top:0.4rem;'><b>Sources:</b> {sources_html}</div>", unsafe_allow_html=True)
                                
                            messages_list.append({
                                "role": "assistant",
                                "content": answer,
                                "domain": domain,
                                "confidence": confidence,
                                "sources": sources
                            })
                        else:
                            err_txt = f"API Error: {response.json().get('detail', 'Failed to generate response')}"
                            st.error(err_txt)
                            messages_list.append({
                                "role": "assistant",
                                "content": err_txt,
                                "domain": None,
                                "confidence": None,
                                "sources": []
                            })
                    except Exception as e:
                        err_txt = f"Connection failed: {e}"
                        st.error(err_txt)
                        messages_list.append({
                            "role": "assistant",
                            "content": err_txt,
                            "domain": None,
                            "confidence": None,
                            "sources": []
                        })
        # Rerun to update chat list state
        st.rerun()

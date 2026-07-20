import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# FastAPI Backend Base URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Domain-Specific Educational AI Agent",
    page_icon="🤖",
    layout="wide",
)

st.markdown(
    """
    <!-- Import Premium Google Font -->
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
        padding: 2.5rem;
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.6) 100%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(16px);
        margin-bottom: 2rem;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        text-align: left;
    }
    .hero h1 {
        font-size: 2.85rem;
        margin: 0;
        background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -0.03em;
    }
    .hero p {
        margin-top: 1rem;
        color: #94a3b8;
        font-size: 1.15rem;
        line-height: 1.6;
        font-weight: 300;
    }
    
    /* Glassmorphic cards */
    .status-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 1.75rem;
        margin-bottom: 1.25rem;
        backdrop-filter: blur(12px);
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.25);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .status-card:hover {
        border-color: rgba(139, 92, 246, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 20px 40px rgba(139, 92, 246, 0.1);
    }
    .status-card h3 {
        margin-top: 0;
        color: #a78bfa;
        font-weight: 700;
    }
    
    /* Premium glowing badges for sources */
    .source-tag {
        display: inline-block;
        padding: 0.3rem 0.65rem;
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
    
    /* Custom style for Streamlit buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.6rem 1.5rem !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.3) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Fetch current server health and configuration status
def get_backend_status():
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

backend_status = get_backend_status()

# Hero Header section
st.markdown(
    """
    <div class="hero">
        <h1>Domain-Specific AI Agent Orchestrator</h1>
        <p>
            An educational AI assistant for <b>Artificial Intelligence (AI), Machine Learning (ML), Deep Learning (DL), 
            Natural Language Processing (NLP), Reinforcement Learning (RL), and Computer Vision (CV)</b>.<br>
            Queries are routed through a fine-tuned DistilBERT domain classifier, mapped to the correct semantic context, 
            and answered using local FAISS vector search retrieval.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main structure columns
left, right = st.columns([1.1, 1.9], gap="large")

with left:
    # Status Card
    st.markdown('<div class="status-card">', unsafe_allow_html=True)
    st.subheader("System Status")
    
    if backend_status:
        st.success("🟢 API Connected")
        st.write(f"**Classifier Backend:** {backend_status['classifier']['backend']}")
        st.write(f"**Indexed KB Chunks:** {backend_status['retriever']['indexed_chunks']}")
        st.write(f"**OpenAI Enabled:** {'Yes' if backend_status['openai_enabled'] else 'No (Offline Fallback)'}")
    else:
        st.error("🔴 API Disconnected")
        st.caption(f"Cannot reach FastAPI backend at {API_URL}. Ensure uvicorn server is running.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Document upload panel (Milestone 6 Integration)
    st.markdown('<div class="status-card">', unsafe_allow_html=True)
    st.subheader("Upload Domain Material")
    
    uploaded_file = st.file_uploader("Upload a PDF document to add to the knowledge base", type=["pdf"])
    upload_domain = st.selectbox("Target domain routing folder", ["AI", "ML", "DL", "NLP", "RL", "CV"])
    
    if uploaded_file is not None:
        if st.button("Upload and Index Document", use_container_width=True):
            if not backend_status:
                st.error("Cannot upload. Backend is unreachable.")
            else:
                with st.spinner("Processing PDF, chunking text, and building embeddings..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                        data = {"domain": upload_domain}
                        
                        response = requests.post(f"{API_URL}/upload", files=files, data=data)
                        
                        if response.status_code == 201:
                            res_json = response.json()
                            st.success(f"Success! Indexed {res_json['chunks_indexed']} chunks from {uploaded_file.name}.")
                            # Refresh status
                            backend_status = get_backend_status()
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {response.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error during upload: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

    # Supported Domains List
    st.markdown('<div class="status-card">', unsafe_allow_html=True)
    st.subheader("Supported Domains")
    st.write("`AI` (General Artificial Intelligence)")
    st.write("`ML` (Traditional Machine Learning)")
    st.write("`DL` (Deep Neural Networks)")
    st.write("`NLP` (Natural Language Processing)")
    st.write("`RL` (Reinforcement Learning)")
    st.write("`CV` (Computer Vision)")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    # Chat message storage initialization
    if "messages" not in st.session_state:
        st.session_state.messages = [
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

    # Render conversation log
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("domain"):
                st.caption(f"Routed Domain: **{message['domain']}** (Confidence: {message['confidence']:.2f})")
            if message.get("sources"):
                sources_html = "".join([f'<span class="source-tag">{src}</span>' for src in message["sources"]])
                st.markdown(f"**Sources:** {sources_html}", unsafe_allow_html=True)

    # Chat Input block
    user_question = st.chat_input("Ask a question about AI, ML, DL, NLP, RL, or CV")
    if user_question:
        # Append user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_question,
            "domain": None,
            "confidence": None,
            "sources": []
        })
        
        with st.chat_message("user"):
            st.markdown(user_question)

        # Trigger response retrieval
        with st.chat_message("assistant"):
            if not backend_status:
                error_msg = "I'm sorry, I cannot process your request. The FastAPI backend server is currently offline."
                st.markdown(error_msg)
                st.session_state.messages.append({
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
                                st.caption(f"Routed Domain: **{domain}** (Confidence: {confidence:.2f})")
                            if sources:
                                sources_html = "".join([f'<span class="source-tag">{src}</span>' for src in sources])
                                st.markdown(f"**Sources:** {sources_html}", unsafe_allow_html=True)
                            
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer,
                                "domain": domain,
                                "confidence": confidence,
                                "sources": sources
                            })
                        else:
                            err_txt = f"API Error: {response.json().get('detail', 'Failed to generate response')}"
                            st.error(err_txt)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": err_txt,
                                "domain": None,
                                "confidence": None,
                                "sources": []
                            })
                    except Exception as e:
                        err_txt = f"Connection failed: {e}"
                        st.error(err_txt)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": err_txt,
                            "domain": None,
                            "confidence": None,
                            "sources": []
                        })

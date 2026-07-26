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
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;500&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');
    
    /* Apply custom font across app text elements */
    html, body, .stMarkdown, p, h1, h2, h3, h4, h5, h6, input, button, select, textarea {
        font-family: 'Outfit', sans-serif;
    }

    /* Preserve Material Symbols font for collapse/expand toggle buttons & expanders */
    [data-testid="stSidebarCollapseButton"] *,
    [data-testid="collapsedControl"] *,
    button[aria-label*="sidebar"] *,
    [data-testid="stSidebarHeader"] button *,
    [data-testid="stHeader"] button * {
        font-family: 'Material Symbols Outlined', 'Material Icons', sans-serif !important;
        color: #f97316 !important;
        -webkit-text-fill-color: #f97316 !important;
        font-size: 1.3rem !important;
    }

    /* Fix Streamlit expander icon text overlap / raw ligature string collision */
    [data-testid="stExpander"] summary *,
    [data-testid="stExpanderToggleIcon"],
    [data-testid="stExpander"] summary span:first-child,
    details summary span:first-child,
    details summary svg {
        font-family: 'Material Symbols Outlined', 'Material Icons', sans-serif !important;
    }

    /* Clean Expander Container & Header Text */
    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1.5px solid rgba(249, 115, 22, 0.25) !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03) !important;
        margin-bottom: 1rem !important;
        overflow: hidden !important;
    }

    div[data-testid="stExpander"] summary {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }

    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span:last-child {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 700 !important;
        display: inline-block !important;
        margin-left: 0.25rem !important;
    }

    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="collapsedControl"] button {
        background-color: #ffffff !important;
        border: 1px solid rgba(249, 115, 22, 0.3) !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
        padding: 0.3rem 0.5rem !important;
    }
    
    code, pre, [class*="code"] {
        font-family: 'Fira Code', monospace !important;
        font-size: 0.9rem !important;
    }

    .stApp {
        background: radial-gradient(circle at 10% 20%, #fefcf9 0%, #f6f3ed 100%), #faf8f5;
        color: #1e293b;
    }
    
    /* Style Streamlit's native sidebar for light mode and shift up */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f5f3ef 0%, #e9e6df 100%) !important;
        border-right: 1px solid rgba(249, 115, 22, 0.15) !important;
    }
    section[data-testid="stSidebar"] > div:first-child,
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
    div[data-testid="stSidebarContent"] {
        padding-top: 0.5rem !important;
    }

    /* Force ALL text in sidebar (except icons) to be dark slate (#0f172a) and 100% legible */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] h5,
    section[data-testid="stSidebar"] h6 {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        opacity: 1 !important;
    }

    /* Radio buttons text visibility fix */
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label *,
    div[role="radiogroup"] label * {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 700 !important;
    }

    /* File Uploader Container & Widget Styling */
    div[data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        border: 2px dashed #f97316 !important;
        border-radius: 14px !important;
        padding: 0.75rem !important;
        box-shadow: 0 4px 15px rgba(249, 115, 22, 0.08) !important;
    }

    div[data-testid="stFileUploader"] section {
        background-color: #ffffff !important;
    }

    div[data-testid="stFileUploader"] label,
    div[data-testid="stFileUploader"] small,
    div[data-testid="stFileUploaderDropzoneInstructions"] * {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }

    /* Force Uploaded File Preview Box to White Card with Crisp Dark Text */
    div[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"],
    div[data-testid="stFileUploader"] [data-testid="stFileUploaderFileData"],
    div[data-testid="stFileUploader"] [data-testid="stUploadedFileInfo"],
    div[data-testid="stFileUploaderFile"],
    div[data-testid="stFileUploaderFileData"],
    div[data-testid="stUploadedFileInfo"] {
        background-color: #ffffff !important;
        border: 1.5px solid #f97316 !important;
        border-radius: 10px !important;
        padding: 0.5rem 0.75rem !important;
    }

    /* Force 100% High-Contrast Legible Bold Dark Text (#0f172a) on Uploaded Filename Box */
    div[data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"],
    div[data-testid="stFileUploaderFileName"],
    div[data-testid="stFileUploaderFileName"] *,
    div[data-testid="stFileUploaderFileData"] *,
    div[data-testid="stUploadedFileInfo"] *,
    div[data-testid="stFileUploader"] [data-testid="stFileUploaderFileData"] span,
    div[data-testid="stFileUploader"] [data-testid="stFileUploaderFileData"] div,
    div[data-testid="stFileUploader"] [data-testid="stFileUploaderFileData"] p,
    div[data-testid="stFileUploader"] [data-testid="stFileUploaderFileData"] small {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    /* Remove/Delete Icon Button inside File Preview */
    div[data-testid="stFileUploader"] button[aria-label*="Remove"],
    div[data-testid="stFileUploader"] button[aria-label*="Delete"],
    div[data-testid="stFileUploaderFile"] button,
    div[data-testid="stFileUploaderFileData"] button {
        background-color: #f97316 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        min-width: 32px !important;
        height: 32px !important;
    }

    div[data-testid="stFileUploader"] button[aria-label*="Remove"] *,
    div[data-testid="stFileUploader"] button[aria-label*="Delete"] * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    /* Force ALL Orange Action Buttons (e.g. 'Index PDF Material', 'Upload CSV Dataset', 'Browse Files') to show Bold White Text */
    div[data-testid="stButton"] button,
    div[data-testid="stFileUploader"] section button,
    div[data-testid="stFileUploaderDropzone"] button,
    section[data-testid="stSidebar"] div[data-testid="stButton"] button,
    .stButton > button {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 0.6rem 1.25rem !important;
        box-shadow: 0 3px 10px rgba(249, 115, 22, 0.25) !important;
        cursor: pointer !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    div[data-testid="stButton"] button *,
    div[data-testid="stFileUploader"] section button *,
    div[data-testid="stFileUploaderDropzone"] button *,
    section[data-testid="stSidebar"] div[data-testid="stButton"] button *,
    .stButton > button * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        opacity: 1 !important;
        visibility: visible !important;
        display: inline-block !important;
    }




    /* Input & Select Box styling overrides for light mode */
    div[data-baseweb="input"], div[data-baseweb="select"], .stTextArea textarea, .stTextInput input {
        background-color: #ffffff !important;
        border: 1px solid rgba(249, 115, 22, 0.25) !important;
        color: #1e293b !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
        border-color: #f97316 !important;
        box-shadow: 0 0 10px rgba(249, 115, 22, 0.12) !important;
    }

    /* Fix st.chat_input container & text visibility completely */
    div[data-testid="stChatInput"] {
        background-color: #ffffff !important;
        border: 2px solid #f97316 !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 20px rgba(249, 115, 22, 0.15) !important;
    }
    div[data-testid="stChatInput"] textarea,
    div[data-testid="stChatInput"] [data-baseweb="textarea"] textarea,
    .stChatInput textarea {
        background-color: #ffffff !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif !important;
    }
    div[data-testid="stChatInput"] textarea::placeholder,
    .stChatInput textarea::placeholder {
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
    }
    div[data-testid="stChatInput"] button,
    .stChatInput button {
        background-color: #f97316 !important;
        color: #ffffff !important;
        border-radius: 10px !important;
    }

    /* Force 100% High-Contrast Visible Text in Chat Messages */
    div[data-testid="stChatMessage"] {
        background-color: #ffffff !important;
        border: 1px solid rgba(249, 115, 22, 0.2) !important;
        border-radius: 16px !important;
        padding: 1.25rem 1.5rem !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03) !important;
    }

    /* Ensure EVERY paragraph, list, span, heading inside chat is dark slate (#0f172a) */
    div[data-testid="stChatMessage"] *,
    div[data-testid="stChatMessageContent"] *,
    div[data-testid="stChatMessage"] .stMarkdown,
    div[data-testid="stChatMessage"] p,
    div[data-testid="stChatMessage"] li,
    div[data-testid="stChatMessage"] span,
    div[data-testid="stChatMessage"] div,
    div[data-testid="stChatMessage"] h1,
    div[data-testid="stChatMessage"] h2,
    div[data-testid="stChatMessage"] h3,
    div[data-testid="stChatMessage"] h4,
    div[data-testid="stChatMessage"] h5,
    div[data-testid="stChatMessage"] h6,
    div[data-testid="stChatMessage"] strong,
    div[data-testid="stChatMessage"] em,
    div[data-testid="stChatMessage"] ol,
    div[data-testid="stChatMessage"] ul {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        opacity: 1 !important;
    }

    /* Code snippets inside chat messages */
    div[data-testid="stChatMessage"] code {
        background-color: #f1f5f9 !important;
        color: #ea580c !important;
        -webkit-text-fill-color: #ea580c !important;
        padding: 0.2rem 0.45rem !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }

    div[data-testid="stChatMessage"] pre code {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
    }

    /* User Message Bubble styling */
    div[data-testid="stChatMessage"]:has([aria-label*="user"]),
    div[data-testid="stChatMessage"][data-test-aria-label*="user"] {
        background: #fff7ed !important;
        border: 1px solid rgba(249, 115, 22, 0.3) !important;
    }

    /* Chat Avatar Styling to prevent font text spillover */
    div[data-testid="stChatMessageAvatar"] {
        background-color: #f97316 !important;
        color: #ffffff !important;
        border-radius: 50% !important;
        box-shadow: 0 2px 8px rgba(249, 115, 22, 0.25) !important;
    }
    
    /* Custom IDE Code Block Container styles */
    .code-window {
        background: #0f172a !important;
        border-radius: 16px !important;
        border: 1px solid rgba(0, 0, 0, 0.08) !important;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12) !important;
        text-align: left !important;
        overflow: hidden !important;
        margin-top: 1rem;
    }
    .code-header {
        background: #1e293b !important;
        padding: 0.6rem 1.25rem !important;
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    .code-dot {
        width: 11px !important;
        height: 11px !important;
        border-radius: 50% !important;
        display: inline-block !important;
    }
    .code-dot.red { background-color: #ef4444 !important; }
    .code-dot.yellow { background-color: #f59e0b !important; }
    .code-dot.green { background-color: #10b981 !important; }
    .code-title {
        color: #94a3b8 !important;
        font-size: 0.8rem !important;
        margin-left: 0.5rem !important;
        font-family: 'Fira Code', monospace !important;
    }
    .code-content {
        padding: 1.5rem !important;
        margin: 0 !important;
        color: #e2e8f0 !important;
        background: #0f172a !important;
        font-size: 0.85rem !important;
        line-height: 1.6 !important;
        overflow-x: auto !important;
    }
    
    /* Grid cards style in light mode */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        margin-bottom: 3rem;
    }
    
    .feature-card {
        background: #ffffff;
        border: 1px solid rgba(0, 0, 0, 0.05);
        border-radius: 20px;
        padding: 1.75rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.02);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .feature-card:hover {
        border-color: rgba(249, 115, 22, 0.35);
        transform: translateY(-4px);
        box-shadow: 0 15px 30px rgba(249, 115, 22, 0.08);
    }
    .feature-card h3 {
        margin-top: 0;
        color: #f97316;
        font-weight: 700;
        font-size: 1.35rem;
        margin-bottom: 0.75rem;
    }
    .feature-card p {
        color: #475569;
        font-size: 0.95rem;
        line-height: 1.6;
        margin: 0;
    }

    /* Infinite Horizontal Carousel Auto-Scrolling */
    .carousel-track-wrapper {
        overflow: hidden;
        width: 100%;
        position: relative;
        padding: 0.5rem 0 1.5rem 0;
        mask-image: linear-gradient(to right, transparent 0%, black 6%, black 94%, transparent 100%);
        -webkit-mask-image: linear-gradient(to right, transparent 0%, black 6%, black 94%, transparent 100%);
    }

    .carousel-track {
        display: flex;
        gap: 1.5rem;
        width: max-content;
        animation: scroll-left 32s linear infinite;
    }

    .carousel-track-reverse {
        display: flex;
        gap: 1.5rem;
        width: max-content;
        animation: scroll-right 36s linear infinite;
    }

    .carousel-track:hover, .carousel-track-reverse:hover {
        animation-play-state: paused;
    }

    @keyframes scroll-left {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }

    @keyframes scroll-right {
        0% { transform: translateX(-50%); }
        100% { transform: translateX(0); }
    }

    .carousel-card {
        background: #ffffff;
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 20px;
        padding: 1.5rem 1.75rem;
        width: 300px;
        flex-shrink: 0;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.02);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .carousel-card:hover {
        border-color: rgba(249, 115, 22, 0.4);
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 15px 30px rgba(249, 115, 22, 0.1);
    }

    /* Fix Mermaid diagram text, edge label and connector visibility with warm palette */
    .mermaid .node rect, .mermaid .node circle, .mermaid .node polygon,
    div[data-testid="stMarkdownContainer"] svg .node rect {
        stroke-width: 2px !important;
    }
    
    .mermaid .node .label, .mermaid .node foreignObject div,
    div[data-testid="stMarkdownContainer"] svg .node text {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
    }
    
    .mermaid .edgeLabel, .mermaid .edgeLabel span, .mermaid .edgeLabel rect, .mermaid .labelBkg, g.edgeLabel rect {
        background-color: #F7D8C5 !important;
        fill: #F7D8C5 !important;
        color: #843323 !important;
        font-weight: 700 !important;
        padding: 4px 10px !important;
        border-radius: 6px !important;
        stroke: #E3BBA6 !important;
        stroke-width: 1px !important;
    }

    /* Target ALL SVG connecting lines & arrows in Mermaid flowcharts */
    div[data-testid="stMarkdownContainer"] svg path,
    div[data-testid="stMarkdownContainer"] svg g.edgePath path,
    div[data-testid="stMarkdownContainer"] svg g.edgePaths path,
    div[data-testid="stMarkdownContainer"] svg .flowchart-link,
    .stMarkdown svg path,
    .mermaid path {
        stroke: #B33928 !important;
        stroke-width: 3.5px !important;
        stroke-opacity: 1 !important;
        stroke-dasharray: none !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    /* Target ALL SVG arrowheads */
    div[data-testid="stMarkdownContainer"] svg marker path,
    div[data-testid="stMarkdownContainer"] svg defs marker path,
    div[data-testid="stMarkdownContainer"] svg #arrowhead path,
    .stMarkdown svg marker path,
    .mermaid marker path {
        fill: #B33928 !important;
        stroke: #B33928 !important;
        stroke-width: 2px !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    /* Technical layout visualizer list */
    .tree-node {
        font-family: 'Fira Code', monospace;
        background: #ffffff;
        border-left: 3px solid #f97316;
        padding: 0.75rem 1.25rem;
        margin-bottom: 0.6rem;
        border-radius: 0 10px 10px 0;
        font-size: 0.9rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    }
    
    /* Premium glowing badges for sources */
    .source-tag {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        margin: 0.25rem;
        border-radius: 8px;
        background: rgba(249, 115, 22, 0.05);
        border: 1px solid rgba(249, 115, 22, 0.25);
        font-family: 'Fira Code', monospace;
        font-size: 0.8rem;
        color: #f97316;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .source-tag:hover {
        background: rgba(249, 115, 22, 0.12);
        border-color: rgba(249, 115, 22, 0.5);
        color: #ea580c;
        transform: scale(1.02);
    }

    .meta-tag {
        display: inline-block;
        padding: 0.25rem 0.55rem;
        margin: 0.2rem;
        border-radius: 6px;
        background: rgba(132, 204, 22, 0.08);
        border: 1px solid rgba(132, 204, 22, 0.25);
        font-size: 0.8rem;
        color: #65a30d;
        font-weight: 600;
    }
    
    /* Custom style for Streamlit buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.25) !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button *,
    div.stButton > button p,
    div.stButton > button span,
    div.stButton > button div {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(249, 115, 22, 0.35) !important;
    }

    
    /* Secondary Back navigation button */
    div.stButton > button[key="back_home_btn"] {
        background: transparent !important;
        color: #f97316 !important;
        border: 1px solid rgba(249, 115, 22, 0.4) !important;
        box-shadow: none !important;
    }
    
    .status-card {
        background: #ffffff;
        border: 1px solid rgba(0, 0, 0, 0.05);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.02);
    }
    
    /* Overrides for Streamlit standard chat bubbles to match light theme */
    div[data-testid="stChatMessage"] {
        background-color: #ffffff !important;
        border: 1px solid rgba(0, 0, 0, 0.04) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.01) !important;
    }

    /* Keyframes for animations */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes slideUp {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    @keyframes zoomIn {
        from { transform: scale(0.95); opacity: 0; }
        to { transform: scale(1); opacity: 1; }
    }
    .fade-in { animation: fadeIn 0.8s ease-out forwards; }
    .slide-up { animation: slideUp 0.8s ease-out forwards; }
    .zoom-in { animation: zoomIn 0.6s ease-out forwards; }
    
    .tech-pill {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        margin: 0.3rem;
        border-radius: 99px;
        background: #ffffff;
        border: 1px solid rgba(0,0,0,0.06);
        font-size: 0.9rem;
        font-weight: 500;
        color: #475569;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        transition: all 0.2s ease;
    }
    .tech-pill:hover {
        border-color: rgba(249, 115, 22, 0.3);
        color: #f97316;
        transform: translateY(-1px);
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

@st.cache_resource
def get_local_orchestrator():
    from src.orchestrator import RAGOrchestrator
    model_dir = os.getenv("DISTILBERT_MODEL_DIR", "workspace/models/distilbert_model")
    kb_dir = os.getenv("KNOWLEDGE_BASE_DIR", "workspace/data/knowledge_base")
    memory_dir = os.getenv("MEMORY_DIR", "memory")
    return RAGOrchestrator(model_dir=model_dir, kb_dir=kb_dir, memory_dir=memory_dir)

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

# Render Page View
if st.session_state.page == "Landing Page":
    # ==========================================
    # VIEW A: EDUQUERY AI LANDING PORTAL
    # ==========================================
    
    # Page 1: Hero Section
    st.markdown(
        """
        <div style="text-align: center; margin-top: 1.5rem;" class="fade-in">
            <span class="meta-tag">🚀 EduQuery AI</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    hero_col1, hero_col2 = st.columns([1.1, 0.9], gap="large")
    
    with hero_col1:
        st.markdown(
            """
            <div style="padding-top: 1rem;" class="fade-in">
                <h1 style="font-size: 3.5rem; font-weight: 800; line-height: 1.1; margin-top: 0.5rem; margin-bottom: 0.5rem; letter-spacing: -0.03em; color: #1e293b;">
                    EduQuery AI
                </h1>
                <p style="font-size: 1.25rem; color: #f97316; font-style: italic; font-weight: 600; margin-bottom: 1.5rem; line-height: 1.4;">
                    Domain-Specific Educational Assistant using Fine-Tuned DistilBERT & Retrieval-Augmented Generation (RAG).
                </p>
                <p style="color: #475569; font-size: 1.05rem; line-height: 1.6; font-weight: 300; margin-bottom: 1.5rem;">
                    Unlike conventional question-answering systems that search every available resource, EduQuery AI first predicts the subject of the user's query and then retrieves information only from the most relevant knowledge source. This targeted retrieval approach improves response speed, enhances answer accuracy, and reduces unnecessary document searching.
                </p>
                <p style="color: #475569; font-size: 1.05rem; line-height: 1.6; font-weight: 300; margin-bottom: 2rem;">
                    <b>About the Project:</b> The platform combines fine-tuned DistilBERT text classification, intelligent routing, Retrieval-Augmented Generation (RAG), local PDF parsing, CSV analysis, and high-performance vector search databases.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Suggested CTA buttons (Explore Workflow, View Architecture, View Results, Launch Console)
        btn_col1, btn_col2 = st.columns([1, 1])
        with btn_col1:
            if st.button("Launch Agent Console ⚡", use_container_width=True):
                st.session_state.page = "Dashboard"
                st.rerun()
        with btn_col2:
            st.markdown(
                """
                <a href="#page-2-technology-stack-workflow" style="text-decoration: none;">
                    <div style="text-align: center; background: #ffffff; border: 1px solid rgba(249, 115, 22, 0.4); color: #f97316; padding: 0.7rem 1.5rem; border-radius: 12px; font-weight: 700; font-size: 1.05rem; box-shadow: 0 4px 10px rgba(0,0,0,0.02); transition: all 0.2s ease; cursor: pointer;">
                        Explore Workflow ↓
                    </div>
                </a>
                """,
                unsafe_allow_html=True,
            )
            
    with hero_col2:
        st.markdown(
            """
            <div class="code-window zoom-in">
                <div class="code-header">
                    <span class="code-dot red"></span>
                    <span class="code-dot yellow"></span>
                    <span class="code-dot green"></span>
                    <span class="code-title">orchestrator.py</span>
                </div>
                <pre class="code-content"><code># ship your product
agent.launch(pipeline={
  <span style="color: #a2ff00;">"router"</span>: <span style="color: #eab308;">"local-distilbert"</span>,
  <span style="color: #a2ff00;">"retriever"</span>: <span style="color: #eab308;">"dense-faiss"</span>,
  <span style="color: #a2ff00;">"database"</span>: <span style="color: #eab308;">"duckdb-sql"</span>,
  <span style="color: #a2ff00;">"synthesis"</span>: <span style="color: #eab308;">"gpt-4o-mini"</span>
})</code></pre>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Supported Domains (6 cards)
        st.markdown(
            """
            <div style="margin-top: 1.25rem;">
                <h4 style="font-size: 1rem; font-weight: 700; color: #1e293b; margin-bottom: 0.75rem; text-align: center;">Supported Domains</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                    <div style="background: #ffffff; border: 1px solid rgba(132, 204, 22, 0.2); padding: 0.45rem; text-align: center; border-radius: 8px; font-size: 0.85rem; font-weight: 600; color: #334155;">🧠 Machine Learning</div>
                    <div style="background: #ffffff; border: 1px solid rgba(132, 204, 22, 0.2); padding: 0.45rem; text-align: center; border-radius: 8px; font-size: 0.85rem; font-weight: 600; color: #334155;">🕸 Deep Learning</div>
                    <div style="background: #ffffff; border: 1px solid rgba(132, 204, 22, 0.2); padding: 0.45rem; text-align: center; border-radius: 8px; font-size: 0.85rem; font-weight: 600; color: #334155;">🗣 NLP</div>
                    <div style="background: #ffffff; border: 1px solid rgba(132, 204, 22, 0.2); padding: 0.45rem; text-align: center; border-radius: 8px; font-size: 0.85rem; font-weight: 600; color: #334155;">👁 Computer Vision</div>
                    <div style="background: #ffffff; border: 1px solid rgba(132, 204, 22, 0.2); padding: 0.45rem; text-align: center; border-radius: 8px; font-size: 0.85rem; font-weight: 600; color: #334155;">🎮 Reinforcement Learning</div>
                    <div style="background: #ffffff; border: 1px solid rgba(132, 204, 22, 0.2); padding: 0.45rem; text-align: center; border-radius: 8px; font-size: 0.85rem; font-weight: 600; color: #334155;">🤖 Artificial Intelligence</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Hero section feature cards (8 cards)
    st.markdown(
        """
        <div style="margin-top: 3.5rem;">
            <h3 style="font-size: 1.75rem; font-weight: 800; color: #1e293b; text-align: center; margin-bottom: 1.75rem;">Core Capabilities</h3>
            <div class="feature-grid">
                <div class="feature-card">
                    <h4 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.1rem; font-weight: 700;">Domain Classification</h4>
                    <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Predicts the specific educational subject area before starting searches.</p>
                </div>
                <div class="feature-card">
                    <h4 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.1rem; font-weight: 700;">PDF Question Answering</h4>
                    <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Extracts text and answers questions over PDF curriculum files dynamically.</p>
                </div>
                <div class="feature-card">
                    <h4 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.1rem; font-weight: 700;">CSV Data Analysis</h4>
                    <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Executes SQL queries automatically on tabular datasets with DuckDB.</p>
                </div>
                <div class="feature-card">
                    <h4 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.1rem; font-weight: 700;">Intelligent Routing</h4>
                    <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Steers user prompts to specific modules instead of searching everything.</p>
                </div>
                <div class="feature-card">
                    <h4 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.1rem; font-weight: 700;">RAG-based Responses</h4>
                    <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Generates replies grounded in document context to eliminate hallucinations.</p>
                </div>
                <div class="feature-card">
                    <h4 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.1rem; font-weight: 700;">Semantic Search</h4>
                    <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Scans sentence embeddings in a dense multi-dimensional vector space.</p>
                </div>
                <div class="feature-card">
                    <h4 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.1rem; font-weight: 700;">Fast Retrieval</h4>
                    <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Cuts search time by narrowing the query to the single correct folder.</p>
                </div>
                <div class="feature-card">
                    <h4 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.1rem; font-weight: 700;">Subject-specific KB</h4>
                    <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Organized namespace folders corresponding to curriculum databases.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("<br><hr id='page-2-technology-stack-workflow' style='border-top: 1px solid rgba(0,0,0,0.06);'><br>", unsafe_allow_html=True)
    
    # Page 2: Technology Stack & Workflow
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2.5rem;">
            <span class="meta-tag" style="background: rgba(132, 204, 22, 0.08); border-color: rgba(132, 204, 22, 0.25); color: #65a30d; font-size: 0.8rem; padding: 0.25rem 0.65rem;">
                PIPELINE
            </span>
            <h2 style="font-size: 2.25rem; font-weight: 800; margin-top: 0.75rem; color: #1e293b;">
                Technology Stack & Workflow
            </h2>
            <p style="color: #64748b; max-width: 650px; margin: 0.5rem auto 0 auto; font-size: 1rem;">
                Powered by state-of-the-art libraries for real-time classification, vector space search, and local database compilation.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("<h4 style='font-size: 1.25rem; font-weight: 700; color: #1e293b; margin-bottom: 1.5rem; text-align: center;'>Core Technology Stack</h4>", unsafe_allow_html=True)
    
    tech_col1, tech_col2, tech_col3 = st.columns([1.1, 1, 1.1], gap="large")
    
    with tech_col1:
        st.markdown(
            """
            <div>
                <div style="font-weight: 700; color: #1e293b; font-size: 1rem; margin-bottom: 0.5rem;">🧠 Artificial Intelligence</div>
                <span class="tech-pill">DistilBERT</span>
                <span class="tech-pill">Hugging Face Transformers</span>
                <span class="tech-pill">Sentence Transformers</span>
                <span class="tech-pill">RAG</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    with tech_col2:
        st.markdown(
            """
            <div>
                <div style="font-weight: 700; color: #1e293b; font-size: 1rem; margin-bottom: 0.5rem;">⚙️ Backend & API Service</div>
                <span class="tech-pill">Python</span>
                <span class="tech-pill">FastAPI</span>
            </div>
            <div style="margin-top: 1.5rem;">
                <div style="font-weight: 700; color: #1e293b; font-size: 1rem; margin-bottom: 0.5rem;">🐳 Deployment & Packaging</div>
                <span class="tech-pill">Docker</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    with tech_col3:
        st.markdown(
            """
            <div>
                <div style="font-weight: 700; color: #1e293b; font-size: 1rem; margin-bottom: 0.5rem;">⚡ Vector Search Index</div>
                <span class="tech-pill">FAISS</span>
            </div>
            <div style="margin-top: 1.5rem;">
                <div style="font-weight: 700; color: #1e293b; font-size: 1rem; margin-bottom: 0.5rem;">📊 Data Processing</div>
                <span class="tech-pill">Pandas</span>
                <span class="tech-pill">NumPy</span>
                <span class="tech-pill">Scikit-learn</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    # Mermaid representation of the Workflow
    st.markdown(
        """
        <div style="margin-top: 2rem;">
            <h5 style="font-size: 1rem; font-weight: 700; color: #475569; text-align: center; margin-bottom: 1rem;">Logical Workflow Flowchart</h5>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(
        """
        ```mermaid
        graph TD
            User[USER] --> Query[User Query]
            Query --> DistilBERT[Fine-Tuned DistilBERT<br>Domain Classification]
            DistilBERT --> Agent[Routing Agent]
            Agent --> PDF[PDF Tool]
            Agent --> CSV[CSV Analyzer]
            Agent --> KB[Knowledge Base]
            PDF --> ST[Sentence Transformers]
            CSV --> ST
            KB --> ST
            ST --> FAISS[FAISS Vector Search]
            FAISS --> Chunks[Relevant Context]
            Chunks --> LLM[Large Language Model RAG]
            LLM --> Resp[Final Response]
            
            style User fill:#FA9884,stroke:#E57A65,stroke-width:2px,color:#ffffff
            style Query fill:#F7D8C5,stroke:#E3BBA6,stroke-width:2px,color:#4A150E
            style DistilBERT fill:#FAAA9B,stroke:#E88C7B,stroke-width:2px,color:#ffffff
            style Agent fill:#F5C2A3,stroke:#DEA483,stroke-width:2px,color:#4A150E
            style PDF fill:#FCC8BF,stroke:#E8A99E,stroke-width:1.5px,color:#4A150E
            style CSV fill:#FCC8BF,stroke:#E8A99E,stroke-width:1.5px,color:#4A150E
            style KB fill:#FCC8BF,stroke:#E8A99E,stroke-width:1.5px,color:#4A150E
            style ST fill:#F7D8C5,stroke:#E3BBA6,stroke-width:1.5px,color:#4A150E
            style FAISS fill:#F5C2A3,stroke:#DEA483,stroke-width:2px,color:#4A150E
            style Chunks fill:#FCC8BF,stroke:#E8A99E,stroke-width:1.5px,color:#4A150E
            style LLM fill:#FA9884,stroke:#E57A65,stroke-width:2px,color:#ffffff
            style Resp fill:#F5C2A3,stroke:#DEA483,stroke-width:2px,color:#4A150E
        ```
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<br><hr id='page-3-system-architecture' style='border-top: 1px solid rgba(0,0,0,0.06);'><br>", unsafe_allow_html=True)
    
    # Page 3: System Architecture
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2.5rem;">
            <span class="meta-tag" style="background: rgba(249, 115, 22, 0.08); border-color: rgba(249, 115, 22, 0.25); color: #f97316; font-size: 0.8rem; padding: 0.25rem 0.65rem;">
                ARCHITECTURE
            </span>
            <h2 style="font-size: 2.25rem; font-weight: 800; margin-top: 0.75rem; color: #1e293b;">
                System Architecture Layers
            </h2>
            <p style="color: #64748b; max-width: 650px; margin: 0.5rem auto 0 auto; font-size: 1rem;">
                Detailed look at the modular routing and context synthesis data pipeline layers.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    arch_col1, arch_col2 = st.columns([1, 1.1], gap="large")
    
    with arch_col1:
        st.markdown(
            """
            ```mermaid
            graph TD
                User[USER] --> Query[User Query]
                Query --> DistilBERT[Fine-Tuned DistilBERT<br>Domain Classification]
                DistilBERT --> Agent[Intelligent Agent]
                Agent --> PDF[PDF Retrieval]
                Agent --> CSV[CSV Tool]
                Agent --> KB[Knowledge Base]
                PDF --> ST[Sentence Transformers]
                CSV --> ST
                KB --> ST
                ST --> FAISS[FAISS Database]
                FAISS --> Chunks[Relevant Chunks]
                Chunks --> LLM[Large Language Model]
                LLM --> Resp[Generated Response]
                
                style User fill:#FA9884,stroke:#E57A65,stroke-width:2px,color:#ffffff
                style Query fill:#F7D8C5,stroke:#E3BBA6,stroke-width:2px,color:#4A150E
                style DistilBERT fill:#FAAA9B,stroke:#E88C7B,stroke-width:2px,color:#ffffff
                style Agent fill:#F5C2A3,stroke:#DEA483,stroke-width:2px,color:#4A150E
                style PDF fill:#FCC8BF,stroke:#E8A99E,stroke-width:1.5px,color:#4A150E
                style CSV fill:#FCC8BF,stroke:#E8A99E,stroke-width:1.5px,color:#4A150E
                style KB fill:#FCC8BF,stroke:#E8A99E,stroke-width:1.5px,color:#4A150E
                style ST fill:#F7D8C5,stroke:#E3BBA6,stroke-width:1.5px,color:#4A150E
                style FAISS fill:#F5C2A3,stroke:#DEA483,stroke-width:2px,color:#4A150E
                style Chunks fill:#FCC8BF,stroke:#E8A99E,stroke-width:1.5px,color:#4A150E
                style LLM fill:#FA9884,stroke:#E57A65,stroke-width:2px,color:#ffffff
                style Resp fill:#F5C2A3,stroke:#DEA483,stroke-width:2px,color:#4A150E
            ```
            """,
            unsafe_allow_html=True
        )
        
    with arch_col2:
        st.markdown(
            """
            <div style="padding-top: 1.5rem;">
                <h4 style="font-size: 1.25rem; font-weight: 700; color: #1e293b; margin-bottom: 1rem;">Architecture Description</h4>
                <p style="color: #475569; font-size: 1rem; line-height: 1.7; font-weight: 300; margin-bottom: 1rem;">
                    EduQuery AI routes questions dynamically into educational folders (namespaces) using a local fine-tuned <b>DistilBERT</b> text classifier. This ensures prompt security and eliminates long wait times by restricting document scans to the predicted folder.
                </p>
                <p style="color: #475569; font-size: 1rem; line-height: 1.7; font-weight: 300;">
                    Once domain prediction completes, our <b>intelligent agent</b> launches specific data retrievers:
                </p>
                <ul style="color: #475569; font-size: 0.95rem; line-height: 1.8; font-weight: 300; padding-left: 1.2rem;">
                    <li><b>PDF Retrieval Tool:</b> Parses curriculum materials and extracts matching paragraphs.</li>
                    <li><b>CSV Database Tool:</b> Automatically queries structural files with native SQL code using DuckDB.</li>
                    <li><b>Subject Knowledge Base:</b> Conducts vector distance searches inside partitioned namespaces.</li>
                </ul>
                <p style="color: #475569; font-size: 1rem; line-height: 1.7; font-weight: 300;">
                    Paragraph segments are compiled by <b>Sentence Transformers</b>, scanned in <b>FAISS</b> vector indices, and fed to the LLM (gpt-4o-mini) to build grounded responses.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    st.markdown("<br><hr id='page-4-model-performance' style='border-top: 1px solid rgba(0,0,0,0.06);'><br>", unsafe_allow_html=True)
    
    # Page 4: Model Performance
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2.5rem;">
            <span class="meta-tag" style="background: rgba(132, 204, 22, 0.08); border-color: rgba(132, 204, 22, 0.25); color: #65a30d; font-size: 0.8rem; padding: 0.25rem 0.65rem;">
                PERFORMANCE
            </span>
            <h2 style="font-size: 2.25rem; font-weight: 800; margin-top: 0.75rem; color: #1e293b;">
                Model Performance & Metrics
            </h2>
            <p style="color: #64748b; max-width: 650px; margin: 0.5rem auto 0 auto; font-size: 1rem;">
                Quantitative results of the fine-tuned DistilBERT router on an unseen holdout test set (151 samples).
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # 4.1 Four Metric Cards with Circular Progress Indicators
    st.markdown(
        """
        <div style="display: flex; justify-content: space-around; gap: 1rem; margin-top: 1rem; margin-bottom: 2.5rem; flex-wrap: wrap;">
            <!-- Accuracy -->
            <div style="background: #ffffff; border: 1px solid rgba(0,0,0,0.05); padding: 1.25rem 2rem; text-align: center; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.01); width: 150px;">
                <svg width="60" height="60" viewBox="0 0 36 36" style="transform: rotate(-90deg); margin: 0 auto;">
                    <circle cx="18" cy="18" r="16" fill="none" stroke="#f1f5f9" stroke-width="3" />
                    <circle cx="18" cy="18" r="16" fill="none" stroke="#84cc16" stroke-width="3" stroke-dasharray="70.86 100" stroke-linecap="round" />
                </svg>
                <div style="font-size: 1.35rem; font-weight: 800; color: #1e293b; margin-top: 0.6rem;">70.86%</div>
                <div style="font-size: 0.8rem; color: #64748b; font-weight: 600; text-transform: uppercase; margin-top: 0.2rem;">Accuracy</div>
            </div>
            <!-- Precision -->
            <div style="background: #ffffff; border: 1px solid rgba(0,0,0,0.05); padding: 1.25rem 2rem; text-align: center; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.01); width: 150px;">
                <svg width="60" height="60" viewBox="0 0 36 36" style="transform: rotate(-90deg); margin: 0 auto;">
                    <circle cx="18" cy="18" r="16" fill="none" stroke="#f1f5f9" stroke-width="3" />
                    <circle cx="18" cy="18" r="16" fill="none" stroke="#eab308" stroke-width="3" stroke-dasharray="64.19 100" stroke-linecap="round" />
                </svg>
                <div style="font-size: 1.35rem; font-weight: 800; color: #1e293b; margin-top: 0.6rem;">64.19%</div>
                <div style="font-size: 0.8rem; color: #64748b; font-weight: 600; text-transform: uppercase; margin-top: 0.2rem;">Precision</div>
            </div>
            <!-- Recall -->
            <div style="background: #ffffff; border: 1px solid rgba(0,0,0,0.05); padding: 1.25rem 2rem; text-align: center; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.01); width: 150px;">
                <svg width="60" height="60" viewBox="0 0 36 36" style="transform: rotate(-90deg); margin: 0 auto;">
                    <circle cx="18" cy="18" r="16" fill="none" stroke="#f1f5f9" stroke-width="3" />
                    <circle cx="18" cy="18" r="16" fill="none" stroke="#84cc16" stroke-width="3" stroke-dasharray="70.86 100" stroke-linecap="round" />
                </svg>
                <div style="font-size: 1.35rem; font-weight: 800; color: #1e293b; margin-top: 0.6rem;">70.86%</div>
                <div style="font-size: 0.8rem; color: #64748b; font-weight: 600; text-transform: uppercase; margin-top: 0.2rem;">Recall</div>
            </div>
            <!-- F1 Score -->
            <div style="background: #ffffff; border: 1px solid rgba(0,0,0,0.05); padding: 1.25rem 2rem; text-align: center; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.01); width: 150px;">
                <svg width="60" height="60" viewBox="0 0 36 36" style="transform: rotate(-90deg); margin: 0 auto;">
                    <circle cx="18" cy="18" r="16" fill="none" stroke="#f1f5f9" stroke-width="3" />
                    <circle cx="18" cy="18" r="16" fill="none" stroke="#f97316" stroke-width="3" stroke-dasharray="66.97 100" stroke-linecap="round" />
                </svg>
                <div style="font-size: 1.35rem; font-weight: 800; color: #1e293b; margin-top: 0.6rem;">66.97%</div>
                <div style="font-size: 0.8rem; color: #64748b; font-weight: 600; text-transform: uppercase; margin-top: 0.2rem;">F1 Score</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # 4.2 Bar Chart, Radar Chart & Confusion Matrix Images
    eval_row1_col1, eval_row1_col2 = st.columns([1, 1.2], gap="large")
    
    with eval_row1_col1:
        st.markdown("<h4 style='font-size: 1.25rem; font-weight: 700; color: #1e293b; margin-bottom: 1rem;'>Accuracy Bar & Radar Charts</h4>", unsafe_allow_html=True)
        
        # HTML/CSS Accuracy Bar Chart
        st.markdown(
            """
            <div style="display: flex; flex-direction: column; gap: 0.8rem; background: #ffffff; padding: 1.25rem; border-radius: 12px; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 4px 12px rgba(0,0,0,0.01);">
                <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; color: #1e293b; margin-bottom: 0.2rem;">
                        <span>Accuracy</span>
                        <span>70.86%</span>
                    </div>
                    <div style="background: #f1f5f9; border-radius: 99px; height: 8px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #f97316, #eab308); width: 70.86%; height: 100%; border-radius: 99px;"></div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; color: #1e293b; margin-bottom: 0.2; margin-top: 0.25rem;">
                        <span>Precision</span>
                        <span>64.19%</span>
                    </div>
                    <div style="background: #f1f5f9; border-radius: 99px; height: 8px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #f97316, #eab308); width: 64.19%; height: 100%; border-radius: 99px;"></div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; color: #1e293b; margin-bottom: 0.2; margin-top: 0.25rem;">
                        <span>Recall</span>
                        <span>70.86%</span>
                    </div>
                    <div style="background: #f1f5f9; border-radius: 99px; height: 8px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #f97316, #eab308); width: 70.86%; height: 100%; border-radius: 99px;"></div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; color: #1e293b; margin-bottom: 0.2; margin-top: 0.25rem;">
                        <span>F1 Score</span>
                        <span>66.97%</span>
                    </div>
                    <div style="background: #f1f5f9; border-radius: 99px; height: 8px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #f97316, #eab308); width: 66.97%; height: 100%; border-radius: 99px;"></div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Responsive SVG Radar Chart
        st.markdown(
            """
            <div style="margin-top: 1.5rem; background: #ffffff; padding: 1rem; border-radius: 12px; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 4px 12px rgba(0,0,0,0.01); text-align: center;">
                <span style="font-size: 0.8rem; font-weight: 700; color: #64748b; display: block; margin-bottom: 0.5rem; text-transform: uppercase;">Metrics Radar Overlay</span>
                <svg width="260" height="220" viewBox="0 0 320 220" style="margin: 0 auto; display: block;">
                  <polygon points="160,30 240,110 160,190 80,110" fill="none" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="2" />
                  <polygon points="160,50 220,110 160,170 100,110" fill="none" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="2" />
                  <polygon points="160,70 200,110 160,150 120,110" fill="none" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="2" />
                  <polygon points="160,90 180,110 160,130 140,110" fill="none" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="2" />
                  <line x1="160" y1="30" x2="160" y2="190" stroke="#cbd5e1" stroke-width="1" />
                  <line x1="80" y1="110" x2="240" y2="110" stroke="#cbd5e1" stroke-width="1" />
                  <polygon points="160,53.31 211.35,110 160,166.69 106.42,110" fill="rgba(249, 115, 22, 0.2)" stroke="#f97316" stroke-width="2" />
                  <circle cx="160" cy="53.31" r="3.5" fill="#f97316" />
                  <circle cx="211.35" cy="110" r="3.5" fill="#f97316" />
                  <circle cx="160" cy="166.69" r="3.5" fill="#f97316" />
                  <circle cx="106.42" cy="110" r="3.5" fill="#f97316" />
                  <text x="160" y="20" text-anchor="middle" font-size="10" font-weight="700" fill="#475569">Accuracy (70.86%)</text>
                  <text x="245" y="113" text-anchor="start" font-size="10" font-weight="700" fill="#475569">Precision (64.19%)</text>
                  <text x="160" y="205" text-anchor="middle" font-size="10" font-weight="700" fill="#475569">Recall (70.86%)</text>
                  <text x="75" y="113" text-anchor="end" font-size="10" font-weight="700" fill="#475569">F1 Score (66.97%)</text>
                </svg>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    with eval_row1_col2:
        st.markdown("<h4 style='font-size: 1.25rem; font-weight: 700; color: #1e293b; margin-bottom: 1rem;'>DistilBERT Confusion Matrix Analysis</h4>", unsafe_allow_html=True)
        st.image("ui/confusion_matrix.png", width=360)
        st.markdown(
            """
            <div style="margin-top: 0.8rem; color: #475569; font-size: 0.95rem; line-height: 1.6;">
                Most categories fare well—Machine Learning (ML), Natural Language Processing (NLP), Computer Vision (CV), Reinforcement Learning (RL), and Artificial Intelligence (AI) are all classified satisfactorily. 
                Deep Learning (DL) lags noticeably behind the rest due to semantic overlap: DL questions read very much like ML questions, and the model struggles to keep the two apart.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Performance Highlights & Sample table
    st.markdown(
        """
        <div style="margin-top: 2rem;">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                <div style="background: #ffffff; padding: 1rem; border-radius: 12px; border: 1px solid rgba(132, 204, 22, 0.2); box-shadow: 0 4px 6px rgba(0,0,0,0.01);">
                    <div style="font-weight: 700; color: #84cc16; margin-bottom: 0.25rem;">🚀 Faster Retrieval</div>
                    <p style="color: #64748b; font-size: 0.85rem; line-height: 1.4; margin: 0;">Bypasses full-system sweeps, scanning only the single appropriate subject folder.</p>
                </div>
                <div style="background: #ffffff; padding: 1rem; border-radius: 12px; border: 1px solid rgba(132, 204, 22, 0.2); box-shadow: 0 4px 6px rgba(0,0,0,0.01);">
                    <div style="font-weight: 700; color: #84cc16; margin-bottom: 0.25rem;">🔍 Reduced Search Space</div>
                    <p style="color: #64748b; font-size: 0.85rem; line-height: 1.4; margin: 0;">Reduces scan dimensions by 5/6ths, limiting compute to specific namespaces.</p>
                </div>
                <div style="background: #ffffff; padding: 1rem; border-radius: 12px; border: 1px solid rgba(132, 204, 22, 0.2); box-shadow: 0 4px 6px rgba(0,0,0,0.01);">
                    <div style="font-weight: 700; color: #84cc16; margin-bottom: 0.25rem;">📍 Context-aware Responses</div>
                    <p style="color: #64748b; font-size: 0.85rem; line-height: 1.4; margin: 0;">Eliminates background noise from other subjects leaking into generated RAG answers.</p>
                </div>
                <div style="background: #ffffff; padding: 1rem; border-radius: 12px; border: 1px solid rgba(132, 204, 22, 0.2); box-shadow: 0 4px 6px rgba(0,0,0,0.01);">
                    <div style="font-weight: 700; color: #84cc16; margin-bottom: 0.25rem;">🎓 Subject-specific Classification</div>
                    <p style="color: #64748b; font-size: 0.85rem; line-height: 1.4; margin: 0;">Enables targeted micro-retrieval routing designed specifically for computer science.</p>
                </div>
            </div>
            <h4 style="font-size: 1.25rem; font-weight: 700; color: #1e293b; margin-bottom: 1rem; text-align: center;">Query Classification Examples</h4>
            <table style="width: 100%; border-collapse: collapse; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.05);">
                <tr style="background: #f8fafc; border-bottom: 1px solid rgba(0,0,0,0.05); text-align: left;">
                    <th style="padding: 0.75rem 1rem; font-weight: 700; color: #1e293b; font-size: 0.9rem;">User Query Example</th>
                    <th style="padding: 0.75rem 1rem; font-weight: 700; color: #1e293b; font-size: 0.9rem;">Predicted Domain</th>
                </tr>
                <tr style="border-bottom: 1px solid rgba(0,0,0,0.03);">
                    <td style="padding: 0.75rem 1rem; color: #475569; font-size: 0.85rem; font-family: monospace;">"What is Support Vector Machine?"</td>
                    <td style="padding: 0.75rem 1rem; color: #f97316; font-size: 0.85rem; font-weight: 600;">Machine Learning</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(0,0,0,0.03);">
                    <td style="padding: 0.75rem 1rem; color: #475569; font-size: 0.85rem; font-family: monospace;">"Explain Convolutional Neural Networks."</td>
                    <td style="padding: 0.75rem 1rem; color: #f97316; font-size: 0.85rem; font-weight: 600;">Deep Learning</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(0,0,0,0.03);">
                    <td style="padding: 0.75rem 1rem; color: #475569; font-size: 0.85rem; font-family: monospace;">"What is Named Entity Recognition?"</td>
                    <td style="padding: 0.75rem 1rem; color: #f97316; font-size: 0.85rem; font-weight: 600;">Natural Language Processing</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(0,0,0,0.03);">
                    <td style="padding: 0.75rem 1rem; color: #475569; font-size: 0.85rem; font-family: monospace;">"Explain YOLO Algorithm."</td>
                    <td style="padding: 0.75rem 1rem; color: #f97316; font-size: 0.85rem; font-weight: 600;">Computer Vision</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(0,0,0,0.03);">
                    <td style="padding: 0.75rem 1rem; color: #475569; font-size: 0.85rem; font-family: monospace;">"What is Q-Learning?"</td>
                    <td style="padding: 0.75rem 1rem; color: #f97316; font-size: 0.85rem; font-weight: 600;">Reinforcement Learning</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(0,0,0,0.03);">
                    <td style="padding: 0.75rem 1rem; color: #475569; font-size: 0.85rem; font-family: monospace;">"Define Artificial Intelligence."</td>
                    <td style="padding: 0.75rem 1rem; color: #f97316; font-size: 0.85rem; font-weight: 600;">Artificial Intelligence</td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("<br><hr style='border-top: 1px solid rgba(0,0,0,0.06);'><br>", unsafe_allow_html=True)
    
    # Page 5: Project Highlights & Future Scope
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2.5rem;">
            <span class="meta-tag" style="background: rgba(234, 179, 8, 0.08); border-color: rgba(234, 179, 8, 0.25); color: #b45309; font-size: 0.8rem; padding: 0.25rem 0.65rem;">
                HIGHLIGHTS
            </span>
            <h2 style="font-size: 2.25rem; font-weight: 800; margin-top: 0.75rem; color: #1e293b;">
                Why EduQuery AI? Advantages & Future Scope
            </h2>
            <p style="color: #64748b; max-width: 650px; margin: 0.5rem auto 0 auto; font-size: 1rem;">
                Performing domain prediction before retrieval makes this educational assistant significantly more efficient than traditional educational chatbots.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Grid of 9 Advantages (Infinite Horizontal Scroll Carousel)
    st.markdown(
        """
        <div style="margin-bottom: 3.5rem;">
            <h3 style="font-size: 1.75rem; font-weight: 800; color: #1e293b; margin-bottom: 1.5rem; text-align: center;">Advantages & Capabilities</h3>
            <div class="carousel-track-wrapper">
                <div class="carousel-track">
                    <!-- First Pass -->
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">Fine-Tuned DistilBERT</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Adapted locally using a domain-specific dataset for high-accuracy routing.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">Intelligent Query Routing</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Coordinating orchestrator agent dynamically maps query domains to active sub-agents.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">Retrieval-Augmented Generation</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Anchors generation context directly in sources to construct credible responses.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">Semantic Search</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Extracts text segment embeddings to query similar phrases in a high-density index.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">PDF Support</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Loads on-the-fly user uploads, updating local FAISS namespaces with new data.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">CSV Analysis</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Translates user questions to functional database queries on tabular datasets using DuckDB.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">FastAPI Backend</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Delivers high-performance backend pipelines with clean REST routing.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">Docker Deployment</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Standardized and isolated multi-agent environments for consistent execution.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">Scalable Architecture</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Open-ended structure allowing easy ingestion of new subjects and libraries.</p>
                    </div>
                    <!-- Duplicate Pass for Seamless Infinite Loop -->
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">Fine-Tuned DistilBERT</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Adapted locally using a domain-specific dataset for high-accuracy routing.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">Intelligent Query Routing</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Coordinating orchestrator agent dynamically maps query domains to active sub-agents.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">Retrieval-Augmented Generation</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Anchors generation context directly in sources to construct credible responses.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">Semantic Search</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Extracts text segment embeddings to query similar phrases in a high-density index.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">PDF Support</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Loads on-the-fly user uploads, updating local FAISS namespaces with new data.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">CSV Analysis</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Translates user questions to functional database queries on tabular datasets using DuckDB.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">FastAPI Backend</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Delivers high-performance backend pipelines with clean REST routing.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">Docker Deployment</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Standardized and isolated multi-agent environments for consistent execution.</p>
                    </div>
                    <div class="carousel-card">
                        <h5 style="color: #f97316; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">Scalable Architecture</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Open-ended structure allowing easy ingestion of new subjects and libraries.</p>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Grid of 8 Future Scopes (Infinite Reverse Horizontal Scroll Carousel)
    st.markdown(
        """
        <div style="margin-bottom: 3.5rem;">
            <h3 style="font-size: 1.75rem; font-weight: 800; color: #1e293b; margin-bottom: 1.5rem; text-align: center;">Future Scope & Enhancements</h3>
            <div class="carousel-track-wrapper">
                <div class="carousel-track-reverse">
                    <!-- First Pass -->
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">🌐 Multilingual Support</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Enables query translation and multilingual RAG synthesizers for global learning.</p>
                    </div>
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">🎙 Voice Assistant</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Supports speech-to-text inputs and real-time auditory answers.</p>
                    </div>
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">📷 OCR Support</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Extracts text and math formulas from whiteboard screenshots and textbook captures.</p>
                    </div>
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">☁️ Cloud Deployment</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Ports local models to scalable managed container hosting (AWS, GCP).</p>
                    </div>
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">📚 Additional Technical Domains</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Extends scope to subjects like software engineering, databases, and mathematics.</p>
                    </div>
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">🎯 Personalized Learning</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Adapts reply complexity to match individual learning styles and histories.</p>
                    </div>
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">📈 Educational Analytics</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Provides instructors with student queries statistics and learning gaps logs.</p>
                    </div>
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">⚡ Live Knowledge Integration</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Interfaces with online academic indexes (ArXiv, IEEE) for state-of-the-art responses.</p>
                    </div>
                    <!-- Duplicate Pass -->
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">🌐 Multilingual Support</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Enables query translation and multilingual RAG synthesizers for global learning.</p>
                    </div>
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">🎙 Voice Assistant</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Supports speech-to-text inputs and real-time auditory answers.</p>
                    </div>
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">📷 OCR Support</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Extracts text and math formulas from whiteboard screenshots and textbook captures.</p>
                    </div>
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">☁️ Cloud Deployment</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Ports local models to scalable managed container hosting (AWS, GCP).</p>
                    </div>
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">📚 Additional Technical Domains</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Extends scope to subjects like software engineering, databases, and mathematics.</p>
                    </div>
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">🎯 Personalized Learning</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Adapts reply complexity to match individual learning styles and histories.</p>
                    </div>
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">📈 Educational Analytics</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Provides instructors with student queries statistics and learning gaps logs.</p>
                    </div>
                    <div class="carousel-card" style="border-color: rgba(132, 204, 22, 0.2);">
                        <h5 style="color: #84cc16; margin: 0 0 0.5rem 0; font-size: 1.05rem; font-weight: 700;">⚡ Live Knowledge Integration</h5>
                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin: 0;">Interfaces with online academic indexes (ArXiv, IEEE) for state-of-the-art responses.</p>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # 5.5 Professional Footer
    st.markdown(
        """
        <div style="margin-top: 4rem; padding-top: 2rem; border-top: 1px solid rgba(0,0,0,0.06); text-align: center; color: #64748b; font-size: 0.9rem; padding-bottom: 2rem;">
            <p style="font-weight: 700; color: #1e293b; font-size: 1.05rem; margin-bottom: 0.5rem;">EduQuery AI</p>
            <p style="margin-bottom: 0.5rem; font-weight: 300;">An Intelligent Subject-Aware Learning Assistant Dashboard.</p>
            <p style="font-size: 0.8rem; color: #94a3b8; font-weight: 500;">
                Designed & Developed by <b>Simran Maurya</b> &bull; B.Tech AI (2024-2028) &bull; Amity University Noida
            </p>
            <p style="font-size: 0.8rem; color: #cbd5e1; margin-top: 0.5rem;">&copy; 2026 EduQuery AI. All rights reserved.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

else:
    # ==========================================
    # VIEW B: CHATGPT-STYLE AGENT DASHBOARD
    # ==========================================
    
    # Sidebar layout (Persistent navigation)
    with st.sidebar:
        st.markdown("<h3 style='margin-top:0;'>🛠 Navigation</h3>", unsafe_allow_html=True)
        if st.button("🏠 Back to Info Portal", key="back_home_btn", use_container_width=True):
            st.session_state.page = "Landing Page"
            st.rerun()
            
        st.markdown("<div style='margin: 0.5rem 0; border-top: 1px solid rgba(0,0,0,0.08);'></div>", unsafe_allow_html=True)
        st.markdown("### 💬 Active Conversations")
        
        # New session trigger button
        if st.button("➕ New Chat Session", use_container_width=True):
            new_id = f"session_{uuid.uuid4().hex[:8]}"
            st.session_state.chat_sessions[new_id] = [
                {
                    "role": "assistant",
                    "content": (
                        "Hello! Ask me any educational question. "
                        "My fine-tuned DistilBERT classification agent will automatically detect your query's subject domain, "
                        "retrieve matching documentation, and synthesize a grounded answer."
                    ),
                    "domain": None,
                    "confidence": None,
                    "sources": []
                }
            ]
            st.session_state.current_session_id = new_id
            st.rerun()
            
        # List recent sessions
        for sess_id in list(st.session_state.chat_sessions.keys()):
            # Label sessions nicely
            first_msg = st.session_state.chat_sessions[sess_id][1]["content"][:25] + "..." if len(st.session_state.chat_sessions[sess_id]) > 1 else "Empty Chat"
            btn_label = f"💬 {first_msg}"
            
            # Highlight currently selected session
            is_active = (sess_id == st.session_state.current_session_id)
            if st.button(btn_label, key=f"sess_{sess_id}", use_container_width=True, disabled=is_active):
                st.session_state.current_session_id = sess_id
                st.rerun()
                
        st.markdown("<div style='margin: 0.5rem 0; border-top: 1px solid rgba(0,0,0,0.08);'></div>", unsafe_allow_html=True)
        
        # Ingestion File Uploaders Panel
        st.markdown("### 📤 Upload Center")
        
        # File selector type
        upload_type = st.radio("File Type:", ["PDF Document", "CSV Dataset"], horizontal=True)
        
        if upload_type == "PDF Document":
            pdf_file = st.file_uploader("Upload PDF curriculum material", type=["pdf"])
            
            if pdf_file is not None:
                if st.button("Index PDF Material", use_container_width=True):
                    with st.spinner("Analyzing topic relevance & storing in raw_uploads..."):
                        try:
                            curr_sess_id = st.session_state.current_session_id
                            local_orc = get_local_orchestrator()
                            res = local_orc.process_incoming_pdf(
                                pdf_bytes=pdf_file.getvalue(),
                                filename=pdf_file.name,
                                explicit_domain="AUTO",
                                session_id=curr_sess_id
                            )
                            
                            if res["status"] == "success":
                                st.success(f"Successfully classified '{pdf_file.name}' into domain '{res['domain']}' and indexed {res['chunks_indexed']} chunks!")
                                st.session_state.chat_sessions[curr_sess_id].append({
                                    "role": "assistant",
                                    "content": f"📎 **Document Classified & Attached:** `{pdf_file.name}`\n\n- **Target Domain Folder:** `{res['domain']}`\n- **Indexed Chunks:** `{res['chunks_indexed']}`\n\nYou can now ask me any educational questions grounded in this PDF!",
                                    "domain": res["domain"],
                                    "confidence": res.get("confidence", 1.0),
                                    "sources": [pdf_file.name]
                                })
                                st.rerun()
                            else:
                                st.warning(f"⚠️ **Off-Topic Document Detected:** `{pdf_file.name}`\n\nSaved in `workspace/data/raw_uploads/`, but **NOT** stored in Knowledge Base or indexed. Agent will not answer questions using off-topic documents.")
                        except Exception as e:
                            st.error(f"Upload error: {e}")

                                
        else:
            csv_file = st.file_uploader("Upload CSV database file", type=["csv"])
            
            if csv_file is not None:
                if st.button("Upload CSV Dataset", use_container_width=True):
                    with st.spinner("Saving dataset & auto-detecting schema..."):
                        try:
                            content = csv_file.getvalue()
                            if backend_status:
                                files = {"file": (csv_file.name, content, "text/csv")}
                                response = requests.post(f"{API_URL}/upload-csv", files=files)
                                if response.status_code == 201:
                                    st.success(f"Success! {csv_file.name} saved as the active query database.")
                                else:
                                    st.error(f"Failed to save CSV: {response.json().get('detail', 'Unknown error')}")
                            else:
                                with open("Titanic.csv", "wb") as f:
                                    f.write(content)
                                Path("workspace/data").mkdir(parents=True, exist_ok=True)
                                with open("workspace/data/Titanic.csv", "wb") as f:
                                    f.write(content)
                                st.success(f"Success! {csv_file.name} saved as active query database (Local Mode).")
                        except Exception as e:
                            st.error(f"Upload error: {e}")
                                
        st.markdown("---")
        # System Health Card
        if backend_status:
            st.caption(f"🟢 Connected API | Classifier: {backend_status['classifier']['backend']}")
        else:
            st.caption("⚡ Local Orchestrator Active (Direct Embedded Engine)")

    # Main Agent Workspace
    active_sess_id = st.session_state.current_session_id
    messages_list = st.session_state.chat_sessions[active_sess_id]
    
    st.markdown(
        """
        <h2 style='margin-top: 0; background: linear-gradient(90deg, #a2ff00, #ffff00, #ffb000); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            🤖 Cognitive Agent Console
        </h2>
        """,
        unsafe_allow_html=True,
    )
    
    # Render conversation log
    for idx, message in enumerate(messages_list):
        avatar_icon = "🤖" if message["role"] == "assistant" else "👤"
        with st.chat_message(message["role"], avatar=avatar_icon):
            st.markdown(message["content"])
            
            # Metadata elements for assistant responses
            if message["role"] == "assistant":
                if message.get("domain") and message["domain"] != "UNKNOWN":
                    st.markdown(
                        f"""
                        <div style='margin-top: 0.5rem;'>
                            <span class='meta-tag'>Routed Domain: {message['domain']}</span>
                            <span class='meta-tag' style='background: rgba(255, 176, 0, 0.12); border-color: rgba(255, 176, 0, 0.3); color: #ffb000;'>Confidence: {message['confidence']:.2f}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                if message.get("sources"):
                    sources_html = "".join([f'<span class="source-tag">{src}</span>' for src in message["sources"]])
                    st.markdown(f"<div style='margin-top:0.4rem;'><b>Sources:</b> {sources_html}</div>", unsafe_allow_html=True)

    # Chat Input block
    user_question = st.chat_input("Ask any question (DistilBERT auto-classifies domain)...")

    
    if user_question:
        # Append user message to active session
        messages_list.append({
            "role": "user",
            "content": user_question,
            "domain": None,
            "confidence": None,
            "sources": []
        })
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_question)
            
        # Get response from API backend or local orchestrator fallback
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Classifying query and searching vector space..."):
                try:
                    if backend_status:
                        payload = {"query": user_question, "session_id": active_sess_id}
                        response = requests.post(f"{API_URL}/chat", json=payload)
                        if response.status_code == 200:
                            data = response.json()
                            answer = data["answer"]
                            domain = data["domain"]
                            confidence = data["confidence"]
                            sources = data["sources"]
                        else:
                            answer = f"API Error: {response.json().get('detail', 'Failed to generate response')}"
                            domain = None
                            confidence = None
                            sources = []
                    else:
                        local_orc = get_local_orchestrator()
                        data = local_orc.run_query(user_question, active_sess_id)
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
                                <span class='meta-tag' style='background: rgba(255, 176, 0, 0.12); border-color: rgba(255, 176, 0, 0.3); color: #ffb000;'>Confidence: {confidence:.2f}</span>
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
                except Exception as e:
                    err_txt = f"Connection / Processing error: {e}"
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

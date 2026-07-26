import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from openai import OpenAI

from .classifier import DistilBertClassifier, SUPPORTED_DOMAINS
from .retriever import FAISSRetriever
from .memory import MemoryManager
from .query import QueryContext

load_dotenv()

# Declare OpenAI Function calling tools
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_csv",
            "description": "Query the Titanic passenger CSV dataset using natural language. The tool converts the question into SQL, runs it on the data, and returns the records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The natural language question to execute as SQL on Titanic.csv. Example: 'Find all survivors in first class'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the FAISS vector database for relevant educational material in a given domain (AI, ML, DL, NLP, RL, CV).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to match against indexed documents."
                    },
                    "domain": {
                        "type": "string",
                        "description": "The target domain to filter the search (AI, ML, DL, NLP, RL, CV)."
                    }
                },
                "required": ["query", "domain"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a local file. Supports text files, markdown, and automatically extracts text from PDF documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The filesystem path of the file to read. E.g. 'workspace/data/myfile.pdf'"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_to_long_term_memory",
            "description": "Save important information to long-term memory that should be remembered across conversations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The information to save to long-term memory."
                    }
                },
                "required": ["content"]
            }
        }
    }
]

class RAGOrchestrator:
    """Core orchestrator agent coordinating classification, tool execution, and OpenAI tool calling."""
    def __init__(
        self,
        model_dir: Optional[str] = None,
        kb_dir: Optional[str] = None,
        memory_dir: str = "memory"
    ):
        self.confidence_floor = float(os.getenv("DOMAIN_CONFIDENCE_FLOOR", "0.45"))
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Initialize modules
        self.classifier = DistilBertClassifier(model_dir=model_dir, min_confidence=self.confidence_floor)
        self.retriever = FAISSRetriever(knowledge_base_dir=kb_dir)
        self.memory_manager = MemoryManager(memory_dir=memory_dir)
        
        # Initialize OpenAI Client
        openai_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=openai_key) if openai_key else None
        if not self.client:
            print("[ORCHESTRATOR-WARN] OpenAI API key is missing. Running in offline fallback mode.")
            
        # Session Memory Store: session_id -> {"history": [], "last_domain": None, "active_pdf_path": None, "active_pdf_name": None}
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def set_session_pdf(self, session_id: str, pdf_path: str, pdf_name: str):
        """Associates an uploaded PDF document with a specific chat session."""
        session_key = session_id or "default"
        if session_key not in self.sessions:
            self.sessions[session_key] = {"history": [], "last_domain": None, "active_pdf_path": None, "active_pdf_name": None}
        self.sessions[session_key]["active_pdf_path"] = pdf_path
        self.sessions[session_key]["active_pdf_name"] = pdf_name

    def process_incoming_pdf(
        self,
        pdf_bytes: bytes,
        filename: str,
        explicit_domain: str = "AUTO",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes an incoming PDF document according to domain relevance:
        1. Saves file to 'workspace/data/raw_uploads/<filename>'.
        2. Extracts text sample to classify topic domain (AI, ML, DL, NLP, RL, CV).
        3. If domain is valid (relevant educational subject):
           - Copies file to 'workspace/data/knowledge_base/<DOMAIN>/<filename>'.
           - Indexes chunks into FAISS vector database.
        4. If domain is UNKNOWN or off-topic:
           - Retains file in raw_uploads only.
           - Rejects file from Knowledge Base & vector indexing.
        """
        import shutil
        raw_uploads_dir = Path("workspace/data/raw_uploads")
        raw_uploads_dir.mkdir(parents=True, exist_ok=True)

        raw_file_path = raw_uploads_dir / filename
        with open(raw_file_path, "wb") as f:
            f.write(pdf_bytes)

        # Extract text sample for topic classification
        sample_text = ""
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(raw_file_path))
            for page in reader.pages[:3]:
                extracted = page.extract_text()
                if extracted:
                    sample_text += extracted + " "
                if len(sample_text) >= 1000:
                    break
        except Exception as e:
            print(f"[ORCHESTRATOR-WARN] Could not extract text sample from {filename}: {e}")

        # Determine domain via explicit input or auto-classification
        domain_choice = (explicit_domain or "AUTO").strip().upper()
        if domain_choice in SUPPORTED_DOMAINS:
            target_domain = domain_choice
            confidence = 1.0
        else:
            query_for_classifier = f"{filename} {sample_text[:500]}".strip()
            target_domain, confidence, _ = self.classifier.classify(query_for_classifier)

        if target_domain in SUPPORTED_DOMAINS and target_domain != "UNKNOWN":
            kb_dir = Path(self.retriever.kb_dir)
            target_dir = kb_dir / target_domain
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / filename

            # Copy file to domain folder inside Knowledge Base
            shutil.copy2(str(raw_file_path), str(target_path))

            # Add document to FAISS vector index
            chunks_indexed = self.retriever.add_document(target_path, target_domain)

            if session_id:
                self.set_session_pdf(session_id, str(target_path), filename)

            return {
                "status": "success",
                "filename": filename,
                "domain": target_domain,
                "confidence": confidence,
                "chunks_indexed": chunks_indexed,
                "target_path": str(target_path),
                "message": f"Document '{filename}' is classified under {target_domain} domain and successfully indexed into Knowledge Base ({chunks_indexed} chunks)."
            }
        else:
            return {
                "status": "off_domain",
                "filename": filename,
                "domain": "UNKNOWN",
                "confidence": confidence,
                "chunks_indexed": 0,
                "target_path": str(raw_file_path),
                "message": f"Document '{filename}' is off-topic / unrelated to educational domains (AI, ML, DL, NLP, RL, CV). It is saved in 'workspace/data/raw_uploads' but will NOT be stored in Knowledge Base or indexed for answers."
            }

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:

        """Executes the specific tool dynamically called by the LLM."""
        try:
            if tool_name == "query_csv":
                query = tool_input.get("query", "")
                result = QueryContext(query).query_csv()
                return result
            
            elif tool_name == "search_knowledge_base":
                query = tool_input.get("query", "")
                domain = tool_input.get("domain", "")
                matches = self.retriever.retrieve(query, domain, top_k=4)
                if not matches:
                    return "No relevant materials found in the vector database."
                
                context_pieces = []
                for i, match in enumerate(matches, 1):
                    context_pieces.append(
                        f"[{i}] [Source: {match.get('source')}] [Domain: {match.get('domain')}]\n{match['text']}"
                    )
                return "\n\n".join(context_pieces)

            elif tool_name == "read_file":
                path = tool_input.get("path", "")
                # Safe path resolution
                if not os.path.exists(path):
                    alt_path = Path("workspace/data") / os.path.basename(path)
                    if alt_path.exists():
                        path = str(alt_path)
                    else:
                        return f"File not found: {path}"
                
                if path.lower().endswith(".pdf"):
                    from pypdf import PdfReader
                    reader = PdfReader(path)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() or ""
                    return text
                else:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        return f.read()

            elif tool_name == "save_to_long_term_memory":
                content = tool_input.get("content", "")
                self.memory_manager.write_long_term(content)
                return "Information saved to long-term memory."

            else:
                return f"Error: Unknown tool {tool_name}"
        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"

    def run_query(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the full routing, dynamic tool calling, multi-turn conversational context, and response synthesis loop.
        """
        query = query.strip()
        if not query:
            return {
                "query": query,
                "domain": "UNKNOWN",
                "confidence": 0.0,
                "answer": "Please ask a question related to AI, ML, DL, NLP, RL, or CV.",
                "sources": []
            }

        session_key = session_id or "default"
        if session_key not in self.sessions:
            self.sessions[session_key] = {"history": [], "last_domain": None, "active_pdf_path": None, "active_pdf_name": None}

        session_data = self.sessions[session_key]
        last_domain = session_data.get("last_domain")
        active_pdf_path = session_data.get("active_pdf_path")
        active_pdf_name = session_data.get("active_pdf_name")

        # Step 1: Classify Domain
        domain, confidence, classifier_backend = self.classifier.classify(query)
        
        # Follow-up query domain inheritance & uploaded PDF session context:
        pdf_keywords = ["pdf", "file", "document", "written", "summarize", "read", "content", "explain", "paper", "what", "whats", "whats in", "this"]
        is_pdf_query = bool(active_pdf_path) and any(w in query.lower() for w in pdf_keywords)
        
        if is_pdf_query:
            domain = last_domain or "AI"
            confidence = max(confidence, 0.95)
        elif (confidence < self.confidence_floor or domain not in SUPPORTED_DOMAINS) and last_domain in SUPPORTED_DOMAINS:
            domain = last_domain
            confidence = max(confidence, 0.85)

        # Scoping validation
        if domain not in SUPPORTED_DOMAINS and not is_pdf_query:
            rejection_text = (
                f"I only answer educational questions in AI, ML, DL, NLP, RL, and CV. "
                f"Your query was classified under '{domain}' with confidence {confidence:.2f}. "
                "Please ask an on-topic question."
            )
            return {
                "query": query,
                "domain": domain,
                "confidence": confidence,
                "answer": rejection_text,
                "sources": []
            }

        # Update last domain in session
        session_data["last_domain"] = domain

        # Initialize conversation messages for LLM call
        messages = []
        
        # System instructions with strict domain scoping & multi-turn conversation guidance
        system_prompt = (
            "STRICT DOMAIN SCOPING MANDATE:\n"
            "You are an EXCLUSIVE educational AI agent dedicated STRICTLY to Artificial Intelligence, Machine Learning, Deep Learning, Natural Language Processing, Reinforcement Learning, and Computer Vision (AI, ML, DL, NLP, RL, CV).\n\n"
            "CRITICAL RULES:\n"
            "1. STRICT DOMAIN BOUNDARY: You MUST ONLY answer educational, technical, mathematical, or programming questions directly relevant to AI, ML, DL, NLP, RL, or CV, or questions about uploaded curriculum documents.\n"
            "2. ABSOLUTE OFF-TOPIC REJECTION: If the user asks ANY question outside these 6 educational domains (e.g. cooking, recipes, making curd/food, sports, entertainment, personal advice, general trivia, weather, politics, or non-computer science topics), you MUST STRICTLY REFUSE TO ANSWER.\n"
            "3. CHAT CONTEXT CONTINUITY: You maintain context from previous turns in this session. If the user asks a follow-up question (e.g., 'explain in depth', 'give an example', 'summarize it', 'tell me more'), interpret and answer their request in the context of the preceding educational topic.\n"
            "4. TOOL USAGE: Always use `search_knowledge_base` to retrieve relevant document facts before answering technical questions in AI, ML, DL, NLP, RL, CV.\n"
            f"Active Subject Domain: {domain}."
        )

        if active_pdf_path:
            system_prompt += (
                f"\n\nATTACHED SESSION DOCUMENT:\n"
                f"The user has attached/uploaded a PDF document to this active chat session: '{active_pdf_name}' (Local File Path: '{active_pdf_path}').\n"
                f"CRITICAL INSTRUCTIONS FOR UPLOADED PDF QUERIES:\n"
                f"1. When the user asks 'whats in this pdf', 'what is written in this file', 'summarize this document', or questions about the PDF, "
                f"you MUST call the tool `read_file` with path='{active_pdf_path}' to extract and read its text content.\n"
                f"2. DOMAIN CHECK ON PDF CONTENT:\n"
                f"   - IF the PDF text is ON-TOPIC (relevant to AI, ML, DL, NLP, RL, CV, computer science, data science, math, or academic/technical subjects), "
                f"     provide a complete, structured, grounded summary and answer all user questions accurately.\n"
                f"   - IF the PDF text is OFF-TOPIC (e.g., a cooking recipe book, fiction novel, sports, general entertainment, or non-educational topic), "
                f"     REJECT IT politely: 'The uploaded PDF ({active_pdf_name}) is outside my supported educational domains (AI, ML, DL, NLP, RL, CV). I am a domain-specific agent and cannot process non-educational/off-topic documents.'\n"
                f"3. NEVER ask the user for a path; you ALREADY have the path '{active_pdf_path}'."
            )


        messages.append({"role": "system", "content": system_prompt})


        # Load skills dynamically from SkillRegistry
        try:
            from .skill_registry import SkillRegistry
            skill_registry = SkillRegistry(skills_dir=str(Path(__file__).parent.parent / "skills"))
            messages.append({"role": "system", "content": skill_registry.get_menu()})
        except Exception as e:
            print(f"[ORCHESTRATOR-WARN] Skill Registry load failed: {e}")

        # Load Long-Term Memory
        long_term = self.memory_manager.read_long_term()
        if long_term:
            messages.append({"role": "system", "content": f"[Long-Term Memory]\n{long_term}"})

        # Inject recent chat history (up to last 6 messages / 3 turns)
        recent_history = session_data.get("history", [])[-6:]
        for h_msg in recent_history:
            messages.append({"role": h_msg["role"], "content": h_msg["content"]})

        # Add current user query
        messages.append({"role": "user", "content": query})

        if not self.client:
            # Offline fallback mode
            return {
                "query": query,
                "domain": domain,
                "confidence": confidence,
                "answer": f"Offline mode: OpenAI client unconfigured.\nRouted Domain: {domain}",
                "sources": []
            }

        sources = []
        try:
            # First API call with tool schemas
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,
                tools=TOOLS
            )

            # Process tool calls in a loop
            while response.choices[0].finish_reason == "tool_calls":
                assistant_message = response.choices[0].message
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": assistant_message.tool_calls
                })
                
                # Execute each tool call
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_input = json.loads(tool_call.function.arguments)
                    
                    # Track sources used
                    if tool_name == "read_file":
                        sources.append(os.path.basename(tool_input.get("path", "")))
                    elif tool_name == "query_csv":
                        sources.append("Titanic.csv")
                    elif tool_name == "search_knowledge_base":
                        sources.append(f"Vector DB (Query: {tool_input.get('query')})")
                        
                    tool_result = self.execute_tool(tool_name, tool_input)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                
                # Continue completion
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.3,
                    tools=TOOLS
                )

            # Get final answer
            answer = response.choices[0].message.content or ""
            
            # Store turn in session history for multi-turn chat continuity
            session_data["history"].append({"role": "user", "content": query})
            session_data["history"].append({"role": "assistant", "content": answer})
            if len(session_data["history"]) > 20:
                session_data["history"] = session_data["history"][-20:]

            # Write history log via memory manager
            self.memory_manager.write_daily_log(
                f"User: {query}\nDomain: {domain} (Conf: {confidence:.2f})\nAnswer: {answer[:150]}...\nSources: {sources}"
            )
            
            return {
                "query": query,
                "domain": domain,
                "confidence": confidence,
                "answer": answer,
                "sources": list(set(sources))
            }
            
        except Exception as e:
            return {
                "query": query,
                "domain": domain,
                "confidence": confidence,
                "answer": f"Error running agent loop: {e}",
                "sources": []
            }

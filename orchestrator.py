import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from openai import OpenAI

from classifier import DistilBertClassifier, SUPPORTED_DOMAINS
from retriever import FAISSRetriever
from memory import MemoryManager
from query import QueryContext

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
        Executes the full routing, dynamic tool calling, and response synthesis loop.
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

        # Step 1: Classify Domain
        domain, confidence, classifier_backend = self.classifier.classify(query)
        
        # Scoping validation
        if domain not in SUPPORTED_DOMAINS or confidence < self.confidence_floor:
            rejection_text = (
                f"I only answer questions in AI, ML, DL, NLP, RL, and CV. "
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

        # Initialize conversation messages for this execution
        messages = []
        
        # System instructions
        system_prompt = (
            "You are a domain-specific educational AI agent. You are helpful, structured, and concise.\n"
            f"The user query has been routed to the domain: {domain}.\n"
            "You have access to tools that query tabular CSV data, search a FAISS vector database (knowledge base), "
            "read files (including PDFs), or store memories.\n"
            "Answer the question based on the retrieved facts. If the information is not available, "
            "say so clearly. Supported domains are: AI, ML, DL, NLP, RL, CV."
        )
        messages.append({"role": "system", "content": system_prompt})

        # Load skills dynamically from SkillRegistry
        try:
            from skill_registry import SkillRegistry
            skill_registry = SkillRegistry(skills_dir=str(Path(__file__).parent / "skills"))
            messages.append({"role": "system", "content": skill_registry.get_menu()})
        except Exception as e:
            print(f"[ORCHESTRATOR-WARN] Skill Registry load failed: {e}")

        # Load Long-Term Memory
        long_term = self.memory_manager.read_long_term()
        if long_term:
            messages.append({"role": "system", "content": f"[Long-Term Memory]\n{long_term}"})

        # Add user query
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

            # Process tool calls in a loop (exactly like in main.py)
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

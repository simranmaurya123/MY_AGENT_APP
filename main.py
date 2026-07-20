from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from src.token_utils import threshold_compress, count_all_tokens, get_token_usage_report
from src.memory import MemoryManager
from src.query import QueryContext
import subprocess
from pathlib import Path
from src.skill_registry import SkillRegistry
from src.classifier import DistilBertClassifier, SUPPORTED_DOMAINS
from src.retriever import FAISSRetriever

# Load environment variables
load_dotenv()

model = "gpt-4o-mini" 
client = OpenAI()

# Initialize modules
model_dir = os.getenv("DISTILBERT_MODEL_DIR", "workspace/models/distilbert_model")
kb_dir = os.getenv("KNOWLEDGE_BASE_DIR", "workspace/data/knowledge_base")
confidence_floor = float(os.getenv("DOMAIN_CONFIDENCE_FLOOR", "0.45"))

classifier = DistilBertClassifier(model_dir=model_dir, min_confidence=confidence_floor)
retriever = FAISSRetriever(knowledge_base_dir=kb_dir)

system_prompt = """You are a domain-specific educational AI agent. You are helpful, structured, and concise.
You have access to tools that query tabular CSV data, search a FAISS vector database (knowledge base) containing educational material, read files (including PDFs), or store memories.
Supported domains are: AI, ML, DL, NLP, RL, CV.

CRITICAL INSTRUCTION: You MUST always call the `search_knowledge_base` tool to retrieve facts before answering any domain-specific educational questions in AI, ML, DL, NLP, RL, or CV. Do not rely on your own pre-trained knowledge to answer directly; always search the database first to ensure groundedness and accuracy.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_csv",
            "description": "Query the Titanic CSV file using natural language. The tool converts your question into SQL, executes it, and returns only the relevant records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A natural language question about the Titanic passenger data. Example: 'Find all female passengers who survived in first class'"
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
    {"type": "function",
        "function": {
            "name": "save_to_long_term_memory",
            "description": "Save important information to long-term memory that should be remembered across conversations",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The information to save to long-term memory"
                    }
                },
                "required": ["content"]
            }
        }
     },
     {
         "type": "function",
         "function": {
             "name": "threshold_compress",
             "description": "Compress conversation history when token usage exceeds a certain threshold. This helps to keep the conversation within token limits while retaining important context.",
             "parameters": {
                 "type": "object",
                 "properties": {},
                 "required": []     
                }
             }
     }
]

messages = [
    {"role": "system", "content": system_prompt},   
]

skill_registry = SkillRegistry(skills_dir=Path("skills"))
messages.append({"role": "system", "content": skill_registry.get_menu()})
memory_manager = MemoryManager(memory_dir="memory")

 # Long-term memory
long_term = memory_manager.read_long_term()
if long_term:
    messages.append({"role": "system", "content": f"[Long-Term Memory]\n{long_term}"})



def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return the result"""
    
    # Route to appropriate handler
    try:
        if tool_name == "query_csv":
            query = tool_input.get("query", "")
            result = QueryContext(query).query_csv()
            return result
            
        elif tool_name == "search_knowledge_base":
            query = tool_input.get("query", "")
            domain = tool_input.get("domain", "")
            matches = retriever.retrieve(query, domain, top_k=4)
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
            memory_manager.write_long_term(content)
            return "Information saved to long-term memory"
        
        elif tool_name == "threshold_compress":
            return "Compression completed"
        
        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"
        
    
                                                  
        
            

def chat(user_input: str) -> str:
    """Process user input and return AI response with tool calling support"""
    
    # Step 1: Classify Domain
    domain, confidence, classifier_backend = classifier.classify(user_input)
    
    # Scoping validation
    if domain not in SUPPORTED_DOMAINS or confidence < confidence_floor:
        rejection_text = (
            f"I only answer questions in AI, ML, DL, NLP, RL, and CV. "
            f"Your query was classified under '{domain}' with confidence {confidence:.2f}. "
            "Please ask an on-topic question."
        )
        # Log conversation
        memory_manager.write_daily_log(
            f"User: {user_input}\nAssistant: [Off-Topic Blocked] {rejection_text}\n"
        )
        return rejection_text
        
    messages.append({"role": "user", "content": user_input})
    
    try:
        messages[:] = threshold_compress(messages, budget=3000, client=client)
        
        # First API call with tools
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            tools=TOOLS,
        )
        
        # Handle tool calls if present
        while response.choices[0].finish_reason == "tool_calls":
            assistant_message = response.choices[0].message
            messages.append({"role": "assistant", "content": assistant_message.content or "", "tool_calls": assistant_message.tool_calls})
            
            # Execute each tool call
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)
                
                print(f"\n[DEBUG] LLM triggered Tool Call: {tool_name}")
                print(f"[DEBUG] Parameters: {json.dumps(tool_input, indent=2)}")
                
                tool_result = execute_tool(tool_name, tool_input)
                
                print(f"[DEBUG] Tool Result/Chunks:")
                print(tool_result)
                print("-" * 50 + "\n")
                
                # Add tool result to messages with tool_call_id
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
            
            # Continue conversation
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                tools=TOOLS,
            )
        
        # Get final reply
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        
        # Log conversation
        memory_manager.write_daily_log(
            f"User: {user_input}\nAssistant: {reply[:200]}...\n Routed Domain: {domain} (Conf: {confidence:.2f}, Backend: {classifier_backend})\n Messages: {str(messages)} "
        )
        
        return reply
    
    except Exception as e:
        raise
 
if __name__ == "__main__":
    print("🤖 Domain-Specific Educational AI Agent")
    print("Type 'exit' or 'quit' to stop.\n")


    print("Type 'stats' to see token usage.\n")
    

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye 👋")
            break
        
         # Show token statistics
        if user_input.lower() == "stats":
            report = get_token_usage_report(messages)
            print(f"\n Token Usage Report:")
            print(f"  Total: {report['total']} tokens")
            print(f"  System: {report['system']} | User: {report['user']} | Assistant: {report['assistant']} | Tool: {report['tool']}")
            print(f"  Messages: {report['message_count']}\n")
            continue
        



        try:
            answer = chat(user_input)
            print("\nAgent:\n")
            print(answer)
            print("\n" + "-" * 50 + "\n")
            
            if len(messages) > 20:
                print("[Auto-compressing: conversation over 20 messages...]")
                messages[:] = threshold_compress(messages, budget=120_000, client=client)

        except Exception as e:
            print(f"Error: {e}")
    



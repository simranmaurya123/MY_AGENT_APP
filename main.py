import sys
import io

# Fix Windows encoding for Unicode characters
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from token_utils import threshold_compress, count_all_tokens, get_token_usage_report
from memory import MemoryManager
from query import QueryContext
import subprocess
from pathlib import Path
from skill_registry import SkillRegistry
from docker_sandbox import DockerSandbox







model = "gpt-4o-mini" 
client = OpenAI()

# ============ SANDBOX SECURITY CONFIG ============
SAFE_DIRECTORIES = [
    "data",          # Safe data directory
    "skills",        # Skill documentation
    "memory/Memory.md",  # Only long-term memory summary
]

BLOCKED_PATTERNS = [
    ".env",          # Environment variables
    ".git",          # Git repository
    "venv",          # Virtual environment
    ".env.local",
    "credentials",
    "secret",
    "password",
    "key.pem",
]

# Initialize sandbox (will auto-build Docker image on first use)
sandbox = DockerSandbox(
    image="agent-sandbox:latest",
    workspace=os.getcwd() + "/workspace",  # Use current project directory
    timeout=10,
    memory_limit="256m",
    network=False  # No internet access
)

def is_safe_path(file_path: str) -> bool:
    """Check if a file path is safe to read"""
    path = Path(file_path).resolve()
    
    # Check if in safe directory
    safe = any(Path(safe_dir).resolve() in path.parents or Path(safe_dir).resolve() == path 
               for safe_dir in SAFE_DIRECTORIES)
    
    if not safe:
        return False
    
    # Check for blocked patterns
    path_str = str(path).lower()
    for blocked in BLOCKED_PATTERNS:
        if blocked.lower() in path_str:
            return False
    
    return True

system_prompt = """You are a helpful assistant that provides inventory management information
and answers questions based on the data available. 
You can also call tools to query CSV data, manage PDFs, and interact with git repositories.
Always provide clear and concise answers to the user's questions.

SECURITY NOTE: You operate in a sandboxed environment for safety. 
You can only access whitelisted directories and cannot access sensitive files like .env.
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

    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file given its path. Useful for accessing data or documents relevant to inventory management.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to read. Example: 'data/inventory.csv'"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search files by name in a directory using a pattern (wildcard or partial match)",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "The directory to search in. Example: 'skills' or 'data'"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "The filename pattern to search for. Use wildcards like '*.py' or partial matches like 'test'"
                    }
                },
                "required": ["directory", "pattern"]
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
    
        elif tool_name == "read_file":
            path = tool_input.get("path", "")
            
            # Debug: show what we're checking
            print(f"[DEBUG] Attempting to read: {path}")
            print(f"[DEBUG] File exists: {os.path.exists(path)}")
            print(f"[DEBUG] Is safe path: {is_safe_path(path)}")
            
            # Security check: verify path is safe
            if not is_safe_path(path):
                return f" Access denied: Cannot read '{path}' (not in whitelisted directories or blocked pattern)"
            
            # Verify file exists locally first
            if not os.path.exists(path):
                return "File not found"
            
            # For small, safe files, read directly
            # For potentially large files, use sandbox
            try:
                file_size = os.path.getsize(path)
                print(f"[DEBUG] File size: {file_size} bytes")
                
                if file_size < 100:  # Small files: direct read
                    print(f"[DEBUG] Reading directly (size < 100 bytes)")
                    with open(path, "r", encoding="utf-8") as f:
                        return f.read()
                else:  # Large files: read in sandbox for isolation
                    print(f"[DEBUG] Using SANDBOX to read file...")
                    print(f"[SANDBOX] Running: cat /input/{path}")
                    sandbox_result = sandbox.execute(f"cat /input/{path}")
                    print(f"[SANDBOX] Exit code: {sandbox_result['exit_code']}")
                    print(f"[SANDBOX] Output length: {len(sandbox_result['stdout'])} chars")
                    if sandbox_result["exit_code"] == 0:
                        return sandbox_result["stdout"]
                    else:
                        return f"Error reading file: {sandbox_result['stderr']}"
            except Exception as e:
                return f"Error reading file: {str(e)}"
        
        elif tool_name == "save_to_long_term_memory":
            content = tool_input.get("content", "")
            memory_manager.write_long_term(content)
            return "Information saved to long-term memory"
        
        elif tool_name == "search_files":
            directory = tool_input.get("directory", "")
            pattern = tool_input.get("pattern", "")
            
            # Security check: only allow safe directories
            if not is_safe_path(directory):
                return f" Access denied: Cannot search '{directory}' (not in whitelisted directories)"
            
            if not os.path.exists(directory):
                return f"Directory not found: {directory}"
            
            import glob
            matches = glob.glob(os.path.join(directory, f"**/{pattern}"), recursive=True)
            
            # Filter results to only include safe paths
            safe_matches = [m for m in matches if is_safe_path(m)]
            
            if safe_matches:
                return f"Found {len(safe_matches)} file(s):\n" + "\n".join(safe_matches)
            else:
                return f"No files found matching pattern '{pattern}' in '{directory}'"
        
        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"
        
    
                                                  
        
            

def chat(user_input: str) -> str:
    """Process user input and return AI response with tool calling support"""
    
    
    
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
                tool_result = execute_tool(tool_name, tool_input)
                
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
        try:
            memory_manager.write_daily_log(
                f"User: {user_input}\nAssistant: {reply[:200]}...\n Messages: {str(messages)} "
            )
        except Exception as log_error:
            pass  # Silently ignore logging errors
        
        return reply
    
    except Exception as e:
        raise
 
if __name__ == "__main__":
    print("🤖 Inventory Management Assistant")
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
            # Handle Unicode characters safely
            print(answer.encode('utf-8', errors='replace').decode('utf-8'))
            print("\n" + "-" * 50 + "\n")
            
            if len(messages) > 20:
                print("[Auto-compressing: conversation over 20 messages...]")
                messages[:] = threshold_compress(messages, budget=120_000, client=client)
        
        except Exception as e:
            print(f"Error: {e}")
    



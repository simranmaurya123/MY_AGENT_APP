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
from guardrails import GuardrailsManager







model = "gpt-4o-mini" 
client = OpenAI()

# ============ SANDBOX SECURITY CONFIG ============
SAFE_DIRECTORIES = [
   "workspace" 
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
    timeout=50,
    memory_limit="256m",
    network=False  # No internet access
)

def resolve_file_path(file_path: str) -> str:
    """
    Resolve a file path to its actual location.
    For relative paths (bare filenames or relative paths), search in workspace.
    For absolute paths, use as-is.
    
    Returns: actual file path to use, or None if not found
    """
    p = Path(file_path)
    
    # If absolute, use as-is
    if p.is_absolute():
        return file_path if os.path.exists(file_path) else None
    
    # For relative paths, try multiple locations:
    # 1. workspace/data/{filename} (if it's a bare filename like "myfile.pdf")
    # 2. workspace/{full_path} (if it's a relative path like "data/myfile.pdf")
    # 3. Just relative to CWD
    
    candidates = []
    
    # If no slashes, try workspace/data first
    if "/" not in file_path and "\\" not in file_path:
        candidates.append(os.path.join("workspace", "data", file_path))
    
    # Always try workspace/{path}
    candidates.append(os.path.join("workspace", file_path))
    
    # Try as-is (relative to CWD)
    candidates.append(file_path)
    
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    
    return None  # File not found in any location


def is_safe_path(file_path: str) -> bool:
    """Check if a file path is safe to read"""
    # Resolve the provided path. If it's relative, resolve it against CWD.
    p = Path(file_path)
    if not p.is_absolute():
        path = (Path.cwd() / p).resolve()
    else:
        path = p.resolve()

    # Check if in safe directory
    safe = False
    for safe_dir in SAFE_DIRECTORIES:
        safe_dir_path = Path(safe_dir).resolve()
        try:
            # Check if file is within safe directory
            path.relative_to(safe_dir_path)
            safe = True
            break
        except ValueError:
            # path is not relative to safe_dir_path, continue checking
            continue

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
                        "description": "The directory to search in. Example: 'workspace'"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "The filename pattern to search for. Use wildcards like '*.py' or partial matches like 'test'"
                    }
                },
                "required": ["directory", "pattern"]
            }
        }
    },
    {
  "type": "function",
  "function": {
    "name": "run_python",
    "description": "Execute Python code in a Docker sandbox.\n\nIMPORTANT:\n- Files in /input/data are available inside Docker at /input/data\n- The script is available at /input/temp_script.py\n- Output files MUST be written to /output\n- Always print the final output file path after creating it\n\nExample:\nprint('CREATED: /output/result.pdf')",
    "parameters": {
      "type": "object",
      "properties": {
        "code": {
          "type": "string",
          "description": "The full Python code to execute. For example, code to merge PDFs or create charts. Ensure the code is complete and syntactically correct."
        }
      },
      "required": ["code"]
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
    
guardrails_manager = GuardrailsManager(memory_manager=memory_manager)
print("[GUARDRAILS] System initialized with comprehensive guardrails")


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return the result"""
    
    
    # Route to appropriate handler
    try:
        if tool_name == "query_csv":
            query = tool_input.get("query", "")
            result = QueryContext(query).query_csv()
            return result
    
        elif tool_name == "read_file":
            original_path = tool_input.get("path", "")
            
            # Resolve the actual file path (searches workspace directories)
            resolved_path = resolve_file_path(original_path)
            
            # Debug: show what we're checking
            print(f"[DEBUG] Attempting to read: {original_path}")
            print(f"[DEBUG] Resolved to: {resolved_path}")
            print(f"[DEBUG] File exists: {resolved_path is not None}")
            
            if resolved_path is None:
                return f"File not found: '{original_path}' not found in any workspace location"
            
            print(f"[DEBUG] Is safe path: {is_safe_path(resolved_path)}")
            
            # Security check: verify path is safe
            if not is_safe_path(resolved_path):
                return f" Access denied: Cannot read '{resolved_path}' (not in whitelisted directories or blocked pattern)"
            
            # Check if it's a PDF file
            if resolved_path.lower().endswith('.pdf'):
                print(f"[DEBUG] Reading PDF directly with pdfplumber...")
                try:
                    import pdfplumber
                    text = []
                    with pdfplumber.open(resolved_path) as pdf:
                        text.append(f"Successfully extracted from PDF ({len(pdf.pages)} pages total)")
                        text.append("=" * 60)
                        for i, page in enumerate(pdf.pages):
                            page_text = page.extract_text()
                            if page_text:
                                text.append(f"\n[Page {i+1}]")
                                text.append("-" * 60)
                                text.append(page_text)
                    
                    full_text = "\n".join(text)
                    # Truncate if extremely large to save tokens
                    if len(full_text) > 15000:
                        return full_text[:15000] + "\n... [Content Truncated due to size limits]"
                    return full_text
                except Exception as e:
                    return f"Error reading PDF: {str(e)}"
            
            # For small, safe files, read directly
            # For potentially large files, use sandbox
            try:
                file_size = os.path.getsize(resolved_path)
                print(f"[DEBUG] File size: {file_size} bytes")
                
                if file_size < 100:  # Small files: direct read
                    print(f"[DEBUG] Reading directly (size < 100 bytes)")
                    with open(resolved_path, "r", encoding="utf-8") as f:
                        return f.read()
                else:  # Large files: read in sandbox for isolation
                    print(f"[DEBUG] Using SANDBOX to read file...")
                    # Convert backslashes to forward slashes for Docker paths
                    sandbox_path = resolved_path.replace("\\", "/")
                    sandbox_cmd = f"cat /input/{sandbox_path}"
                    print(f"[SANDBOX] Running: {sandbox_cmd}")
                    sandbox_result = sandbox.execute(sandbox_cmd)
                    print(f"[SANDBOX] Exit code: {sandbox_result['exit_code']}")
                    print(f"[SANDBOX] Output length: {len(sandbox_result['stdout'])} chars")
                    if sandbox_result["exit_code"] == 0:
                        return sandbox_result["stdout"]
                    else:
                        return f"Error reading file in sandbox: {sandbox_result['stderr']}"
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
            
            
            
            
            
        
        elif tool_name == "run_python":
            code = tool_input.get("code", "")

            if not code:
                return "No code provided to execute."

            script_path = os.path.join("workspace", "temp_script.py")
            output_dir = os.path.join("workspace", "output")
            os.makedirs(output_dir, exist_ok=True)

            print("Writing script to:", script_path)

            try:
                

                # Write script to disk
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(code)

                # Execute in Docker with a separate writable output mount
                sandbox_result = sandbox.execute_with_output(
                    script_path=script_path,
                    output_dir=output_dir,
                )

                
                output = f"Exit code: {sandbox_result['exit_code']}\n"

                if sandbox_result["stdout"]:
                    output += f"Output:\n{sandbox_result['stdout']}\n"

                if sandbox_result["stderr"]:
                    output += f"Errors:\n{sandbox_result['stderr']}\n"

                # Report which files were saved to disk
                saved = os.listdir(output_dir)
                if saved:
                    output += f"\nFiles saved to workspace/output/: {saved}"

                return output

            except Exception as e:
                return f"Error executing Python code: {str(e)}"

            finally:
                if os.path.exists(script_path):
                    os.remove(script_path)

   
    except Exception as e:
        return f"Error executing tool {tool_name}: {str(e)}"

def chat(user_input: str) -> str:
    """Process user input and return AI response with tool calling support"""
    
    # GUARDRAIL: Validate input before sending to API
    is_valid, validation_msg = guardrails_manager.validate_input(user_input)
    if not is_valid:
        print(f"[GUARDRAILS BLOCKED] {validation_msg}")
        return validation_msg
    
    # Add user input to message history after validation passes
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
        
        
        # GUARDRAIL: Validate output
        is_valid,validation_msg,metadata= guardrails_manager.validate_output(reply)
        if not is_valid:
            print(f"[GUARDRAILS BLOCKED] {validation_msg}")
           # Note: We still return the response but flag it as potentially problematic
            # You can modify this to reject the response entirely if needed
        
        # GUARDRAIL: Track resource usage (estimate based on response size)
        # Note: For accurate token count, you'd need to use tiktoken library
        estimated_input_tokens = len(user_input)//4
        estimated_output_tokens = len(reply)//4
        estimated_cost = (estimated_input_tokens * 0.00015 + estimated_output_tokens * 0.0006) / 1000
         
         
        resource_ok,resource_msg  = guardrails_manager.track_resource_usage(
            estimated_input_tokens, estimated_output_tokens, estimated_cost )
        
        if not resource_ok:
            print(f"[GUARDRAILS BLOCKED] {resource_msg}")
            return resource_msg
        
        
        
        
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
        print(f"[DEBUG] Error in chat function: {e}")
        guardrails_manager.audit_guard.log_event(
            "error",
            f"Exception in chat:{str(e)}",
            "critical"
        )
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
    

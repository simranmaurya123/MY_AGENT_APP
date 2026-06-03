# AI Agent Guide: Inventory Management Chatbot

## Project Overview
This is a Python-based AI agent that provides inventory management information and answers questions via OpenAI's GPT-4o-mini model with tool-calling capabilities.

## Quick Setup
- **Environment**: Python 3
- **Key Dependencies**: `openai`, `python-dotenv` (see [requirements.txt](requirements.txt))
- **Config**: Requires `.env` file with `OPENAI_API_KEY`
- **Run**: `python main.py` (currently no interactive CLI entry point - needs implementation)

## Architecture & Key Files

### [main.py](main.py)
- **Entry point** for the agent application
- **Core function**: `chat(user_input: str) -> str` — processes user queries through OpenAI with tool calling
- **Tool system**: Extensible framework with `execute_tool()` function (currently supports `read_file` tool)
- **Message loop**: Handles multi-turn conversations with tool call execution and retry logic

### Tool Calling Pattern
1. Send request to OpenAI with `tools=TOOLS` parameter
2. If response has `finish_reason == "tool_calls"`, execute each tool via `execute_tool()`
3. Append tool results as `"role": "tool"` messages
4. Continue conversation with refined context

## Common Development Tasks

### Adding a New Tool
1. Define tool in `TOOLS` list with schema matching OpenAI's function calling format
2. Add corresponding handler in `execute_tool()` function
3. Test tool call flow with `chat()` function

### Running Conversations
- Current code has `chat()` function but no CLI loop
- To test: Create a simple entry point or modify `chat()` to accept interactive input
- Debug output available via `[DEBUG]` print statements

## Notes & Conventions
- Model is hardcoded to `gpt-4o-mini` — update if using different model
- Empty `TOOLS` list means tool calling is configured but inactive
- System prompt focuses on inventory management (customize as needed)
- Uses `temperature=0.3` for consistent, deterministic responses

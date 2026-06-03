# Inventory Management AI Agent

A Python-based chatbot powered by OpenAI's GPT-4o-mini model that provides inventory management information and answers questions using tool-calling capabilities.

## Getting Started

### Prerequisites
- Python 3
- OpenAI API key

### Installation
1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```bash
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt)**:
     ```bash
     venv\Scripts\activate.bat
     ```
   - **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Create a `.env` file in the project root with:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

### Running the Agent
```bash
python main.py
```

## Project Structure
- **main.py** — Core agent logic with OpenAI integration and tool-calling system
- **requirements.txt** — Python dependencies
- **AGENTS.md** — AI agent guidance and conventions (see this for development details)

## Development
See [AGENTS.md](AGENTS.md) for information on the architecture, tool-calling pattern, and common development tasks.

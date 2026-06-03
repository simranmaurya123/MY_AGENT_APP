# Sandbox Integration Guide

## ✅ What Changed

Your agent is now **sandboxed** to prevent access to sensitive files like `.env`. Here's what's been implemented:

### Security Features Added

1. **Whitelist System** - Only specific directories can be accessed:
   - `data/` - Safe data files
   - `skills/` - Skill documentation
   - `memory/Memory.md` - Long-term memory only

2. **Blocklist** - Blocked patterns (agent cannot access these):
   - `.env`, `.env.local` - Environment files
   - `venv/` - Virtual environment
   - `.git/` - Git repository
   - Any file containing: `secret`, `password`, `credentials`, `key.pem`

3. **Docker Isolation** - File operations run in a restricted container with:
   - No network access
   - Non-root user (security level)
   - 256MB memory limit
   - Read-only filesystem (only `/tmp` and `/workspace` writable)
   - No dangerous capabilities (fork bomb protection)

---

## 🚀 Setup Steps

### Step 1: Build the Docker Sandbox Image

Run this command **once** to build the sandbox image:

```bash
docker build -f Dockerfile.sandbox -t agent-sandbox:latest .
```

**What this does:**
- Creates a minimal Python 3.12 container
- Installs only safe tools: `ruff`, `pytest`, `httpx`
- Runs as non-root user `agent` (hardened security)

### Step 2: Test the Integration

Run your agent and try to read a file:

```bash
python main.py
```

Then ask the agent to read different files:

```
✅ WORKS:      "Read the skills directory"
✅ WORKS:      "Show me data/inventory.csv"
❌ BLOCKED:    "Read my .env file"
❌ BLOCKED:    "Show venv/lib/python3.11/site-packages"
```

---

## 🔧 Customization

### Add Safe Directories

Edit `main.py` in the `SAFE_DIRECTORIES` list:

```python
SAFE_DIRECTORIES = [
    "data",              # Add your safe dirs here
    "skills",
    "memory/Memory.md",
    "documents/public",  # Example: add this
]
```

### Add Blocked Patterns

Add patterns you want to block:

```python
BLOCKED_PATTERNS = [
    ".env",
    ".git",
    "venv",
    "api_keys",  # Block any file with "api_keys" in the name
    "private",
]
```

### Adjust Sandbox Limits

```python
sandbox = DockerSandbox(
    image="agent-sandbox:latest",
    timeout=10,              # Max 10 seconds per command
    memory_limit="256m",     # Max 256MB RAM
    network=False            # No internet access
)
```

---

## 📋 How It Works

```
User Question
    ↓
Agent wants to read_file("/data/sales.csv")
    ↓
is_safe_path() checks:
  ✓ Is it in SAFE_DIRECTORIES? → YES ("/data" is allowed)
  ✓ Contains blocked pattern? → NO (no .env, .git, etc.)
    ↓
✅ File is read directly (< 100KB) or via sandbox (> 100KB)
```

```
User Question: "Read .env"
    ↓
Agent wants to read_file(".env")
    ↓
is_safe_path() checks:
  ✓ Is it in SAFE_DIRECTORIES? → NO
  ✓ Contains blocked pattern? → YES (".env" is blocked)
    ↓
❌ ACCESS DENIED
```

---

## ⚠️ Important Notes

1. **Docker Required** - You must have Docker installed and running
   - Check: `docker --version`
   - On Windows, use Docker Desktop

2. **First Run Latency** - Sandbox commands take ~1-2s longer (Docker overhead)
   - Small files (< 100KB) bypass sandbox for speed
   - Large files use sandbox for isolation

3. **Network Disabled** - Agent cannot download files or reach the internet
   - This is intentional (security)
   - If you need network, set `network=True` (⚠️ reduces security)

4. **Non-Root Execution** - Agent runs as user `1000:1000`, not root
   - Prevents system-level damage
   - Cannot execute arbitrary system commands

---

## 🐛 Troubleshooting

### "docker: command not found"
Install Docker Desktop from https://www.docker.com/products/docker-desktop

### "Cannot find image agent-sandbox:latest"
Build it first:
```bash
docker build -f Dockerfile.sandbox -t agent-sandbox:latest .
```

### Agent can't read a file I want accessible
1. Check the file is in `SAFE_DIRECTORIES`
2. Check it doesn't contain blocked patterns
3. Update `SAFE_DIRECTORIES` to include the parent folder

### Performance is slow
- Small files are read directly (not sandboxed)
- Only large files use sandbox overhead
- Adjust `timeout` if commands are taking too long

---

## 📊 Security Summary

| Feature | Status | What It Does |
|---------|--------|-------------|
| Whitelist | ✅ Enabled | Only safe directories |
| Blocklist | ✅ Enabled | Blocks sensitive files |
| Docker Isolation | ✅ Enabled | Restricted container |
| Network | ✅ Disabled | No internet access |
| Root Access | ✅ Disabled | Non-root user only |
| Fork Bomb Protection | ✅ Enabled | Max 100 processes |
| Memory Limit | ✅ Enabled | Max 256MB |
| CPU Limit | ✅ Enabled | Max 1 CPU core |

Your agent is now **significantly more secure**! 🛡️

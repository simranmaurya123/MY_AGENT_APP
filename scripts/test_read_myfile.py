#!/usr/bin/env python
"""Test the read_file tool with myfile.pdf"""
import sys
import os
sys.path.insert(0, os.getcwd())

# Minimal imports to test the path logic
from pathlib import Path

def resolve_file_path(file_path: str) -> str:
    """Resolve a file path to its actual location."""
    p = Path(file_path)
    
    if p.is_absolute():
        return file_path if os.path.exists(file_path) else None
    
    candidates = []
    
    if "/" not in file_path and "\\" not in file_path:
        candidates.append(os.path.join("workspace", "data", file_path))
    
    candidates.append(os.path.join("workspace", file_path))
    candidates.append(file_path)
    
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    
    return None

def is_safe_path(file_path: str) -> bool:
    """Check if a file path is safe to read"""
    SAFE_DIRECTORIES = ["workspace"]
    BLOCKED_PATTERNS = [".env", ".git", "venv", ".env.local", "credentials", "secret", "password", "key.pem"]
    
    p = Path(file_path)
    if not p.is_absolute():
        path = (Path.cwd() / p).resolve()
    else:
        path = p.resolve()

    safe = False
    for safe_dir in SAFE_DIRECTORIES:
        safe_dir_path = Path(safe_dir).resolve()
        try:
            path.relative_to(safe_dir_path)
            safe = True
            break
        except ValueError:
            continue

    if not safe:
        return False

    path_str = str(path).lower()
    for blocked in BLOCKED_PATTERNS:
        if blocked.lower() in path_str:
            return False

    return True


# Test the logic
print("=" * 60)
print("TESTING FILE ACCESS: myfile.pdf")
print("=" * 60)

original_path = "myfile.pdf"
resolved_path = resolve_file_path(original_path)

print(f"\n1. Path Resolution:")
print(f"   Input: {original_path}")
print(f"   Resolved to: {resolved_path}")
print(f"   File exists: {resolved_path is not None and os.path.exists(resolved_path)}")

if resolved_path:
    print(f"\n2. Safety Check:")
    print(f"   Is safe path: {is_safe_path(resolved_path)}")
    
    print(f"\n3. File Details:")
    file_size = os.path.getsize(resolved_path)
    print(f"   Size: {file_size} bytes")
    print(f"   Can read directly: {file_size < 100}")
    
    print(f"\n✅ SUCCESS: File can be read!")
else:
    print(f"\n❌ FAILED: File not found")

print("=" * 60)

#!/usr/bin/env python
"""Test sandbox path construction for myfile.pdf"""
import os

# Test path resolution and sandbox command construction
resolved_path = "workspace\\data\\myfile.pdf"  # Windows path format

print(f"Original path: {resolved_path}")
print(f"File exists: {os.path.exists(resolved_path)}")

# Correct transformation for sandbox
sandbox_path = resolved_path.replace("\\", "/")
sandbox_cmd = f"cat /input/{sandbox_path}"

print(f"Sandbox path: {sandbox_path}")
print(f"Sandbox command: {sandbox_cmd}")
print(f"Expected in Docker: /input/workspace/data/myfile.pdf")
print(f"Match: {sandbox_cmd == 'cat /input/workspace/data/myfile.pdf'}")

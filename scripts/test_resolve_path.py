import os
from pathlib import Path

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


if __name__ == '__main__':
    print("Test 1 - bare filename 'myfile.pdf':")
    result = resolve_file_path('myfile.pdf')
    print(f"  Result: {result}")
    print(f"  Exists: {os.path.exists(result) if result else False}")
    
    print("\nTest 2 - relative path 'workspace/data/myfile.pdf':")
    result = resolve_file_path('workspace/data/myfile.pdf')
    print(f"  Result: {result}")
    print(f"  Exists: {os.path.exists(result) if result else False}")
    
    print("\nTest 3 - absolute path:")
    abs_path = r"D:\MY_AGENT_APP\workspace\data\myfile.pdf"
    result = resolve_file_path(abs_path)
    print(f"  Result: {result}")
    print(f"  Exists: {os.path.exists(result) if result else False}")

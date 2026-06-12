import os
from pathlib import Path

SAFE_DIRECTORIES = ["workspace"]
BLOCKED_PATTERNS = [
    ".env",
    ".git",
    "venv",
    ".env.local",
    "credentials",
    "secret",
    "password",
    "key.pem",
]


def is_safe_path(file_path: str) -> bool:
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


if __name__ == '__main__':
    test_path = r"D:\MY_AGENT_APP\workspace\data\myfile.pdf"
    print("Testing path:", test_path)
    print("os.path.exists:", os.path.exists(test_path))
    print("is_safe_path:", is_safe_path(test_path))
    
    # Also test the relative form commonly used by the app
    rel_path = "workspace/data/myfile.pdf"
    print("\nTesting relative path:", rel_path)
    print("os.path.exists:", os.path.exists(rel_path))
    print("is_safe_path:", is_safe_path(rel_path))

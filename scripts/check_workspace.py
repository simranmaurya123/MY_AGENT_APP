from pathlib import Path
ws = Path(r"D:\MY_AGENT_APP")  # <- replace with your workspace path
print("exists:", ws.exists())
print("resolved:", ws.resolve())
print("contains myfile.pdf:", (ws / "myfile.pdf").exists())
print("sample entries:", [p.name for p in ws.iterdir()][:20])
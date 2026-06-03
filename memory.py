import os
from datetime import datetime, timedelta

class MemoryManager:
    def __init__(self,memory_dir:str):
        self.memory_dir = memory_dir
        self.daily_dir = os.path.join(memory_dir, "daily logs")
        os.makedirs(self.daily_dir, exist_ok=True)
        
        
    def read_long_term(self)->str:
        path=os.path.join(self.memory_dir,"Memory.md")   
        if os.path.exists(path):
            return open(path, "r").read()
        return ""
    
    def write_long_term(self,content:str,append:bool=True):
        """Save to long-term memory (Memory.md)"""
        
        path=os.path.join(self.memory_dir,"Memory.md")   
        mode = "a" if append else "w"
        with open(path, mode) as f:
            if append:
                f.write(f"\n{content}")
            else:
                f.write(content)
                
    def read_recent_logs(self,days:int=4)->str:
        logs=[]
        for i in range(days):
            date=(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            path=os.path.join(self.daily_dir,f"{date}.md")
            if os.path.exists(path):
                logs.append(open(path, "r").read())
                
            return "\n---\n".join(logs)  
        
    def write_daily_log(self,content:str):
        date=datetime.now().strftime("%Y-%m-%d")
        path=os.path.join(self.daily_dir,f"{date}.md")
        with open(path, "a") as f:
            f.write(f"\n## {datetime.now().strftime('%H:%M:%S')}\n")    
            f.write(content + "\n")     
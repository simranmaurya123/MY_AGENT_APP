import json
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class Skill:
    name: str
    description: str
    license: str
    schemas: list = field(default_factory=list)
    
    
    
class SkillRegistry:
    """Registry with on demand skill loading"""    
    
    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir)
        self._catalog: dict[str, Skill] = {}
        self._active: dict[str, Skill] = {}
        self._scan()
        
        
    def _scan(self):
        """scan the skills directory and build the catalog"""
        
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                skill_md = skill_dir / "skill.md"
            schema_file = skill_dir / "schema.json"
            if not skill_md.exists():
                continue
            
            doc = skill_md.read_text(encoding='utf-8')
            
            first_heading = ""
            for line in doc.splitlines():
                if line.startswith("# "):
                    first_heading = line[3:].strip()
                    break
            
            
               
               
            self._catalog[skill_dir.name]  = Skill(
                name=skill_dir.name,
                description=first_heading,
                license="MIT",
            ) 
            
    def get_menu(self) -> str:
        """Generate the skill menu for the model."""
        lines = ["Available skills (use load_skill to activate):\n"]
        for name, skill in self._catalog.items():
            status = "[loaded]" if name in self._active else "[inactive]"
            lines.append(f"{name} - {skill.description} [{status}]")
        return "\n".join(lines)
    
    
    
    def load_skill(self, name: str) -> str:
        """load a skill, making its tools available"""
        
        if name not in self._catalog:
            return f"Error: Unknown skill '{name}'. Check the skill menu."
        
        if name in self._active:
            return f"Skill '{name}' is already loaded."
        
        
        skill = self._catalog[name]
        self._active[name] = skill
        
        
        return f"Loaded skill '{name}'"
            
    def unload_skill(self, name: str) -> str:
        """unload a skill to free up context space"""
        
        if name not in self._active:
            return f"Skill '{name}' is not loaded."  
        
        del self._active[name]
        return f"Unloaded skill '{name}'"


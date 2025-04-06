"""
Utility functions for roadmap generation and formatting.
"""

import re
from typing import Dict, List, Tuple, TypedDict

class RoadmapItem(TypedDict):
    action: str
    responsible: str
    rationale: str

RoadmapSection = List[RoadmapItem]
RoadmapStructure = Dict[str, RoadmapSection]

def format_roadmap_steps(roadmap_text: str) -> RoadmapStructure:
    """
    Parse and structure the raw roadmap text into organized steps.
    Returns:
        {
            "immediate": [
                {"action": "...", "responsible": "...", "rationale": "..."},
                ...
            ],
            "short_term": [...],
            "medium_term": [...]
        }
    """
    sections: RoadmapStructure = {
        "immediate": [],
        "short_term": [], 
        "medium_term": []
    }
    
    current_section = None
    for line in roadmap_text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Detect section headers
        if line.startswith('1.'):
            current_section = "immediate"
            continue
        elif line.startswith('2.'):
            current_section = "short_term"
            continue
        elif line.startswith('3.'):
            current_section = "medium_term"
            continue
            
        # Parse action items
        if current_section and line:
            action, responsible, rationale = parse_roadmap_line(line)
            if action:
                sections[current_section].append({
                    "action": action,
                    "responsible": responsible,
                    "rationale": rationale
                })
                
    return sections

def parse_roadmap_line(line: str) -> Tuple[str, str, str]:
    """
    Parse a single roadmap line into components.
    Returns: (action, responsible, rationale)
    """
    # Extract responsible party (in parentheses)
    responsible_match = re.search(r'\((.*?)\)', line)
    responsible = responsible_match.group(1) if responsible_match else "Security Team"
    
    # Extract rationale (after dash)
    rationale = ""
    dash_pos = line.find('-')
    if dash_pos > 0:
        rationale = line[dash_pos+1:].strip()
        line = line[:dash_pos].strip()
    
    # Clean up action text
    action = re.sub(r'\(.*?\)', '', line).strip()
    
    return action, responsible, rationale

def generate_roadmark_markdown(roadmap_data: RoadmapStructure) -> str:
    """
    Convert structured roadmap data to markdown format.
    """
    markdown = "# Remediation Roadmap\n\n"
    
    for section, items in roadmap_data.items():
        if not items:
            continue
            
        title = {
            "immediate": "Immediate Actions (Next 24-48 hours)",
            "short_term": "Short-term Actions (Next Week)",
            "medium_term": "Medium-term Actions (Next Month)"
        }.get(section, section.replace('_', ' ').title())
        
        markdown += f"## {title}\n\n"
        
        for item in items:
            markdown += f"- **{item['action']}**\n"
            markdown += f"  - *Responsible*: {item['responsible']}\n"
            markdown += f"  - *Rationale*: {item['rationale']}\n\n"
            
    return markdown
# Doc Analyzer Agent

Security analysis component that identifies potential vulnerabilities based on system descriptions.

## Features
- Automated keyword generation from system descriptions
- NVD API integration for vulnerability lookup
- Security weak point identification
- Report generation with actionable recommendations

## Usage

```python
from src.doc_analyzer_agent import DocAnalyzerAgent

agent = DocAnalyzerAgent()
report = agent.process("Your system description here")

# Access report components
print(f"Found {len(report.vulnerabilities)} vulnerabilities")
print("Weak points:", report.weak_points)
```

## Requirements
- Python 3.10+
- AWS Bedrock access for keyword generation
- NVD API key (set in environment variables)
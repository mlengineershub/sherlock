# Remediation Advisory Component

## Overview
This component provides remediation planning capabilities for security vulnerabilities identified by the investigation system. It:
- Takes investigation tree output as input
- Generates multiple perspectives on each vulnerability
- Allows security experts to evaluate and annotate findings
- Produces actionable remediation roadmaps

## Architecture
- `agent.py`: Core logic for remediation planning
- `api.py`: FastAPI endpoints for frontend interaction
- `perspective_generator.py`: Generates expert/attacker/business/compliance views
- `roadmap_generator.py`: Creates prioritized remediation plans

## API Endpoints
- `POST /api/remediation/load`: Load investigation data
- `GET /api/remediation/board`: Get board nodes
- `POST /api/remediation/node/{node_id}/perspectives`: Generate perspectives
- `PUT /api/remediation/node/{node_id}/perspective/{type}`: Update perspective selection
- `PUT /api/remediation/node/{node_id}/input`: Add user notes
- `POST /api/remediation/roadmap`: Generate final roadmap

## Dependencies
- AWS Bedrock for LLM capabilities
- FastAPI for web interface
- Pydantic for data validation
"""
Script to run the FastAPI server for the investigation agent.
"""

import uvicorn
from backend.investigation.src.api import app

if __name__ == "__main__":
    print("Starting Investigation Agent API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
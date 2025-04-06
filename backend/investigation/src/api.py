"""
FastAPI server for the investigation agent.
Provides endpoints for the frontend to interact with the investigation agent.
"""

import logging
import os
from typing import Dict, List, Optional, Any
from pydantic import Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.investigation.src.agent import InvestigationAgent, NodeStatus
from backend.common.src.utils.bedrock_client import BedrockClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FastAPI app
app = FastAPI(title="Investigation Agent API")

# Add CORS middleware to allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the investigation agent
bedrock_client = BedrockClient()
investigation_agent = InvestigationAgent(bedrock_client=bedrock_client)

# Define request and response models
class StartInvestigationRequest(BaseModel):
    breach_info: str
    num_initial_nodes: int = 3

class UpdateNodeStatusRequest(BaseModel):
    status: str

class ExpandNodeRequest(BaseModel):
    num_nodes: int = 3

class NodeDetailsResponse(BaseModel):
    id: str
    title: str
    description: str
    type: str
    status: str
    confidence: float
    evidence: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

@app.post("/api/investigation/start")
async def start_investigation(request: StartInvestigationRequest):
    """Start a new investigation with the provided breach information."""
    try:
        logger.info(f"Starting investigation with breach info: {request.breach_info[:50]}...")
        
        # Create a new investigation
        tree = investigation_agent.create_investigation(
            breach_info=request.breach_info,
            num_initial_nodes=request.num_initial_nodes
        )
        
        # Export the tree for visualization
        tree_data = investigation_agent.export_tree_visualization()
        
        return tree_data
    except Exception as e:
        logger.error(f"Error starting investigation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investigation/tree")
async def get_investigation_tree():
    """Get the current investigation tree."""
    try:
        tree = investigation_agent.get_current_tree()
        if not tree:
            raise HTTPException(status_code=404, detail="No active investigation found")
        
        tree_data = investigation_agent.export_tree_visualization()
        return tree_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting investigation tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/investigation/node/{node_id}/status")
async def update_node_status(node_id: str, request: UpdateNodeStatusRequest):
    """Update the status of a node in the investigation tree."""
    try:
        # Convert string status to NodeStatus enum
        try:
            status = NodeStatus[request.status.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status: {request.status}. Valid values are: {', '.join([s.name.lower() for s in NodeStatus])}"
            )
        
        # Update the node status
        success = investigation_agent.update_node_status(node_id=node_id, status=status)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating node status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/investigation/node/{node_id}/expand")
async def expand_node(node_id: str, request: ExpandNodeRequest):
    """Generate the next level of nodes for a given parent node."""
    try:
        # Generate next level nodes
        new_node_ids = investigation_agent.generate_next_level(
            parent_id=node_id,
            num_nodes=request.num_nodes
        )
        
        if not new_node_ids:
            raise HTTPException(
                status_code=400, 
                detail=f"Could not generate next level for node {node_id}. Check if the node exists and has a valid status."
            )
        
        return {"node_ids": new_node_ids}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error expanding node: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investigation/node/{node_id}/details")
async def get_node_details(node_id: str):
    """Get detailed information about a specific node."""
    try:
        logger.info(f"Getting details for node: {node_id}")
        tree = investigation_agent.get_current_tree()
        if not tree:
            logger.error("No active investigation found")
            raise HTTPException(status_code=404, detail="No active investigation found")
        
        node = tree.get_node(node_id)
        logger.info(f"Node data: {node}")
        if not node:
            logger.error(f"Node {node_id} not found")
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        
        # Convert node dictionary to response model with safe access
        try:
            # Get evidence and ensure it's a list of strings
            evidence_data = node.get("evidence", [])
            # Convert evidence items to strings if they're not already
            evidence_list = []
            for item in evidence_data:
                if isinstance(item, str):
                    evidence_list.append(item)
                elif isinstance(item, dict):
                    # If it's a dictionary, convert it to a string representation
                    evidence_list.append(str(item))
                else:
                    # For any other type, convert to string
                    evidence_list.append(str(item))
            
            response = NodeDetailsResponse(
                id=node_id,
                title=node.get("title", "Unknown Title"),
                description=node.get("description", "No description available"),
                type=node.get("type", "unknown"),
                status=node.get("status", "unverified"),
                confidence=float(node.get("confidence", 0.0)),
                evidence=evidence_list,
                metadata=node.get("metadata", {})
            )
            logger.info(f"Successfully created response for node {node_id}")
            return response
        except Exception as conversion_error:
            logger.error(f"Error converting node data to response: {conversion_error}")
            logger.error(f"Node data structure: {type(node)}, keys: {node.keys() if hasattr(node, 'keys') else 'No keys method'}")
            
            # Log more details about the evidence field
            evidence_data = node.get("evidence", [])
            logger.error(f"Evidence field type: {type(evidence_data)}, value: {evidence_data}")
            if isinstance(evidence_data, list):
                for i, item in enumerate(evidence_data):
                    logger.error(f"Evidence item {i} type: {type(item)}, value: {item}")
            
            raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting node details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/investigation/report")
async def generate_report():
    """Generate a report from the current investigation."""
    try:
        report = investigation_agent.generate_report()
        return report.model_dump()
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
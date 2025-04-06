"""
FastAPI server for the remediation advisory component.
Standalone implementation without shared utilities.
"""

import json
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from backend.remediation.src.agent import RemediationAgent
from backend.common.src.utils.bedrock_client import BedrockClient

# Initialize FastAPI app
app = FastAPI(
    title="Remediation Advisory API",
    description="API for generating security remediation plans"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the remediation agent
bedrock_client = BedrockClient()
remediation_agent = RemediationAgent(bedrock_client=bedrock_client)

# Request models
class LoadInvestigationRequest(BaseModel):
    tree_path: str
    documentation_path: Optional[str] = None

class PerspectiveSelectionRequest(BaseModel):
    selected: bool

class UserInputRequest(BaseModel):
    content: str

# API Endpoints
@app.post("/api/remediation/load")
async def load_investigation(request: LoadInvestigationRequest):
    """Load investigation tree for remediation planning"""
    import logging
    import os
    logger = logging.getLogger(__name__)
    
    logger.info(f"Received request to load investigation from path: {request.tree_path}")
    
    # Validate the tree path
    if not request.tree_path:
        logger.error("Empty tree path provided")
        raise HTTPException(status_code=400, detail="Tree path cannot be empty")
    
    # Resolve the path - handle both absolute and relative paths
    # If it's a relative path, assume it's relative to the project root
    tree_path = request.tree_path
    if not os.path.isabs(tree_path):
        # Get the project root directory (assuming the API is running from the project root)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        tree_path = os.path.join(project_root, tree_path)
        logger.info(f"Resolved relative path to absolute path: {tree_path}")
    
    # Check if file exists
    if not os.path.exists(tree_path):
        logger.error(f"Investigation tree file not found: {tree_path}")
        # Try to list files in the directory to help with debugging
        try:
            dir_path = os.path.dirname(tree_path)
            if os.path.exists(dir_path):
                files = os.listdir(dir_path)
                logger.info(f"Files in directory {dir_path}: {files}")
                
                # Check if the file exists with a different case
                base_name = os.path.basename(tree_path)
                for file in files:
                    if file.lower() == base_name.lower():
                        logger.info(f"Found file with different case: {file}")
                        # Use the correct case
                        correct_path = os.path.join(dir_path, file)
                        logger.info(f"Using correct case path: {correct_path}")
                        tree_path = correct_path
                        break
            else:
                logger.error(f"Directory does not exist: {dir_path}")
                # Try to list the parent directory
                parent_dir = os.path.dirname(dir_path)
                if os.path.exists(parent_dir):
                    logger.info(f"Parent directory exists: {parent_dir}")
                    logger.info(f"Files in parent directory: {os.listdir(parent_dir)}")
        except Exception as e:
            logger.error(f"Error listing directory: {str(e)}")
            
        # Try alternative paths
        alternative_paths = [
            os.path.join(os.path.dirname(__file__), "../../../output/investigation_tree_viz.json"),
            "/home/azzedine/Projects/secai/output/investigation_tree_viz.json",
            "output/investigation_tree_viz.json"
        ]
        
        for alt_path in alternative_paths:
            if os.path.exists(alt_path):
                logger.info(f"Found file at alternative path: {alt_path}")
                tree_path = alt_path
                break
        else:
            logger.error("File not found at any alternative paths")
            
        raise HTTPException(
            status_code=404,
            detail=f"Investigation tree file not found: {tree_path}"
        )
    
    try:
        # Attempt to load the investigation tree
        logger.info(f"Loading investigation tree from: {tree_path}")
        remediation_agent.load_investigation_tree(tree_path)
        node_count = len(remediation_agent.board_nodes)
        logger.info(f"Successfully loaded investigation tree with {node_count} nodes")
        return {"node_count": node_count}
    except FileNotFoundError as e:
        logger.error(f"File not found error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"Value error when loading investigation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON format in file: {request.tree_path}")
    except Exception as e:
        logger.error(f"Unexpected error loading investigation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load investigation data: {str(e)}"
        )

@app.get("/api/remediation/board")
async def get_board_nodes():
    """Get all nodes for the remediation board"""
    if not remediation_agent.board_nodes:
        raise HTTPException(status_code=404, detail="No investigation loaded")
    return remediation_agent.board_nodes

@app.post("/api/remediation/node/{node_id}/perspectives")
async def generate_perspectives(node_id: str):
    """Generate perspectives for a node"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Generating perspectives for node {node_id}")
    
    # Check if node exists
    node = next((n for n in remediation_agent.board_nodes if n["id"] == node_id), None)
    if not node:
        logger.error(f"Node {node_id} not found")
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    
    try:
        logger.info(f"Calling remediation_agent.generate_perspectives for node {node_id}")
        perspectives = remediation_agent.generate_perspectives(node_id)
        
        if not perspectives:
            logger.error(f"No perspectives generated for node {node_id}")
            raise HTTPException(status_code=404, detail=f"Failed to generate perspectives for node {node_id}")
        
        logger.info(f"Successfully generated {len(perspectives)} perspectives for node {node_id}")
        return perspectives
    except Exception as e:
        logger.error(f"Failed to generate perspectives for node {node_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate perspectives: {str(e)}"
        )

@app.put("/api/remediation/node/{node_id}/perspective/{perspective_type}")
async def update_perspective_selection(
    node_id: str,
    perspective_type: str, 
    request: PerspectiveSelectionRequest
):
    """Update perspective selection status"""
    success = remediation_agent.record_perspective_selection(
        node_id,
        perspective_type,
        request.selected
    )
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Node {node_id} or perspective {perspective_type} not found"
        )
    return {"success": True}

@app.put("/api/remediation/node/{node_id}/input")
async def add_user_input(node_id: str, request: UserInputRequest):
    """Add user notes for a node"""
    try:
        remediation_agent.add_user_input(node_id, request.content)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/remediation/roadmap")
async def generate_roadmap():
    """Generate remediation roadmap"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("Received request to generate remediation roadmap")
    
    # Check if investigation is loaded
    if not remediation_agent.board_nodes:
        logger.error("No investigation loaded before attempting to generate roadmap")
        raise HTTPException(
            status_code=400,
            detail="No investigation data loaded. Please load an investigation first."
        )
    
    # Check if perspectives have been generated
    if not remediation_agent.node_perspectives:
        logger.error("No perspectives generated before attempting to generate roadmap")
        raise HTTPException(
            status_code=400,
            detail="No perspectives generated. Please generate perspectives for at least one node."
        )
    
    # Check if any perspectives are selected
    has_selected = False
    for node_id, perspectives in remediation_agent.node_perspectives.items():
        for persp_type, persp in perspectives.items():
            if persp.get("selected") == True:
                has_selected = True
                break
        if has_selected:
            break
    
    if not has_selected:
        logger.warning("No perspectives selected before generating roadmap")
        # This is just a warning, not an error, as it might be valid to generate a roadmap without selections
    
    try:
        logger.info("Calling remediation_agent.generate_remediation_roadmap()")
        roadmap = remediation_agent.generate_remediation_roadmap()
        logger.info("Successfully generated roadmap")
        return roadmap
    except Exception as e:
        logger.error(f"Failed to generate roadmap: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate roadmap: {str(e)}")
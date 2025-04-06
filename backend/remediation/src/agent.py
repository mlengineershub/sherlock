"""
Remediation advisory agent that generates perspectives and roadmaps for security vulnerabilities.
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from backend.common.src.utils.bedrock_client import BedrockClient
from backend.remediation.src.roadmap_generator import RoadmapGenerator as EnhancedRoadmapGenerator
from backend.remediation.config import MODEL_CONFIG

logger = logging.getLogger(__name__)

class PerspectiveGenerator:
    """
    Generates different perspectives on security vulnerabilities.
    """
    
    def __init__(self, bedrock_client: BedrockClient):
        self.bedrock_client = bedrock_client
        
    def generate_perspectives(self, node: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Generate four different perspectives for a node.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Generating all perspectives for node {node['id']}")
        
        perspectives = {}
        perspective_types = ["expert", "attacker", "business", "compliance"]
        
        for perspective_type in perspective_types:
            try:
                logger.info(f"Generating {perspective_type} perspective for node {node['id']}")
                perspectives[perspective_type] = self._generate_perspective(node, perspective_type)
            except Exception as e:
                logger.error(f"Error generating {perspective_type} perspective: {str(e)}", exc_info=True)
                # Continue with other perspectives even if one fails
                perspectives[perspective_type] = {
                    "title": f"{perspective_type.capitalize()} Perspective",
                    "content": f"Error generating perspective: {str(e)}",
                    "selected": None,
                    "error": True
                }
        
        if not perspectives:
            logger.error(f"Failed to generate any perspectives for node {node['id']}")
            raise Exception(f"Failed to generate any perspectives for node {node['id']}")
        
        logger.info(f"Successfully generated {len(perspectives)} perspectives for node {node['id']}")
        return perspectives
        
    def _generate_perspective(self, node: Dict[str, Any], perspective_type: str) -> Dict[str, Any]:
        """Generate a single perspective."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Generating {perspective_type} perspective for node {node['id']}")
        
        prompts = {
            "expert": (
                "You are a senior cybersecurity expert. Provide professional perspective on how "
                f"to address:\n\n{node['title']}\n{node['description']}\n"
                "Focus on technical solutions and security controls (2-3 paragraphs maximum)."
            ),
            "attacker": (
                "Analyze as an attacker:\n\n"
                f"{node['title']}\n{node['description']}\n"
                "Explain attack methods and potential goals (2-3 paragraphs)."
            ),
            "business": (
                "Analyze business impact:\n\n"
                f"{node['title']}\n{node['description']}\n"
                "How would remediation affect operations? (2-3 paragraphs)."
            ),
            "compliance": (
                "Analyze regulatory implications:\n\n"
                f"{node['title']}\n{node['description']}\n"
                "What compliance risks does this create? (2-3 paragraphs)."
            )
        }
        
        # Get model configuration from config
        from backend.remediation.config import MODEL_CONFIG
        model_config = MODEL_CONFIG.get("perspective_generation", {})
        model_id = model_config.get("model_id", "anthropic.claude-3-haiku-20240307-v1:0")
        max_tokens = model_config.get("max_tokens", 300)
        temperature = model_config.get("temperature", 0.7)
        
        logger.info(f"Using model {model_id} for {perspective_type} perspective generation")
        
        try:
            logger.info(f"Invoking model for {perspective_type} perspective")
            response = self.bedrock_client.invoke_model(
                prompt=prompts[perspective_type],
                model_id=model_id,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            logger.info(f"Successfully generated {perspective_type} perspective")
            return {
                "title": f"{perspective_type.capitalize()} Perspective",
                "content": response.strip(),
                "selected": None
            }
        except Exception as e:
            logger.error(f"Failed to generate {perspective_type} perspective: {str(e)}", exc_info=True)
            
            # Try fallback model if primary model fails
            fallback_model = "anthropic.claude-3-haiku-20240307-v1:0"
            if model_id != fallback_model:
                logger.info(f"Trying fallback model {fallback_model}")
                try:
                    response = self.bedrock_client.invoke_model(
                        prompt=prompts[perspective_type],
                        model_id=fallback_model,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    
                    logger.info(f"Successfully generated {perspective_type} perspective with fallback model")
                    return {
                        "title": f"{perspective_type.capitalize()} Perspective",
                        "content": response.strip(),
                        "selected": None
                    }
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {str(fallback_error)}", exc_info=True)
            
            # If we get here, both primary and fallback models failed
            raise Exception(f"Failed to generate {perspective_type} perspective: {str(e)}")


# Legacy RoadmapGenerator class is now replaced by the enhanced version from roadmap_generator.py


class RemediationAgent:
    """
    Main agent for remediation advisory functionality.
    """
    
    def __init__(self, bedrock_client: Optional[BedrockClient] = None):
        self.bedrock_client = bedrock_client or BedrockClient()
        self.perspective_generator = PerspectiveGenerator(self.bedrock_client)
        
        # Use the enhanced RoadmapGenerator from roadmap_generator.py
        logger.info("Initializing EnhancedRoadmapGenerator")
        self.roadmap_generator = EnhancedRoadmapGenerator(self.bedrock_client)
        
        self.board_nodes: List[Dict[str, Any]] = []
        self.node_perspectives: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.user_inputs: Dict[str, str] = {}
        
    def load_investigation_tree(self, tree_path: str) -> None:
        """Load investigation tree for remediation planning."""
        import os
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Attempting to load investigation tree from: {tree_path}")
        
        # Check if file exists
        if not os.path.exists(tree_path):
            logger.error(f"Investigation tree file not found: {tree_path}")
            raise FileNotFoundError(f"Investigation tree file not found: {tree_path}")
        
        try:
            with open(tree_path, 'r') as f:
                logger.info(f"Successfully opened file: {tree_path}")
                try:
                    tree_data = json.load(f)
                    logger.info(f"Successfully parsed JSON from file: {tree_path}")
                    
                    # Basic validation of tree data
                    if not isinstance(tree_data, dict) or "id" not in tree_data:
                        logger.error(f"Invalid tree data format in file: {tree_path}")
                        raise ValueError(f"Invalid tree data format in file: {tree_path}")
                    
                    # Clear existing board nodes before loading new ones
                    self.board_nodes = []
                    
                    self._flatten_tree_to_board(tree_data)
                    logger.info(f"Successfully flattened tree to board with {len(self.board_nodes)} nodes")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from file {tree_path}: {str(e)}")
                    raise ValueError(f"Invalid JSON format in file: {tree_path}")
        except Exception as e:
            logger.error(f"Error loading investigation tree: {str(e)}", exc_info=True)
            raise
            
    def _flatten_tree_to_board(self, node: Dict[str, Any], depth: int = 0) -> None:
        """Convert hierarchical tree to flat board representation."""
        board_node = {
            "id": node["id"],
            "title": node["title"],
            "description": node["description"],
            "type": node["type"],
            "status": node["status"],
            "confidence": node["confidence"],
            "depth": depth
        }
        self.board_nodes.append(board_node)
        
        for child in node.get("children", []):
            self._flatten_tree_to_board(child, depth + 1)
            
    def generate_perspectives(self, node_id: str) -> Dict[str, Dict[str, Any]]:
        """Generate perspectives for a specific node."""
        node = next((n for n in self.board_nodes if n["id"] == node_id), None)
        if not node:
            return {}
            
        perspectives = self.perspective_generator.generate_perspectives(node)
        self.node_perspectives[node_id] = perspectives
        return perspectives
        
    def add_user_input(self, node_id: str, text: str) -> None:
        """Store user-provided input for a node."""
        self.user_inputs[node_id] = text
        
    def record_perspective_selection(self, node_id: str, perspective_type: str, selected: bool) -> bool:
        """Track which perspectives user has selected."""
        if node_id in self.node_perspectives and perspective_type in self.node_perspectives[node_id]:
            self.node_perspectives[node_id][perspective_type]["selected"] = selected
            return True
        return False
        
    def generate_remediation_roadmap(self) -> Dict[str, Any]:
        """Generate final remediation roadmap."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting remediation roadmap generation with {len(self.board_nodes)} board nodes")
        
        # Check if board_nodes is empty
        if not self.board_nodes:
            logger.error("No board nodes available for roadmap generation")
            raise ValueError("No investigation data loaded. Please load an investigation first.")
        
        # Check if perspectives are selected
        has_selected_perspectives = False
        for node_id, perspectives in self.node_perspectives.items():
            for persp_type, persp in perspectives.items():
                if persp.get("selected") == True:
                    has_selected_perspectives = True
                    break
            if has_selected_perspectives:
                break
        
        if not has_selected_perspectives:
            logger.warning("No perspectives selected for any nodes")
        
        relevant_nodes = [
            {
                "node": node,
                "perspectives": self.node_perspectives.get(node["id"], {}),
                "user_input": self.user_inputs.get(node["id"], "")
            }
            for node in self.board_nodes
        ]
        
        logger.info(f"Prepared {len(relevant_nodes)} relevant nodes for roadmap generation")
        
        try:
            logger.info(f"Using RoadmapGenerator class: {self.roadmap_generator.__class__.__module__}.{self.roadmap_generator.__class__.__name__}")
            return self.roadmap_generator.generate_roadmap(relevant_nodes)
        except Exception as e:
            logger.error(f"Failed to generate roadmap: {str(e)}", exc_info=True)
            raise
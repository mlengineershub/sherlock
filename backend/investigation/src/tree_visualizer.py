"""
Tree Exporter for the Investigation Agent.
Provides functionality to export investigation trees to JSON format.
"""

import json
import logging
from typing import Dict

from backend.investigation.src.tree import InvestigationTree

logger = logging.getLogger(__name__)

class TreeVisualizer:
    """
    Simple exporter for investigation trees that outputs JSON format for UI consumption.
    """
    
    def export_tree(self, tree: InvestigationTree) -> Dict:
        """
        Export the tree to a hierarchical JSON format suitable for UI visualization.
        
        Args:
            tree: The investigation tree to export
            
        Returns:
            Dictionary with hierarchical structure of the tree
        """
        if not tree.root_id or not tree.graph.nodes:
            return {"name": "Empty Tree", "children": []}
        
        def build_node(node_id: str) -> Dict:
            """Recursively build a node and its children."""
            node_data = tree.graph.nodes[node_id]
            
            # Get children of this node
            children = list(tree.graph.successors(node_id))
            
            node = {
                "id": node_id,
                "title": node_data.get("title", ""),
                "type": node_data.get("type", ""),
                "description": node_data.get("description", ""),
                "status": node_data.get("status", ""),
                "confidence": node_data.get("confidence", 0.0),
                "evidence": node_data.get("evidence", []),
                "metadata": node_data.get("metadata", {})
            }
            
            if children:
                node["children"] = [build_node(child) for child in children]
            
            return node
        
        # Start building from the root
        return build_node(tree.root_id)
    
    def save_tree(self, tree: InvestigationTree, output_path: str) -> None:
        """
        Save the tree visualization data to a JSON file.
        
        Args:
            tree: The investigation tree to save
            output_path: Path where to save the JSON file
        """
        tree_data = self.export_tree(tree)
        
        with open(output_path, 'w') as f:
            json.dump(tree_data, f, indent=2)
            logger.info(f"Tree data saved to {output_path}")
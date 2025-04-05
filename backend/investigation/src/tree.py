"""
Tree data structures and generator for the Investigation Agent.
"""

import json
import logging
import uuid
from enum import Enum
from typing import Dict, List, Optional, Set, Union

import networkx as nx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class NodeStatus(str, Enum):
    """Status of a node in the investigation tree."""
    UNVERIFIED = "unverified"  # Initial state
    PLAUSIBLE = "plausible"    # User marked as plausible
    IMPLAUSIBLE = "implausible"  # User marked as implausible
    CONFIRMED = "confirmed"    # Confirmed by evidence


class NodeType(str, Enum):
    """Type of a node in the investigation tree."""
    ROOT = "root"  # Root cause of the breach
    VULNERABILITY = "vulnerability"  # A vulnerability that was exploited
    ATTACK_VECTOR = "attack_vector"  # Method used to exploit
    IMPACT = "impact"  # Impact of the breach
    MITIGATION = "mitigation"  # Potential mitigation


class TreeNode(BaseModel):
    """
    Represents a node in the investigation tree.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    type: NodeType
    title: str
    description: str
    status: NodeStatus = NodeStatus.UNVERIFIED
    confidence: float = 0.0  # 0.0 to 1.0
    evidence: List[str] = Field(default_factory=list)
    metadata: Dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert the node to a dictionary."""
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "metadata": self.metadata
        }


class InvestigationTree:
    """
    Represents the investigation tree for breach analysis.
    """
    
    def __init__(self, name: str = "Investigation Tree"):
        """
        Initialize a new investigation tree.
        
        Args:
            name: Name of the investigation tree
        """
        self.name = name
        self.graph = nx.DiGraph()
        self.root_id: Optional[str] = None
        
    def add_node(self, node: TreeNode) -> str:
        """
        Add a node to the tree.
        
        Args:
            node: The node to add
            
        Returns:
            The ID of the added node
        """
        self.graph.add_node(node.id, **node.to_dict())
        
        # If the node has a parent, add an edge
        if node.parent_id:
            if node.parent_id in self.graph:
                self.graph.add_edge(node.parent_id, node.id)
            else:
                logger.warning(f"Parent node {node.parent_id} not found for node {node.id}")
        elif self.root_id is None:
            # If no root exists and this node has no parent, set it as root
            self.root_id = node.id
            
        return node.id
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """
        Get a node by its ID.
        
        Args:
            node_id: The ID of the node to get
            
        Returns:
            The node data or None if not found
        """
        if node_id in self.graph:
            return dict(self.graph.nodes[node_id])
        return None
    
    def update_node(self, node_id: str, **attributes) -> bool:
        """
        Update a node's attributes.
        
        Args:
            node_id: The ID of the node to update
            **attributes: The attributes to update
            
        Returns:
            True if the node was updated, False otherwise
        """
        if node_id in self.graph:
            for key, value in attributes.items():
                self.graph.nodes[node_id][key] = value
            return True
        return False
    
    def get_children(self, node_id: str) -> List[Dict]:
        """
        Get all children of a node.
        
        Args:
            node_id: The ID of the node to get children for
            
        Returns:
            List of child nodes
        """
        if node_id not in self.graph:
            return []
        
        children = []
        for child_id in self.graph.successors(node_id):
            children.append(dict(self.graph.nodes[child_id]))
        
        return children
    
    def get_path_to_root(self, node_id: str) -> List[Dict]:
        """
        Get the path from a node to the root.
        
        Args:
            node_id: The ID of the node to get the path for
            
        Returns:
            List of nodes in the path from the node to the root
        """
        if node_id not in self.graph or self.root_id is None:
            return []
        
        try:
            path = nx.shortest_path(self.graph, self.root_id, node_id)
            return [dict(self.graph.nodes[n]) for n in path]
        except nx.NetworkXNoPath:
            return []
    
    def get_all_nodes(self) -> List[Dict]:
        """
        Get all nodes in the tree.
        
        Returns:
            List of all nodes
        """
        return [dict(self.graph.nodes[n]) for n in self.graph.nodes]
    
    def get_nodes_by_status(self, status: NodeStatus) -> List[Dict]:
        """
        Get all nodes with a specific status.
        
        Args:
            status: The status to filter by
            
        Returns:
            List of nodes with the specified status
        """
        return [
            dict(self.graph.nodes[n]) 
            for n in self.graph.nodes 
            if self.graph.nodes[n].get("status") == status.value
        ]
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[Dict]:
        """
        Get all nodes of a specific type.
        
        Args:
            node_type: The type to filter by
            
        Returns:
            List of nodes with the specified type
        """
        return [
            dict(self.graph.nodes[n]) 
            for n in self.graph.nodes 
            if self.graph.nodes[n].get("type") == node_type.value
        ]
    
    def to_dict(self) -> Dict:
        """
        Convert the tree to a dictionary.
        
        Returns:
            Dictionary representation of the tree
        """
        return {
            "name": self.name,
            "root_id": self.root_id,
            "nodes": self.get_all_nodes(),
            "edges": [{"source": u, "target": v} for u, v in self.graph.edges]
        }
    
    def to_json(self) -> str:
        """
        Convert the tree to a JSON string.
        
        Returns:
            JSON string representation of the tree
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict) -> "InvestigationTree":
        """
        Create a tree from a dictionary.
        
        Args:
            data: Dictionary representation of the tree
            
        Returns:
            New InvestigationTree instance
        """
        tree = cls(name=data.get("name", "Investigation Tree"))
        tree.root_id = data.get("root_id")
        
        # Add nodes
        for node_data in data.get("nodes", []):
            tree.graph.add_node(node_data["id"], **node_data)
        
        # Add edges
        for edge_data in data.get("edges", []):
            tree.graph.add_edge(edge_data["source"], edge_data["target"])
        
        return tree
    
    @classmethod
    def from_json(cls, json_str: str) -> "InvestigationTree":
        """
        Create a tree from a JSON string.
        
        Args:
            json_str: JSON string representation of the tree
            
        Returns:
            New InvestigationTree instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


class TreeGenerator:
    """
    Generator for investigation trees.
    """
    
    def __init__(self):
        """Initialize the tree generator."""
        pass
    
    def create_initial_tree(self, breach_info: str) -> InvestigationTree:
        """
        Create an initial investigation tree based on breach information.
        
        Args:
            breach_info: Description of the breach
            
        Returns:
            New investigation tree with initial nodes
        """
        # This is a placeholder. In a real implementation, this would use
        # the LLM to generate initial nodes based on the breach information.
        tree = InvestigationTree(name=f"Investigation: {breach_info[:50]}...")
        
        # Create root node
        root_node = TreeNode(
            type=NodeType.ROOT,
            title="Initial Breach",
            description=breach_info,
            confidence=0.8
        )
        tree.add_node(root_node)
        
        return tree
    
    def generate_next_level(
        self, 
        tree: InvestigationTree, 
        parent_id: str,
        num_nodes: int = 3
    ) -> List[str]:
        """
        Generate the next level of nodes for a given parent node.
        
        Args:
            tree: The investigation tree
            parent_id: The ID of the parent node
            num_nodes: Number of nodes to generate
            
        Returns:
            List of IDs of the generated nodes
        """
        # This is a placeholder. In a real implementation, this would use
        # the LLM to generate next-level nodes based on the parent node.
        parent_node = tree.get_node(parent_id)
        if not parent_node:
            return []
        
        node_ids = []
        for i in range(num_nodes):
            node = TreeNode(
                parent_id=parent_id,
                type=NodeType.ATTACK_VECTOR,
                title=f"Hypothesis {i+1}",
                description=f"This is a potential next step in the attack path based on {parent_node['title']}",
                confidence=0.5
            )
            node_id = tree.add_node(node)
            node_ids.append(node_id)
        
        return node_ids
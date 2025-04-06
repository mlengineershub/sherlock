"""
Investigation Agent for security breach analysis.
Creates and manages the investigation tree for breach analysis.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Union, Any

from pydantic import BaseModel, Field

from backend.common.src.utils.bedrock_client import BedrockClient
from backend.investigation.src.tree import InvestigationTree, TreeNode, NodeStatus, NodeType
from backend.investigation.src.nvd_client import NVDClient, CVEVulnerability
from backend.investigation.src.hypothesis_generator import HypothesisGenerator
from backend.investigation.src.tree_visualizer import TreeVisualizer

logger = logging.getLogger(__name__)

class InvestigationReport(BaseModel):
    """Report generated from the investigation."""
    title: str
    summary: str
    findings: List[Dict] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    graph_data: Optional[Dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class InvestigationAgent:
    """
    Agent for security breach investigation.
    Creates and manages the investigation tree for breach analysis.
    """
    
    def __init__(
        self,
        bedrock_client: Optional[BedrockClient] = None,
        nvd_client: Optional[NVDClient] = None,
        hypothesis_generator: Optional[HypothesisGenerator] = None,
        tree_visualizer: Optional[TreeVisualizer] = None
    ):
        """
        Initialize the investigation agent.
        
        Args:
            bedrock_client: Optional BedrockClient instance
            nvd_client: Optional NVDClient instance
            hypothesis_generator: Optional HypothesisGenerator instance
            tree_visualizer: Optional TreeVisualizer instance
        """
        self.bedrock_client = bedrock_client or BedrockClient()
        self.nvd_client = nvd_client or NVDClient()
        self.hypothesis_generator = hypothesis_generator or HypothesisGenerator(self.bedrock_client)
        self.tree_visualizer = tree_visualizer or TreeVisualizer()
        self.current_tree: Optional[InvestigationTree] = None
    
    def create_investigation(self, breach_info: str, num_initial_nodes: int = 3) -> InvestigationTree:
        """
        Create a new investigation tree based on breach information.
        
        Args:
            breach_info: Description of the breach
            num_initial_nodes: Number of initial nodes to generate
            
        Returns:
            The created investigation tree
        """
        # Create a new tree
        self.current_tree = InvestigationTree(name=f"Investigation: {breach_info[:50]}...")
        
        # Create root node
        root_node = TreeNode(
            type=NodeType.ROOT,
            title="Initial Breach",
            description=breach_info,
            confidence=0.8
        )
        root_id = self.current_tree.add_node(root_node)
        
        # Generate initial hypotheses
        self.hypothesis_generator.generate_next_level(
            tree=self.current_tree,
            parent_id=root_id,
            num_nodes=num_initial_nodes
        )
        
        return self.current_tree
    
    def get_current_tree(self) -> Optional[InvestigationTree]:
        """
        Get the current investigation tree.
        
        Returns:
            The current investigation tree or None if no investigation is in progress
        """
        return self.current_tree
    
    def update_node_status(self, node_id: str, status: NodeStatus) -> bool:
        """
        Update the status of a node in the investigation tree.
        
        Args:
            node_id: The ID of the node to update
            status: The new status for the node
            
        Returns:
            True if the node was updated, False otherwise
        """
        if not self.current_tree:
            return False
        
        return self.current_tree.update_node(node_id, status=status.value)
    
    def generate_next_level(
        self, 
        parent_id: str, 
        num_nodes: int = 3,
        enrich_with_nvd: bool = True
    ) -> List[str]:
        """
        Generate the next level of nodes for a given parent node.
        
        Args:
            parent_id: The ID of the parent node
            num_nodes: Number of nodes to generate
            enrich_with_nvd: Whether to enrich with NVD data
            
        Returns:
            List of IDs of the generated nodes
        """
        if not self.current_tree:
            return []
        
        # Get the parent node
        parent_node = self.current_tree.get_node(parent_id)
        if not parent_node:
            return []
        
        # Only generate next level for plausible or confirmed nodes
        if parent_node.get("status") not in [NodeStatus.PLAUSIBLE.value, NodeStatus.CONFIRMED.value]:
            parent_node_id = parent_node.get("id")
            self.current_tree.update_node(parent_node_id, status=NodeStatus.PLAUSIBLE.value)
        
        # Get related vulnerabilities if enrichment is enabled
        related_vulnerabilities = []
        if enrich_with_nvd:
            # Extract keywords from the parent node
            keywords = self._extract_keywords(parent_node.get("title", ""), parent_node.get("description", ""))
            
            # Search for related vulnerabilities
            vulnerabilities = self.nvd_client.search_by_keywords(keywords, max_results=5)
            
            # Convert to dictionaries
            for vuln in vulnerabilities:
                vuln_dict = {
                    "id": vuln.id,
                    "description": next((d.value for d in vuln.descriptions if d.lang == "en"), "")
                }
                related_vulnerabilities.append(vuln_dict)
        
        # Generate next level nodes
        return self.hypothesis_generator.generate_next_level(
            tree=self.current_tree,
            parent_id=parent_id,
            related_vulnerabilities=related_vulnerabilities,
            num_nodes=num_nodes
        )
    
    def _extract_keywords(self, title: str, description: str) -> List[str]:
        """
        Extract keywords from a node's title and description.
        
        Args:
            title: The node title
            description: The node description
            
        Returns:
            List of extracted keywords
        """
        # This is a simple implementation that could be improved with NLP
        combined_text = f"{title} {description}".lower()
        
        # Remove common words and punctuation
        common_words = {
            "the", "and", "a", "an", "in", "on", "at", "to", "for", "with",
            "by", "of", "from", "as", "is", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "but",
            "or", "if", "then", "else", "when", "where", "why", "how",
            "all", "any", "both", "each", "few", "more", "most", "other",
            "some", "such", "no", "nor", "not", "only", "own", "same", "so",
            "than", "too", "very", "can", "will", "just", "should", "now"
        }
        
        # Split into words and filter
        words = combined_text.split()
        keywords = [
            word.strip(".,;:!?()[]{}\"'") 
            for word in words 
            if word.strip(".,;:!?()[]{}\"'") not in common_words and len(word) > 3
        ]
        
        # Get unique keywords
        unique_keywords = list(set(keywords))
        
        # Sort by length (longer words are often more specific)
        unique_keywords.sort(key=len, reverse=True)
        
        # Return top keywords (limit to 10)
        return unique_keywords[:10]
    
    def export_tree_visualization(self, output_path: Optional[str] = None) -> Optional[Dict]:
        """
        Export the current investigation tree in a format suitable for visualization.
        
        Args:
            output_path: Optional path to save the visualization data as JSON
            
        Returns:
            Dictionary containing the tree visualization data, or None if no tree exists
        """
        if not self.current_tree:
            return None
        
        tree_data = self.tree_visualizer.export_tree(tree=self.current_tree)
        
        if output_path:
            self.tree_visualizer.save_tree(
                tree=self.current_tree,
                output_path=output_path
            )
        
        return tree_data
    
    def export_tree_to_json(self, output_path: Optional[str] = None) -> str:
        """
        Export the current investigation tree to JSON.
        
        Args:
            output_path: Optional path to save the JSON
            
        Returns:
            JSON string representation of the tree
        """
        if not self.current_tree:
            return "{}"
        
        tree_json = self.current_tree.to_json()
        
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                f.write(tree_json)
        
        return tree_json
    
    
    def generate_report(self, output_path: Optional[str] = None) -> InvestigationReport:
        """
        Generate a report from the current investigation.
        
        Args:
            output_path: Optional path to save the report
            
        Returns:
            The generated report
        """
        if not self.current_tree:
            return InvestigationReport(
                title="No Investigation",
                summary="No investigation has been created."
            )
        
        # Get all plausible and confirmed nodes
        plausible_nodes = self.current_tree.get_nodes_by_status(NodeStatus.PLAUSIBLE)
        confirmed_nodes = self.current_tree.get_nodes_by_status(NodeStatus.CONFIRMED)
        
        # Combine and sort by confidence
        relevant_nodes = plausible_nodes + confirmed_nodes
        relevant_nodes.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
        
        # Generate findings from relevant nodes
        findings = []
        for node in relevant_nodes:
            finding = {
                "title": node.get("title", ""),
                "description": node.get("description", ""),
                "type": node.get("type", ""),
                "confidence": node.get("confidence", 0.0),
                "evidence": node.get("evidence", []),
                "status": node.get("status", "")
            }
            findings.append(finding)
        
        # Get the graph visualization data
        graph_data = self.export_tree_visualization()
        
        # Create the report
        report = InvestigationReport(
            title=f"Investigation Report: {self.current_tree.name}",
            summary=self._generate_summary(),
            findings=findings,
            recommendations=self._generate_recommendations(),
            graph_data=graph_data
        )
        
        # Save the report if output path is provided
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                json_str = report.model_dump_json()
                formatted_json = json.dumps(json.loads(json_str), indent=2)
                f.write(formatted_json)
        
        return report
    
    def _generate_summary(self) -> str:
        """
        Generate a summary of the investigation.
        
        Returns:
            Summary string
        """
        if not self.current_tree or not self.current_tree.root_id:
            return "No investigation data available."
        
        # Get the root node
        root_node = self.current_tree.get_node(self.current_tree.root_id)
        if not root_node:
            return "No investigation data available."
        
        # Get all plausible and confirmed nodes
        plausible_nodes = self.current_tree.get_nodes_by_status(NodeStatus.PLAUSIBLE)
        confirmed_nodes = self.current_tree.get_nodes_by_status(NodeStatus.CONFIRMED)
        
        # Create a summary prompt for the LLM
        prompt = f"""
You are a cybersecurity expert analyzing a security breach investigation. 
Generate a concise summary (3-5 paragraphs) of the investigation based on the following information:

BREACH DESCRIPTION:
{root_node.get('description', '')}

CONFIRMED FINDINGS ({len(confirmed_nodes)}):
{chr(10).join([f"- {node.get('title', '')}: {node.get('description', '')}" for node in confirmed_nodes])}

PLAUSIBLE FINDINGS ({len(plausible_nodes)}):
{chr(10).join([f"- {node.get('title', '')}: {node.get('description', '')}" for node in plausible_nodes])}

Your summary should highlight the most significant findings, potential attack vectors, and overall security implications.
"""
        
        try:
            # Generate summary using the LLM
            summary = self.bedrock_client.invoke_model(
                prompt=prompt,
                model_id="anthropic.claude-3-opus-20240229-v1:0",
                max_tokens=1000
            )
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Investigation of {root_node.get('description', '')[:100]}... found {len(confirmed_nodes)} confirmed and {len(plausible_nodes)} plausible findings."
    
    def _generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on the investigation.
        
        Returns:
            List of recommendation strings
        """
        if not self.current_tree or not self.current_tree.root_id:
            return ["No recommendations available."]
        
        # Get all plausible and confirmed nodes
        plausible_nodes = self.current_tree.get_nodes_by_status(NodeStatus.PLAUSIBLE)
        confirmed_nodes = self.current_tree.get_nodes_by_status(NodeStatus.CONFIRMED)
        
        # Combine and get the top 5 by confidence
        relevant_nodes = plausible_nodes + confirmed_nodes
        relevant_nodes.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
        top_nodes = relevant_nodes[:5]
        
        # Create a recommendations prompt for the LLM
        prompt = f"""
You are a cybersecurity expert analyzing a security breach investigation. 
Generate 3-5 specific, actionable recommendations based on the following findings:

FINDINGS:
{chr(10).join([f"- {node.get('title', '')}: {node.get('description', '')}" for node in top_nodes])}

Your recommendations should be specific, actionable, and directly address the security issues identified.
Each recommendation should be a single, concise sentence.
"""
        
        try:
            # Generate recommendations using the LLM
            response = self.bedrock_client.invoke_model(
                prompt=prompt,
                model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
                max_tokens=500
            )
            
            # Parse the recommendations
            recommendations = []
            for line in response.strip().split("\n"):
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("1.") or line.startswith("2.")):
                    recommendations.append(line.lstrip("- 123456789.").strip())
            
            return recommendations if recommendations else ["No specific recommendations available."]
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Implement security patches for identified vulnerabilities.",
                   "Review and strengthen access controls.",
                   "Enhance monitoring for suspicious activities."]
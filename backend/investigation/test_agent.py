#!/usr/bin/env python3
"""
Test script for the Investigation Agent.
Demonstrates the functionality of the Investigation Agent without integration.
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.investigation.src.agent import InvestigationAgent
from backend.investigation.src.tree import NodeStatus, NodeType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test the Investigation Agent")
    
    parser.add_argument(
        "--breach-info",
        type=str,
        default="Unauthorized access detected to the customer database server. " +
                "The server logs show multiple failed login attempts followed by a successful login " +
                "from an IP address not associated with our organization. " +
                "The attacker appears to have exfiltrated customer data including names, " +
                "email addresses, and hashed passwords.",
        help="Description of the security breach"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output",
        help="Directory to save output files"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    
    return parser.parse_args()

def interactive_mode(agent: InvestigationAgent, output_dir: str):
    """
    Run the agent in interactive mode.
    
    Args:
        agent: The investigation agent
        output_dir: Directory to save output files
    """
    print("\n=== Investigation Agent Interactive Mode ===\n")
    
    # Get breach information
    breach_info = input("Enter breach description: ")
    if not breach_info:
        breach_info = "Unauthorized access detected to the customer database server. " + \
                     "The server logs show multiple failed login attempts followed by a successful login " + \
                     "from an IP address not associated with our organization. " + \
                     "The attacker appears to have exfiltrated customer data including names, " + \
                     "email addresses, and hashed passwords."
        print(f"Using default breach description: {breach_info}")
    
    # Create investigation
    print("\nCreating investigation tree...")
    tree = agent.create_investigation(breach_info)
    
    # Main interaction loop
    while True:
        print("\n=== Investigation Tree ===\n")
        
        # Display the tree structure
        tree_data = agent.export_tree_visualization()
        if tree_data:
            print(json.dumps(tree_data, indent=2))
        
        # Get all nodes
        all_nodes = tree.get_all_nodes()
        
        # Display nodes
        print("\n=== Nodes ===\n")
        for i, node in enumerate(all_nodes):
            status = node.get("status", "unverified")
            print(f"{i+1}. [{status}] {node.get('title', '')}: {node.get('description', '')[:100]}...")
            print(f"   ID: {node.get('id', '')}")
            print()
        
        # Display options
        print("\n=== Options ===\n")
        print("1. Mark node as plausible")
        print("2. Mark node as implausible")
        print("3. Mark node as confirmed")
        print("4. Generate next level for a node")
        print("5. Generate report")
        print("6. Export tree visualization")
        print("7. Save tree to JSON")
        print("8. Exit")
        
        choice = input("\nEnter choice (1-8): ")
        
        if choice == "1" or choice == "2" or choice == "3":
            node_idx = int(input("Enter node number: ")) - 1
            if 0 <= node_idx < len(all_nodes):
                node_id = all_nodes[node_idx].get("id", "")
                if choice == "1":
                    agent.update_node_status(node_id, NodeStatus.PLAUSIBLE)
                    print(f"Node marked as plausible")
                elif choice == "2":
                    agent.update_node_status(node_id, NodeStatus.IMPLAUSIBLE)
                    print(f"Node marked as implausible")
                else:
                    agent.update_node_status(node_id, NodeStatus.CONFIRMED)
                    print(f"Node marked as confirmed")
            else:
                print("Invalid node number")
        
        elif choice == "4":
            node_idx = int(input("Enter node number: ")) - 1
            if 0 <= node_idx < len(all_nodes):
                node_id = all_nodes[node_idx].get("id", "")
                num_nodes = int(input("Enter number of nodes to generate (default 3): ") or "3")
                print(f"Generating next level for node {node_idx+1}...")
                new_node_ids = agent.generate_next_level(node_id, num_nodes=num_nodes)
                print(f"Generated {len(new_node_ids)} new nodes")
            else:
                print("Invalid node number")
        elif choice == "5":
            print("Visualization option removed - use Mermaid format output instead")
        
        
        elif choice == "6":
            report_path = os.path.join(output_dir, "investigation_report.json")
            print(f"Generating report to {report_path}...")
            report = agent.generate_report(output_path=report_path)
            print("\n=== Report Summary ===\n")
            print(report.summary)
            print("\n=== Recommendations ===\n")
            for i, rec in enumerate(report.recommendations):
                print(f"{i+1}. {rec}")
            print(f"\nFull report saved to {report_path}")
        
        elif choice == "7":
            viz_path = os.path.join(output_dir, "investigation_tree_viz.json")
            print(f"Exporting tree visualization to {viz_path}...")
            agent.export_tree_visualization(output_path=viz_path)
            print(f"Tree visualization exported to {viz_path}")
        
        elif choice == "8":
            print("Exiting...")
            break
        
        else:
            print("Invalid choice")

def automated_test(agent: InvestigationAgent, breach_info: str, output_dir: str):
    """
    Run an automated test of the agent.
    
    Args:
        agent: The investigation agent
        breach_info: Description of the breach
        output_dir: Directory to save output files
    """
    print("\n=== Running Automated Test ===\n")
    
    # Create investigation
    print(f"Creating investigation for breach: {breach_info[:100]}...")
    tree = agent.create_investigation(breach_info)
    
    # Get all nodes
    all_nodes = tree.get_all_nodes()
    print(f"Initial tree created with {len(all_nodes)} nodes")
    
    # Mark some nodes as plausible
    if len(all_nodes) > 1:
        print("Marking nodes as plausible...")
        for i, node in enumerate(all_nodes[1:3]):  # Mark first two non-root nodes as plausible
            node_id = node.get("id", "")
            agent.update_node_status(node_id, NodeStatus.PLAUSIBLE)
            print(f"  Node '{node.get('title', '')}' marked as plausible")
    
    # Generate next level for plausible nodes
    plausible_nodes = tree.get_nodes_by_status(NodeStatus.PLAUSIBLE)
    if plausible_nodes:
        print("Generating next level for plausible nodes...")
        for node in plausible_nodes:
            node_id = node.get("id", "")
            new_node_ids = agent.generate_next_level(node_id, num_nodes=2)
            print(f"  Generated {len(new_node_ids)} new nodes for '{node.get('title', '')}'")
    
    # Mark some new nodes as confirmed
    all_nodes = tree.get_all_nodes()
    if len(all_nodes) > 5:
        print("Marking some nodes as confirmed...")
        for i, node in enumerate(all_nodes[3:5]):  # Mark two nodes as confirmed
            node_id = node.get("id", "")
            agent.update_node_status(node_id, NodeStatus.CONFIRMED)
            print(f"  Node '{node.get('title', '')}' marked as confirmed")
    # Tree visualization removed - use Mermaid format output instead
    
    
    # Export tree to JSON
    json_path = os.path.join(output_dir, "investigation_tree.json")
    print(f"Exporting tree to {json_path}...")
    agent.export_tree_to_json(output_path=json_path)
    print(f"Tree exported to {json_path}")
    
    # Export tree visualization
    viz_path = os.path.join(output_dir, "investigation_tree_viz.json")
    print(f"Exporting tree visualization to {viz_path}...")
    agent.export_tree_visualization(output_path=viz_path)
    print(f"Tree visualization exported to {viz_path}")
    
    # Generate report
    report_path = os.path.join(output_dir, "investigation_report.json")
    print(f"Generating report to {report_path}...")
    report = agent.generate_report(output_path=report_path)
    
    print("\n=== Report Summary ===\n")
    print(report.summary)
    
    print("\n=== Recommendations ===\n")
    for i, rec in enumerate(report.recommendations):
        print(f"{i+1}. {rec}")
    
    print(f"\nFull report saved to {report_path}")
    print("\n=== Test Complete ===\n")

def main():
    """Main function."""
    args = parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create the investigation agent
    agent = InvestigationAgent()
    
    if args.interactive:
        interactive_mode(agent, args.output_dir)
    else:
        automated_test(agent, args.breach_info, args.output_dir)

if __name__ == "__main__":
    main()
# Investigation Agent

The Investigation Agent creates and manages the investigation tree for security breach analysis in the Sherlock system.

## Overview

The Investigation Agent is responsible for:
- Creating and managing investigation trees for security breach analysis
- Generating hypotheses for potential attack paths
- Enriching the investigation with vulnerability data from NVD
- Visualizing the investigation tree
- Generating breach analysis reports

## Components

### 1. Tree Data Structures and Generator

The `tree.py` module provides the core data structures for the investigation tree:
- `TreeNode`: Represents a node in the investigation tree
- `InvestigationTree`: Manages the tree structure using NetworkX
- `NodeStatus`: Enum for node statuses (unverified, plausible, implausible, confirmed)
- `NodeType`: Enum for node types (root, vulnerability, attack_vector, impact, mitigation)

### 2. NVD API Client

The `nvd_client.py` module provides integration with the National Vulnerability Database (NVD):
- Searches for vulnerabilities by keywords
- Retrieves detailed vulnerability information
- Parses CVSS scores and other vulnerability metadata

### 3. Hypothesis Generator

The `hypothesis_generator.py` module uses AWS Bedrock LLMs to generate hypotheses:
- Creates initial nodes for the investigation tree
- Generates next-level nodes based on user feedback
- Enriches hypotheses with vulnerability data

### 4. Tree Visualizer

The `tree_visualizer.py` module provides visualization capabilities:
- Generates visual representations of the investigation tree using matplotlib
- Exports the tree to Mermaid.js format for web rendering
- Exports the tree to D3.js compatible JSON for interactive visualization

### 5. Main Agent

The `agent.py` module integrates all components and provides the main API:
- Creates and manages investigations
- Updates node statuses based on user feedback
- Generates next-level nodes
- Visualizes the tree
- Generates reports

## Usage

### Basic Usage

```python
from backend.investigation.src.agent import InvestigationAgent

# Create the agent
agent = InvestigationAgent()

# Create a new investigation
breach_info = "Unauthorized access detected to the customer database server..."
tree = agent.create_investigation(breach_info)

# Get all nodes
nodes = tree.get_all_nodes()

# Mark a node as plausible
agent.update_node_status(node_id, NodeStatus.PLAUSIBLE)

# Generate next level nodes
new_node_ids = agent.generate_next_level(node_id)

# Visualize the tree
agent.visualize_tree(output_path="tree.png")

# Generate a report
report = agent.generate_report(output_path="report.json")
```

### Test Script

The repository includes a test script that demonstrates the functionality of the Investigation Agent:

```bash
# Run in automated mode
python backend/investigation/test_agent.py --output-dir ./output

# Run in interactive mode
python backend/investigation/test_agent.py --interactive --output-dir ./output

# Provide a custom breach description
python backend/investigation/test_agent.py --breach-info "SQL injection attack detected..." --output-dir ./output
```

## Integration with AWS Bedrock

The Investigation Agent uses AWS Bedrock for LLM capabilities:
- Claude 3 Opus for hypothesis generation and tree analysis
- Claude 3 Haiku for user interaction and recommendations

## Dependencies

- boto3: AWS SDK for Python
- instructor: Structured output from LLMs
- anthropic: Anthropic Claude models on AWS Bedrock
- pydantic: Data validation and parsing
- networkx: Graph data structures for the investigation tree
- matplotlib: Visualization of the investigation tree
- requests: HTTP requests for NVD API

## Future Enhancements

- Integration with other agents in the Sherlock system
- More sophisticated NLP for keyword extraction
- Enhanced visualization options
- Real-time collaboration features
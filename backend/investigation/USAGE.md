# Investigation Agent Usage Guide

This document provides instructions for setting up and running the Investigation Agent.

## Setup

### 1. Install Dependencies

Install the required dependencies using pip:

```bash
pip install -r requirements.txt
```

Alternatively, you can install the dependencies directly:

```bash
pip install boto3 instructor anthropic pydantic networkx matplotlib requests
```

### 2. Configure AWS Credentials

The Investigation Agent uses AWS Bedrock for LLM capabilities. You need to configure your AWS credentials:

```bash
aws configure
```

Provide your AWS Access Key ID, Secret Access Key, default region (e.g., us-east-1), and output format (json).

Alternatively, you can set the environment variables:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### 3. Ensure AWS Bedrock Access

Make sure your AWS account has access to the Claude models on AWS Bedrock:
- Claude 3 Opus (anthropic.claude-3-opus-20240229-v1:0)
- Claude 3 Haiku (anthropic.claude-3-5-haiku-20241022-v1:0)

## Running the Test Script

The repository includes a test script that demonstrates the functionality of the Investigation Agent.

### Automated Test

Run the test script in automated mode:

```bash
python backend/investigation/test_agent.py --output-dir ./output
```

This will:
1. Create an investigation with a default breach description
2. Mark some nodes as plausible
3. Generate next-level nodes
4. Mark some nodes as confirmed
5. Visualize the tree
6. Generate a report

### Interactive Mode

Run the test script in interactive mode:

```bash
python backend/investigation/test_agent.py --interactive --output-dir ./output
```

In interactive mode, you can:
1. Enter a custom breach description
2. Mark nodes as plausible, implausible, or confirmed
3. Generate next-level nodes
4. Visualize the tree
5. Generate a report
6. Export the tree to JSON

### Custom Breach Description

Provide a custom breach description:

```bash
python backend/investigation/test_agent.py --breach-info "SQL injection attack detected in the login form. The attacker was able to extract user credentials and gain administrative access." --output-dir ./output
```

## Output Files

The test script generates the following output files:

- `tree_visualization.png`: Visualization of the investigation tree
- `investigation_tree.json`: JSON representation of the investigation tree
- `investigation_tree.mmd`: Mermaid.js representation of the investigation tree
- `investigation_report.json`: JSON report of the investigation findings and recommendations

## Integration with Other Components

To integrate the Investigation Agent with other components of the Sherlock system:

1. Import the InvestigationAgent class:
   ```python
   from backend.investigation.src.agent import InvestigationAgent
   ```

2. Create an instance of the agent:
   ```python
   agent = InvestigationAgent()
   ```

3. Use the agent's methods to create and manage investigations:
   ```python
   tree = agent.create_investigation(breach_info)
   agent.update_node_status(node_id, NodeStatus.PLAUSIBLE)
   agent.generate_next_level(node_id)
   agent.generate_report()
   ```

## Troubleshooting

### AWS Bedrock Access Issues

If you encounter issues with AWS Bedrock access:
1. Verify that your AWS credentials are correct
2. Ensure that your AWS account has access to the Claude models on AWS Bedrock
3. Check that the region you're using has the Claude models available

### Visualization Issues

If you encounter issues with visualization:
1. Ensure that matplotlib is installed correctly
2. If using a headless environment, set the matplotlib backend:
   ```python
   import matplotlib
   matplotlib.use('Agg')
   ```

### NVD API Rate Limiting

The NVD API has rate limits. If you encounter rate limiting issues:
1. Increase the rate_limit_delay in the NVDClient class
2. Consider obtaining an NVD API key for higher rate limits
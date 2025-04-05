# Common Utilities

This directory contains common utilities and shared functionality for the Sherlock system.

## Overview

The common utilities provide shared functionality that can be used by all agents in the Sherlock system, including:
- AWS Bedrock integration for LLM capabilities
- Shared data models and utilities
- Common configuration and logging

## Components

### 1. AWS Bedrock Client

The `src/utils/bedrock_client.py` module provides integration with AWS Bedrock for LLM capabilities:

- `BedrockClient`: Client for interacting with AWS Bedrock models
  - `invoke_model()`: Invokes a Bedrock model with a prompt and returns the generated text
  - `get_structured_output()`: Gets structured output from a Bedrock model using the Instructor library

#### Usage

```python
from backend.common.src.utils.bedrock_client import BedrockClient

# Create the client
bedrock_client = BedrockClient()

# Invoke a model with a prompt
prompt = "Explain the concept of XSS attacks"
response = bedrock_client.invoke_model(
    prompt=prompt,
    model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
    max_tokens=1000
)

# Get structured output using Instructor
from pydantic import BaseModel

class SecurityVulnerability(BaseModel):
    name: str
    description: str
    severity: str
    mitigation: str

prompt = "Describe the SQL injection vulnerability"
vulnerability = bedrock_client.get_structured_output(
    prompt=prompt,
    response_model=SecurityVulnerability,
    model_id="anthropic.claude-3-5-haiku-20241022-v1:0"
)
```

## Integration with AWS Bedrock

The common utilities use AWS Bedrock for LLM capabilities, supporting the following models:
- Claude 3 Opus: For complex reasoning and detailed analysis
- Claude 3 Sonnet: For balanced performance and cost
- Claude 3 Haiku: For fast responses and interactive elements

## Dependencies

- boto3: AWS SDK for Python
- instructor: Structured output from LLMs
- anthropic: Anthropic Claude models on AWS Bedrock
- pydantic: Data validation and parsing
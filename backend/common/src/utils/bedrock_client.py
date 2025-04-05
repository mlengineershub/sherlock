"""
AWS Bedrock Client for LLM integration.
Provides functionality to interact with AWS Bedrock models.
"""

import json
import logging
import os
from typing import Any, Dict, Optional, Type

import boto3
# import instructor # Removed instructor
# from anthropic import AnthropicBedrock # Removed unused import
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from botocore.config import Config


logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class BedrockClient:
    """Client for interacting with AWS Bedrock models."""
    
    def __init__(self, region_name: Optional[str] = None):
        """
        Initialize the Bedrock client.
        
        Args:
            region_name: AWS region name where Bedrock is available. If None, uses AWS_DEFAULT_REGION from env
        """
        # Get AWS credentials from environment variables
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_session_token = os.getenv('AWS_SESSION_TOKEN')
        self.region_name = region_name or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

        # Create Bedrock client with explicit credentials
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=self.region_name)
        # self.instructor_client = instructor.from_bedrock(self.bedrock_runtime) # Removed instructor client
        

    def invoke_model(
        self,
        prompt: str,
        model_id: str = "anthropic.claude-3-5-haiku-20241022-v1:0",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        top_p: float = 0.999,
        top_k: int = 250
    ) -> str:
        """
        Invoke a Bedrock model with a prompt and return the generated text.
        
        Args:
            prompt: The input prompt for the model
            model_id: The ID of the model to use
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling (higher = more random)
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            
        Returns:
            The generated text response
        """
        try:
            # Prepare the payload based on the model provider
            if model_id.startswith("anthropic.claude"):
                payload = {
                    "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                    "max_tokens_to_sample": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k
                }
            else:
                # Default payload structure (can be extended for other models)
                payload = {
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p
                }
                
            body = json.dumps(payload)
            
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=model_id,
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            
            # Print the full raw response
            logger.info(f"Raw response from {model_id}: {response_body}")
            
            # Extract the generated text based on the model provider
            if model_id.startswith("anthropic.claude"):
                generated_text = response_body.get('completion', '')
            else:
                # Default extraction (can be extended for other models)
                generated_text = response_body.get('generated_text', '')
            
            # Log the response for debugging
            logger.info(f"Model response from {model_id}: {generated_text}")
                
            return generated_text
            
        except Exception as e:
            logger.error(f"Error invoking Bedrock model: {e}")
            raise
    
    def get_structured_output(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0", # Updated default model
        max_tokens: int = 2048, # Increased default max_tokens
        temperature: float = 0.5 # Adjusted default temperature
    ) -> BaseModel:
        """
        Get structured output from a Bedrock model by prompting for JSON.

        Args:
            prompt: The input prompt for the model.
            response_model: The Pydantic model to structure the response.
            model_id: The ID of the model to use.
            max_tokens: Maximum number of tokens to generate.
            temperature: Temperature for sampling.

        Returns:
            An instance of the provided Pydantic model.
        """
        try:
            # Generate JSON schema from the Pydantic model
            schema = response_model.model_json_schema()
            schema_str = json.dumps(schema, indent=2)

            # Define a system prompt instructing the model
            system_prompt = f"""Please act as an expert API. Your task is to process the user's request and provide a response strictly in JSON format. The JSON object must conform exactly to the following JSON Schema:

```json
{schema_str}
```

Do not include any introductory text, explanations, apologies, concluding remarks, or any text outside the JSON object. Your response must start with `{{` and end with `}}`. Ensure the JSON is valid and adheres to the schema's structure and data types."""

            # Format the request body based on the model provider (Claude example)
            if model_id.startswith("anthropic.claude"):
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "system": system_prompt,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
                request_body = json.dumps(body)
                logger.info(f"Sending request to Claude model {model_id} with system prompt and JSON schema.")

            # TODO: Add support for other model providers (e.g., Cohere, AI21) if needed
            # elif model_id.startswith("cohere."): ...
            # elif model_id.startswith("ai21."): ...
            else:
                # Fallback or default handling - might need adjustment based on target models
                # This basic structure might work for some models but needs testing.
                # It assumes a simple prompt structure without a dedicated system prompt field.
                full_prompt = f"{system_prompt}\n\nUser Request:\n{prompt}\n\nJSON Response:"
                body = {
                    "prompt": full_prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    # Add other relevant parameters like top_p, top_k if needed
                }
                request_body = json.dumps(body)
                logger.warning(f"Using generic request format for model {model_id}. May require adjustments.")


            # Invoke the model
            response = self.bedrock_runtime.invoke_model(
                body=request_body,
                modelId=model_id,
                contentType='application/json',
                accept='application/json'
            )

            response_body = json.loads(response['body'].read())
            logger.debug(f"Raw response body from {model_id}: {response_body}")

            # Extract the response text based on the model provider
            response_text = ""
            if model_id.startswith("anthropic.claude"):
                if response_body.get("content") and isinstance(response_body["content"], list):
                    # Handle Claude 3 messages format
                    for block in response_body["content"]:
                        if block.get("type") == "text":
                            response_text = block.get("text", "")
                            break
                else:
                    # Fallback for older Claude formats (if any) or unexpected responses
                    response_text = str(response_body) # Or handle more gracefully
                    logger.warning(f"Unexpected Claude response format: {response_body}")

            # TODO: Add extraction logic for other model providers
            # elif model_id.startswith("cohere."): response_text = response_body.get('generations', [{}])[0].get('text', '')
            # elif model_id.startswith("ai21."): response_text = response_body.get('completions', [{}])[0].get('data', {}).get('text', '')
            else:
                # Default/Fallback extraction (adjust as needed)
                response_text = response_body.get('completion', '') or \
                                response_body.get('generated_text', '') or \
                                str(response_body) # Last resort
                logger.warning(f"Using generic response extraction for model {model_id}.")


            logger.info(f"Raw response text from {model_id}: {response_text}")

            # Clean the response text: remove potential markdown code fences and strip whitespace
            import re
            cleaned_text = re.sub(r'^```json\s*|\s*```$', '', response_text.strip())

            # Validate and parse the cleaned JSON string using the Pydantic model
            try:
                parsed_response = response_model.model_validate_json(cleaned_text)
                logger.info(f"Successfully parsed structured response from {model_id}")
                return parsed_response
            except Exception as json_error:
                logger.error(f"Failed to parse JSON response from {model_id}. Error: {json_error}")
                logger.error(f"Cleaned text attempted to parse: {cleaned_text}")
                # Optionally, raise a custom error or return a default/error state
                raise ValueError(f"Failed to parse model response into {response_model.__name__}") from json_error

        except Exception as e:
            logger.error(f"Error getting structured output from Bedrock model {model_id}: {e}")
            raise
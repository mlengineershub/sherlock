"""
AWS Bedrock Client for LLM integration.
Provides functionality to interact with AWS Bedrock models.
"""

import json
import logging
from typing import Any, Dict, Optional, Type, Union

import boto3
import instructor
from anthropic import AnthropicBedrock
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class BedrockClient:
    """Client for interacting with AWS Bedrock models."""
    
    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize the Bedrock client.
        
        Args:
            region_name: AWS region name where Bedrock is available
        """
        self.region_name = region_name
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        self.anthropic_client = AnthropicBedrock()
        self.instructor_client = instructor.from_anthropic(self.anthropic_client)
        
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
            
            # Extract the generated text based on the model provider
            if model_id.startswith("anthropic.claude"):
                generated_text = response_body.get('completion', '')
            else:
                # Default extraction (can be extended for other models)
                generated_text = response_body.get('generated_text', '')
                
            return generated_text
            
        except Exception as e:
            logger.error(f"Error invoking Bedrock model: {e}")
            raise
    
    def get_structured_output(
        self, 
        prompt: str, 
        response_model: Type[BaseModel],
        model_id: str = "anthropic.claude-3-opus-20240229-v1:0",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> BaseModel:
        """
        Get structured output from a Bedrock model using Instructor.
        
        Args:
            prompt: The input prompt for the model
            response_model: The Pydantic model to structure the response
            model_id: The ID of the model to use
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            
        Returns:
            An instance of the provided Pydantic model
        """
        try:
            response = self.instructor_client.messages.create(
                model=model_id,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                response_model=response_model,
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting structured output from Bedrock model: {e}")
            raise
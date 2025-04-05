"""
AWS Bedrock Client for LLM integration.
Provides functionality to interact with AWS Bedrock models.
"""

import json
import logging
import os
from typing import Any, Dict, Optional, Type, Union

import boto3
import instructor
from anthropic import AnthropicBedrock
from dotenv import load_dotenv
from pydantic import BaseModel
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
            region_name=self.region_name,        
            verify = False)
        self.instructor_client = instructor.from_bedrock(self.bedrock_runtime)
        
        # Flag to track if we've already tried to use Bedrock and failed
        self.bedrock_available = True
        
    def _get_available_model(self) -> str:
        """Get an available model that we have permission to invoke."""
        try:
            # Create a bedrock client to list models with SSL verification disabled
            bedrock = boto3.client(
                'bedrock',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
                region_name=self.region_name,
                verify=False  # Disable SSL verification
            )
            
            # List available Claude models
            response = bedrock.list_foundation_models(byProvider="mistral")
            print("Azzo:", response)
            # Try models in order of preference
            preferred_models = [
                "mistral.mistral-7b-instruct-v0:2",
                "anthropic.claude-3-sonnet-20240229-v1:0",
                "anthropic.claude-v2:1",
                "anthropic.claude-v2",
                "anthropic.claude-instant-v1"
            ]
            
            available_models = [m['modelId'] for m in response['modelSummaries']]
            
            for model in preferred_models:
                if model in available_models:
                    return model
                    
            # If none of our preferred models are available, use the first available Claude model
            for model in available_models:
                if model.startswith("anthropic.claude"):
                    return model
                    
            # If we get here, we couldn't find any suitable models
            logger.warning("No suitable Claude models available, using fallback mode")
            self.bedrock_available = False
            return "fallback"
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            # Mark Bedrock as unavailable
            self.bedrock_available = False
            return "fallback"

    def invoke_model(
        self,
        prompt: str,
        model_id: str = "mistral.mistral-7b-instruct-v0:2",
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
        # If we already know Bedrock is unavailable, use fallback immediately
        if not self.bedrock_available or model_id == "fallback":
            logger.info("Using fallback response mode (no Bedrock access)")
            # Generate a simple fallback response
            return f"Fallback response for: {prompt[:50]}..."
            
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
            if "AccessDeniedException" in str(e):
                logger.warning(f"Access denied for model {model_id}, attempting to find available model...")
                # Get an available model and retry
                available_model = self._get_available_model()
                if available_model != model_id and available_model != "fallback":
                    logger.info(f"Retrying with model {available_model}")
                    return self.invoke_model(
                        prompt=prompt,
                        model_id=available_model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        top_k=top_k
                    )
                else:
                    # We're in fallback mode
                    self.bedrock_available = False
                    return f"Fallback response for: {prompt[:50]}..."
            
            logger.error(f"Error invoking Bedrock model: {e}")
            # Use fallback response instead of raising an exception
            self.bedrock_available = False
            return f"Fallback response for: {prompt[:50]}..."
    
    def get_structured_output(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        model_id: str = "mistral.mistral-7b-instruct-v0:2",
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
        # If we already know Bedrock is unavailable, use fallback immediately
        if not self.bedrock_available or model_id == "fallback":
            logger.info("Using fallback structured response mode (no Bedrock access)")
            # Create a fallback response that matches the expected model structure
            if response_model.__name__ == "HypothesisResponse":
                # Create a fallback HypothesisResponse
                from backend.investigation.src.hypothesis_generator import HypothesisResponse, HypothesisCandidate
                from backend.investigation.src.tree import NodeType
                
                return HypothesisResponse(
                    hypotheses=[
                        HypothesisCandidate(
                            title="Fallback Hypothesis",
                            description="This is a fallback hypothesis generated because Bedrock models are not accessible.",
                            type=NodeType.ATTACK_VECTOR,
                            confidence=0.5,
                            evidence=["No Bedrock access"],
                            reasoning="This is a fallback response due to Bedrock access issues."
                        )
                    ],
                    analysis="Analysis could not be generated due to Bedrock access issues."
                )
            else:
                # For unknown models, create a generic instance with default values
                try:
                    return response_model.model_validate({})
                except Exception:
                    # If validation fails, try to create an instance with minimal data
                    try:
                        return response_model()
                    except Exception as e:
                        logger.error(f"Could not create fallback response: {e}")
                        raise ValueError(f"Cannot create fallback for {response_model.__name__}")
        
        try:
            # For Claude models, structure the request properly
            if model_id.startswith("anthropic.claude"):
                # Add system message to guide structured output
                system_prompt = "You are a cybersecurity expert. Provide responses in JSON format matching the specified schema."
                formatted_prompt = f"""
                {prompt}

                Provide your response in the following JSON format:
                {{
                    "hypotheses": [
                        {{
                            "title": "string",
                            "description": "string",
                            "type": "attack_vector|vulnerability|impact|mitigation|root",
                            "confidence": 0.0-1.0,
                            "evidence": ["string"],
                            "reasoning": "string"
                        }}
                    ],
                    "analysis": "string"
                }}
                """
                
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "system": system_prompt,
                    "messages": [
                        {
                            "role": "user",
                            "content": formatted_prompt
                        }
                    ]
                }
                
                response = self.bedrock_runtime.invoke_model(
                    body=json.dumps(body),
                    modelId=model_id,
                    contentType='application/json',
                    accept='application/json'
                )
                
                response_body = json.loads(response['body'].read())
                response_text = response_body.get('completion', '')
                
                # Parse the response text into the provided model
                return response_model.model_validate_json(response_text)
            else:
                # For other models, use instructor client
                response = self.instructor_client.converse(
                    modelId=model_id,
                    messages=[{"role": "user", "content": prompt}],
                    response_model=response_model
                )
            
            return response
            
        except Exception as e:
            if "AccessDeniedException" in str(e):
                logger.warning(f"Access denied for model {model_id}, attempting to find available model...")
                # Get an available model and retry
                available_model = self._get_available_model()
                if available_model != model_id and available_model != "fallback":
                    logger.info(f"Retrying with model {available_model}")
                    return self.get_structured_output(
                        prompt=prompt,
                        response_model=response_model,
                        model_id=available_model,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                else:
                    # We're in fallback mode
                    self.bedrock_available = False
                    # Return a fallback response
                    return self.get_structured_output(
                        prompt=prompt,
                        response_model=response_model,
                        model_id="fallback",
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
            
            logger.error(f"Error getting structured output from Bedrock model: {e}")
            # Use fallback response instead of raising an exception
            self.bedrock_available = False
            return self.get_structured_output(
                prompt=prompt,
                response_model=response_model,
                model_id="fallback",
                max_tokens=max_tokens,
                temperature=temperature
            )
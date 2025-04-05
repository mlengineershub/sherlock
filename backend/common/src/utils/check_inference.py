import boto3
import json
from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()
# List foundation models

# Get AWS credentials from environment variables
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_session_token = os.getenv('AWS_SESSION_TOKEN')
region_name = os.getenv('AWS_DEFAULT_REGION')

bedrock_client = boto3.client(
    'bedrock-runtime',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    aws_session_token=aws_session_token,
    region_name=region_name
)
# Set the model ID, e.g., Mistral Large.
model_id = "mistral.mistral-7b-instruct-v0:2"
# Start a conversation with the user message.
user_message = "Describe the purpose of a 'hello world' program in one line."
conversation = [
    {
        "role": "user",
        "content": [{"text": user_message}],
    }
]

# Send the message to the model, using a basic inference configuration.
response = bedrock_client.converse(
    modelId=model_id,
    messages=conversation,
    inferenceConfig={"maxTokens": 512, "temperature": 0.5, "topP": 0.9},
)

# Extract and print the response text.
response_text = response["output"]["message"]["content"][0]["text"]
print(response_text)

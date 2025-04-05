import boto3

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
    'bedrock',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    aws_session_token=aws_session_token,
    region_name=region_name
)
# List all foundation models
response = bedrock_client.list_foundation_models(byProvider="meta")
# Print the model summaries
print("=== Foundation Models ===")
print("Model ID\tProvider\tName")

# Output the model summaries
for model in response['modelSummaries']:
    print(f"Model ID: {model['modelId']}, Provider: {model['providerName']}, Name: {model['modelName']}")

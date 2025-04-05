import boto3
import re
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogAnalyzer:
    def __init__(self, s3_bucket, s3_key):
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.s3_client = boto3.client('s3')
        self.bedrock = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
            region_name=os.getenv('AWS_DEFAULT_REGION')
        )

    def fetch_logs(self):
        response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=self.s3_key)
        logs = response['Body'].read().decode('utf-8')
        return logs

    def log_parser(self, logs):
        # Simple log parser that splits logs into lines
        return logs.splitlines()

    def regex_pattern_matcher(self, log_line, pattern):
        # Match a regex pattern to a log line
        return re.search(pattern, log_line)

    def detect_log_format(self, header_lines):
        """Detect log format using LLM analysis of header"""
        prompt = f"""Analyze these log header lines and identify the log format:{header_lines}
        Respond ONLY with JSON format:
        {{
            "format": "apache|syslog|json|custom",
            "fields": ["list","of","expected","fields"],
            "regex_pattern": "generated regex pattern with named groups"
        }}"""

        response = self.bedrock.converse(
            modelId="mistral.mistral-7b-instruct-v0:2",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 512, "temperature": 0.2}
        )
        return json.loads(response["output"]["message"]["content"][0]["text"])

    def generate_security_insights(self, extracted_data):
        """Generate security insights from extracted log data using LLM"""
        prompt = f"""Analyze these log entries for security issues:{json.dumps(extracted_data, indent=2)}
        Respond with security insights in this format:
        {{
            "severity": "low|medium|high",
            "potential_threat": "description of potential threat",
            "recommended_action": "specific remediation steps"
        }}"""

        response = self.bedrock.converse(
            modelId="mistral.mistral-7b-instruct-v0:2",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 512, "temperature": 0.2}
        )
        
        # Log the full response for debugging
        logger.info(f"Full LLM response: {response}")

        try:
            # Extract the actual security insights from the LLM response
            security_insights = response["output"]["message"]["content"][0]["text"]
            logger.info(f"Extracted security insights: {security_insights}")
            if not security_insights.strip():
                raise ValueError("LLM response is empty or contains only whitespace")
            return json.loads(security_insights)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {
                "severity": "unknown",
                "potential_threat": "Failed to parse LLM response",
                "recommended_action": "Check the LLM response and ensure it is in the correct JSON format"
            }
        except ValueError as e:
            logger.error(f"LLM response is empty or contains only whitespace: {e}")
            return {
                "severity": "unknown",
                "potential_threat": "LLM response is empty or contains only whitespace",
                "recommended_action": "Check the LLM response and ensure it is not empty"
            }

    def analyze_logs(self):
        logs = self.fetch_logs()
        parsed_logs = self.log_parser(logs)
        
        # Detect log format from first 5 lines
        log_format = self.detect_log_format("\n".join(parsed_logs[:5]))
        
        anomalies = []
        for log_line in parsed_logs:
            match = self.regex_pattern_matcher(log_line, log_format["regex_pattern"])
            if match:
                entry = {
                    "log_format": log_format["format"],
                    "fields": log_format["fields"],
                    "data": match.groupdict()
                }
                
                # Generate security insights
                security_analysis = self.generate_security_insights(entry)
                entry.update(security_analysis)
                
                anomalies.append(entry)

        return anomalies

    def adapt_to_log_type(self, log_type):
        """Adapt the log analyzer to a specific log type"""
        if log_type == "apache":
            self.regex_pattern = r'(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<timestamp>.*?)\] "(?P<request>.*?)" (?P<status>\d{3}) (?P<size>\d+)'
            self.fields = ["ip", "timestamp", "request", "status", "size"]
        elif log_type == "syslog":
            self.regex_pattern = r'(?P<timestamp>\w{3} \d{2} \d{2}:\d{2}:\d{2}) (?P<hostname>\S+) (?P<service>\S+): (?P<message>.*)'
            self.fields = ["timestamp", "hostname", "service", "message"]
        elif log_type == "json":
            self.regex_pattern = r'(?P<json>{.*?})'
            self.fields = ["json"]
        else:
            self.regex_pattern = r'(?P<custom>.*)'
            self.fields = ["custom"]

    def analyze_logs_with_adaptation(self, log_type):
        """Analyze logs with adaptation to a specific log type"""
        self.adapt_to_log_type(log_type)
        logs = self.fetch_logs()
        parsed_logs = self.log_parser(logs)
        
        anomalies = []
        for log_line in parsed_logs:
            match = self.regex_pattern_matcher(log_line, self.regex_pattern)
            if match:
                entry = {
                    "log_format": log_type,
                    "fields": self.fields,
                    "data": match.groupdict()
                }
                
                # Generate security insights
                security_analysis = self.generate_security_insights(entry)
                entry.update(security_analysis)
                
                anomalies.append(entry)

        return anomalies
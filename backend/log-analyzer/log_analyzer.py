import boto3
import logging
from regex_pattern_matcher import RegexPatternMatcher
import os
import json

class LogFormatDetector:
    def __init__(self, bedrock_client):
        self.bedrock = bedrock_client

    def detect_log_format(self, header_lines):
        prompt = f"""Analyze these log header lines and identify the log format:{header_lines}
        Respond ONLY with JSON format:
        {{
            "format": "apache|syslog|json|custom",
            "fields": ["list","of","expected","fields"],
            "regex_pattern": "generated regex pattern with named groups",
            "security_patterns": ["list","of","security","patterns"]
        }}"""

        response = self.bedrock.converse(
            modelId="mistral.mistral-7b-instruct-v0:2",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 512, "temperature": 0.2}
        )
        json_response = response["output"]["message"]["content"][0]["text"]
        print(f"JSON response before decoding: {json_response}")
        try:
            return json.loads(json_response)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            raise

logger = logging.getLogger(__name__)

class LogAnalyzer:
    def __init__(self, s3_bucket, s3_key, batch_size=100):
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.s3_client = boto3.client('s3')
        self.security_patterns = None
        self.bedrock = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
            region_name=os.getenv('AWS_DEFAULT_REGION')
        )
        self.batch_size = batch_size
        self.log_format_detector = LogFormatDetector(self.bedrock)
        self.regex_matcher = RegexPatternMatcher()

    def fetch_logs(self):
        response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=self.s3_key)
        logs = response['Body'].read().decode('utf-8')
        return logs

    def log_parser(self, logs):
        return logs.splitlines()
    
    def prompt_for_security_patterns(self, log_format):
        prompt = f"""Generate a list of security patterns for the following log format: {log_format}
        Respond ONLY with JSON format:
        {{
            "security_patterns": ["list","of","security","patterns"]
        }}"""
        response = self.bedrock.converse(
            modelId="mistral.mistral-7b-instruct-v0:2",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 512, "temperature": 0.2}
        )
        json_response = response["output"]["message"]["content"][0]["text"]
        print(f"JSON response before decoding: {json_response}")
        try:
            return json.loads(json_response)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            raise

    def analyze_logs(self):
        logs = self.fetch_logs()
        parsed_logs = self.log_parser(logs)
        
        # Initial format detection and pattern generation
        log_samples = "\n".join(parsed_logs[:5])
        format_detection = self.log_format_detector.detect_log_format(log_samples)
        log_format = format_detection["format"]
        
        # Filter and analyze using detected patterns
        regex_pattern = format_detection["regex_pattern"]
        critical_entries = []
        
        for entry in parsed_logs:
            if not entry.strip():
                continue
                
            extracted_data = self.regex_matcher.match_pattern(entry, regex_pattern)
            if not extracted_data:
                continue
                
            # Only process logs with security patterns
            if any(pattern.lower() in entry.lower()
                  for pattern in format_detection["security_patterns"]):
                # Create base log entry
                log_entry = {
                    "raw_log": entry,
                    "extracted_data": extracted_data,
                    "metadata": {
                        "format": log_format,
                        "patterns": format_detection["security_patterns"],
                        "fields": format_detection["fields"]
                    }
                }
                
                # Add security analysis
                security_analysis = self.security_insight_generator.generate_security_insights(log_entry)
                if security_analysis.get("severity") in ["high", "medium"]:
                    log_entry.update(security_analysis)
                    critical_entries.append(log_entry)
                    
        return critical_entries

    def analyze_logs_with_patterns(self, log_format, security_patterns):
        logs = self.fetch_logs()
        parsed_logs = self.log_parser(logs)
        security_relevant_logs = self.security_filter.filter_security_relevant_logs(parsed_logs, log_format, security_patterns)
        critical_information = []
        for i in range(0, len(security_relevant_logs), self.batch_size):
            batch = security_relevant_logs[i:i + self.batch_size]
            for entry in batch:
                security_analysis = self.security_insight_generator.generate_security_insights(entry)
                if security_analysis["severity"] in ["high", "medium"]:
                    entry.update(security_analysis)
                    logger.critical(f"Critical Information: {entry}")
                    critical_information.append(entry)
        return critical_information

    def run_analysis(self, log_type):
        """Main analysis pipeline with integrated format detection"""
        critical_information = self.analyze_logs()
        
        logger.info("\n=== Security Analysis Results ===")
        logger.info(f"Found {len(critical_information)} critical events")
        
        # Generate comprehensive recommendations
        recommendations = self.security_insight_generator.generate_summary_recommendations(critical_information)
        
        logger.info("\n=== Security Summary ===")
        logger.info(recommendations.get("summary", "No summary available"))
        
        logger.info("\n=== Critical Issues ===")
        for issue in recommendations.get("critical_issues", []):
            logger.info(f"- {issue}")
            
        logger.info("\n=== Recommended Actions ===")
        for i, action in enumerate(recommendations.get("recommendations", []), 1):
            logger.info(f"{i}. {action}")

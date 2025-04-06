import boto3
import logging
from regex_pattern_matcher import RegexPatternMatcher
import os
import json
import re

logger = logging.getLogger(__name__)

class LogFormatDetector:
    def __init__(self, bedrock_client):
        self.bedrock = bedrock_client

    def detect_log_format(self, header_lines):
        # Define regex patterns for common log formats
        patterns = {
            "apache": {
                "regex": r'^(?P<client_ip>\S+) \S+ \S+ \[(?P<request_time>[^\]]+)\] "(?P<request_method>\S+) (?P<request_url>\S+)[^"]*" (?P<http_status_code>\d{3}) (?P<content_length>\S+)( "(?P<referer>[^"]*)" "(?P<user_agent>[^"]*)")?',
                "fields": ["client_ip", "request_time", "request_method", "request_url", "http_status_code", "content_length", "referer", "user_agent"],
                "security_patterns": []  # Add relevant security patterns if needed
            },
            "syslog": {
                "regex": r'^(?P<timestamp>\S+ \S+ \S+) (?P<hostname>\S+) (?P<service>\S+): (?P<message>.*)$',
                "fields": ["timestamp", "hostname", "service", "message"],
                "security_patterns": []  # Add relevant security patterns if needed
            },
            "json": {
                "regex": r'^{.*}$',
                "fields": [],  # JSON fields will be dynamic
                "security_patterns": []  # Add relevant security patterns if needed
            }
        }

        # Check each pattern against the header lines
        for format_name, details in patterns.items():
            if re.match(details["regex"], header_lines):
                return {
                    "format": format_name,
                    "fields": details["fields"],
                    "regex_pattern": details["regex"],
                    "security_patterns": details["security_patterns"]
                }

        # If no match found, return unknown format
        return {
            "format": "unknown",
            "fields": [],
            "regex_pattern": "",
            "security_patterns": []
        }

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
        self.security_insight_generator = DummySecurityInsightGenerator()

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
        try:
            return json.loads(json_response)
        except json.JSONDecodeError as e:
            logger.error("JSON decoding error: %s", e)
            return None

    def analyze_logs(self, verbose=False):
        logs = self.fetch_logs()
        logger.debug("Fetched logs, snippet: %s", logs[:100] if verbose else "Logs fetched")
        parsed_logs = self.log_parser(logs)
        logger.debug("Parsed logs into %d lines", len(parsed_logs) if verbose else "Logs parsed")
        
        # Initial format detection and pattern generation
        log_samples = "\n".join(parsed_logs[:5])
        logger.debug("Log samples for format detection:\n%s", log_samples if verbose else "Log samples prepared")
        format_detection = self.log_format_detector.detect_log_format(log_samples)
        logger.debug("Format detection result: %s", format_detection if verbose else "Format detected")
        if isinstance(format_detection, dict):
            log_format = format_detection.get("format", "unknown")
        else:
            logger.error("Format detection did not return a dictionary: %s", type(format_detection))
            return []
        
        # Provide defaults if missing
        if "regex_pattern" not in format_detection or not format_detection["regex_pattern"]:
            if log_format == "apache":
                format_detection["regex_pattern"] = r'^(?P<client_ip>\S+) \S+ \S+ \[(?P<request_time>[^\]]+)\] "(?P<request_method>\S+) (?P<request_url>\S+)[^"]*" (?P<http_status_code>\d{3}) (?P<content_length>\S+)( "(?P<referer>[^"]*)" "(?P<user_agent>[^"]*)")?'
            else:
                format_detection["regex_pattern"] = ""
        if "security_patterns" not in format_detection or not format_detection["security_patterns"]:
            sec_patterns_data = self.prompt_for_security_patterns(log_format)
            format_detection["security_patterns"] = sec_patterns_data.get("security_patterns", [])
        
        regex_pattern = format_detection["regex_pattern"]
        critical_entries = []
        
        for entry in parsed_logs:
            logger.debug("Processing log entry: %s", entry if verbose else "Processing entry")
            if not entry.strip():
                continue
            if log_format.lower() == "json":
                try:
                    extracted_data = json.loads(entry)
                except json.JSONDecodeError as e:
                    logger.debug("JSON parsing error: %s", e if verbose else "JSON error")
                    continue
                entry_str = json.dumps(extracted_data)
            else:
                extracted_data = self.regex_matcher.match_pattern(entry, regex_pattern)
                entry_str = entry
            logger.debug("Matching result for entry: %s", extracted_data if verbose else "Entry matched")
            # Ensure that even if no named groups are matched, the entry is still processed for security patterns
            if extracted_data is None:
                extracted_data = {}
                
            # Only process logs with security patterns
            match_found = False
            if log_format.lower() == "json" and isinstance(extracted_data, dict):
                if "level" in extracted_data and extracted_data["level"].lower() in ["error", "critical", "warning"]:
                    match_found = True
            else:
                # Enhance security pattern matching to include SQL injection detection
                sql_injection_patterns = [
                    r"(?i)\b(?:or|and)\b\s+['\"]?[^'\"]+['\"]?\s*=\s*['\"]?[^'\"]+['\"]?",
                    r"(?i)(?:union\s+select|select\s+\*|insert\s+into|update\s+set|delete\s+from)\b"
                ]
                match_found = any(re.search(pattern, entry_str, re.IGNORECASE) for pattern in format_detection["security_patterns"] + sql_injection_patterns)
            if match_found:
                log_entry = {
                    "raw_log": entry,
                    "extracted_data": extracted_data,
                    "metadata": {
                        "format": log_format,
                        "patterns": format_detection["security_patterns"],
                        "fields": format_detection["fields"]
                    }
                }
                
                security_analysis = self.security_insight_generator.generate_security_insights(log_entry)
                if security_analysis.get("severity") in ["high", "medium"]:
                    log_entry.update(security_analysis)
                    critical_entries.append(log_entry)
                    
        # Return both critical entries and their raw log parts
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

    def run_analysis(self, log_type, verbose=False):
        """Main analysis pipeline with integrated format detection"""
        critical_information = self.analyze_logs(verbose)
        
        recommendations = self.security_insight_generator.generate_summary_recommendations(critical_information)
        summary = {
            "critical_events": len(critical_information),
            "events": [
                {
                    "raw": entry["raw_log"],
                    "data": entry["extracted_data"],
                    "metadata": entry["metadata"]
                } for entry in critical_information
            ],
            "summary": recommendations.get("summary", "No summary available"),
            "critical_issues": recommendations.get("critical_issues", []),
            "actions": recommendations.get("recommendations", [])
        }
        logger.info("Security Analysis Summary:\n%s", json.dumps(summary, indent=2))

class DummySecurityInsightGenerator:
    def generate_security_insights(self, log_entry):
        raw_log_lower = log_entry["raw_log"].lower()
        if "error" in raw_log_lower:
            return {
                "severity": "high",
                "potential_threat": "Detected error in log",
                "recommended_action": "Investigate immediately"
            }
        elif re.search(r"(?i)\b(?:or|and)\b\s+['\"]?[^'\"]+['\"]?\s*=\s*['\"]?[^'\"]+['\"]?|(?:union\s+select|select\s+\*|insert\s+into|update\s+set|delete\s+from)\b", raw_log_lower):
            return {
                "severity": "high",
                "potential_threat": "Possible SQL injection detected",
                "recommended_action": "Review query parameters and implement proper input sanitization"
            }
        return {"severity": "low"}
    
    def generate_summary_recommendations(self, critical_entries):
        if not critical_entries:
            return {
                "summary": "No critical events found",
                "recommendations": [],
                "critical_issues": []
            }
        return {
            "summary": "Critical events detected",
            "recommendations": ["Review error logs"],
            "critical_issues": ["Errors found"]
        }

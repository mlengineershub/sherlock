import os
import json
from log_analyzer import LogAnalyzer

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Test data
test_s3_bucket = os.getenv('TEST_S3_BUCKET')
test_s3_key = os.getenv('TEST_S3_KEY')

# Initialize the LogAnalyzer
analyzer = LogAnalyzer(test_s3_bucket, test_s3_key)

# Test with different log types
log_types = ["apache", "syslog", "json", "custom"]

for log_type in log_types:
    print(f"Testing with log type: {log_type}")
    anomalies = analyzer.analyze_logs_with_adaptation(log_type)
    print(json.dumps(anomalies, indent=2))
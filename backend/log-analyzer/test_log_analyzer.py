import unittest
from unittest.mock import patch, MagicMock
import json
from log_analyzer import LogAnalyzer, LogFormatDetector

class TestLogFormatDetector(unittest.TestCase):
    def setUp(self):
        self.bedrock_mock = MagicMock()
        self.detector = LogFormatDetector(self.bedrock_mock)

    def test_detect_log_format_success(self):
        """Test successful format detection"""
        test_log = "2023-01-01T00:00:00.000Z INFO Test"
        expected_response = {
            "format": "custom",
            "fields": ["timestamp", "level", "message"],
            "regex_pattern": r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z) (?P<level>\w+) (?P<message>.+)',
            "security_patterns": ["error"]
        }
        
        self.bedrock_mock.converse.return_value = {
            "output": {
                "message": {
                    "content": [{"text": json.dumps(expected_response)}]
                }
            }
        }
        
        result = self.detector.detect_log_format(test_log)
        self.assertEqual(result, expected_response)

    def test_detect_log_format_failure(self):
        """Test format detection failure"""
        self.bedrock_mock.converse.return_value = {
            "output": {
                "message": {
                    "content": [{"text": "invalid json"}]
                }
            }
        }
        
        with self.assertRaises(json.JSONDecodeError):
            self.detector.detect_log_format("test log")

class TestLogAnalyzer(unittest.TestCase):
    @patch('boto3.client')
    def setUp(self, mock_boto3):
        # Create analyzer with all required mocks
        self.analyzer = LogAnalyzer('test-bucket', 'test-key')
        
        # Setup complete mock environment
        self.analyzer.s3_client = MagicMock()
        self.analyzer.bedrock = MagicMock()
        self.analyzer.log_format_detector = MagicMock()
        self.analyzer.security_insight_generator = MagicMock()
        self.analyzer.regex_matcher = MagicMock()
        
        # Default mock responses
        self.analyzer.s3_client.get_object.return_value = {
            'Body': MagicMock(read=MagicMock(
                return_value=b'2023-01-01T00:00:00.000Z INFO System OK\n'
                            b'2023-01-01T00:00:01.000Z ERROR Connection failed'
            ))
        }

        self.format_detection = {
            "format": "custom",
            "fields": ["timestamp", "level", "message"],
            "regex_pattern": r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z) (?P<level>\w+) (?P<message>.+)',
            "security_patterns": ["error", "failed"]
        }

        self.security_insight = {
            "severity": "high",
            "potential_threat": "Connection failure",
            "recommended_action": "Check network"
        }

        # Configure default mock behaviors
        self.analyzer.log_format_detector.detect_log_format.return_value = self.format_detection
        self.analyzer.security_insight_generator.generate_security_insights.return_value = self.security_insight
        self.analyzer.security_insight_generator.generate_summary_recommendations.return_value = {
            "summary": "Test summary",
            "recommendations": ["action1"],
            "critical_issues": ["issue1"]
        }

    def test_fetch_logs_success(self):
        """Test successful log fetching"""
        logs = self.analyzer.fetch_logs()
        self.assertEqual(logs, 
            '2023-01-01T00:00:00.000Z INFO System OK\n'
            '2023-01-01T00:00:01.000Z ERROR Connection failed')
        self.analyzer.s3_client.get_object.assert_called_once()

    def test_log_parser(self):
        """Test log parsing"""
        parsed = self.analyzer.log_parser('line1\nline2\nline3')
        self.assertEqual(parsed, ['line1', 'line2', 'line3'])

    def test_analyze_logs_flow(self):
        """Test complete analysis workflow"""
        # Setup mocks
        self.analyzer.log_format_detector.detect_log_format = MagicMock(
            return_value=self.format_detection)
        
        # Mock regex matcher to extract log components
        def mock_match(log, pattern):
            parts = log.split()
            return {
                'timestamp': parts[0],
                'level': parts[1],
                'message': ' '.join(parts[2:])
            }
            
        self.analyzer.regex_matcher.match_pattern = MagicMock(
            side_effect=mock_match)
        
        # Mock security insights to only flag ERROR logs
        def mock_generate_insights(entry):
            if entry['extracted_data']['level'] == 'ERROR':
                return self.security_insight
            return {"severity": "low"}
            
        self.analyzer.security_insight_generator.generate_security_insights = MagicMock(
            side_effect=mock_generate_insights)
        
        # Execute analysis
        results = self.analyzer.analyze_logs()
        
        # Verify results
        self.assertEqual(len(results), 1)  # Only ERROR log should be critical
        self.assertEqual(results[0]['extracted_data']['level'], 'ERROR')
        self.assertEqual(results[0]['severity'], 'high')

    def test_run_analysis_output(self):
        """Test formatted output generation"""
        # Setup mocks
        self.analyzer.analyze_logs = MagicMock(return_value=[{
            'raw_log': 'test error log',
            'severity': 'high',
            'potential_threat': 'test threat',
            'recommended_action': 'test action'
        }])
        
        self.analyzer.security_insight_generator.generate_summary_recommendations = MagicMock(
            return_value={
                'summary': 'Test summary',
                'recommendations': ['action1', 'action2'],
                'critical_issues': ['issue1']
            })
        
        # Verify output formatting
        with self.assertLogs() as logs:
            self.analyzer.run_analysis('custom')
            
        self.assertTrue(any("Security Analysis Results" in msg for msg in logs.output))
        self.assertTrue(any("Test summary" in msg for msg in logs.output))
        self.assertTrue(any("action1" in msg for msg in logs.output))

    def test_empty_logs(self):
        """Test empty log file handling"""
        # Setup empty log response
        self.analyzer.s3_client.get_object.return_value = {
            'Body': MagicMock(read=MagicMock(return_value=b''))
        }
        
        # Configure mocks for empty case
        self.analyzer.log_format_detector.detect_log_format.return_value = {
            "format": "empty",
            "fields": [],
            "regex_pattern": "",
            "security_patterns": []
        }
        
        # Mock regex matcher to return None for empty logs
        self.analyzer.regex_matcher.match_pattern.return_value = None
        
        # Execute and verify
        results = self.analyzer.analyze_logs()
        self.assertEqual(results, [])

if __name__ == '__main__':
    unittest.main()

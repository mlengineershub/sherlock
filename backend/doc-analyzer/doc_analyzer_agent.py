import logging
from typing import List, Optional
from datetime import datetime, timedelta
import requests
from pydantic import BaseModel
import sys
from pathlib import Path
import boto3
import os
from dotenv import load_dotenv

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Initialize Bedrock client
load_dotenv()
bedrock_client = boto3.client(
    'bedrock-runtime',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
    region_name=os.getenv('AWS_DEFAULT_REGION')
)
from investigation.src.nvd_client import NVDClient

logger = logging.getLogger(__name__)


class VulnerabilityReport(BaseModel):
    """Security analysis report model"""
    system_summary: str = ""
    keywords: List[str] = []
    vulnerabilities: List[dict] = []
    weak_points: List[str] = []
    recommendations: List[str] = []

class DocAnalyzerAgent:
    def __init__(self):
        self.bedrock = bedrock_client
        self.nvd_client = NVDClient()
        self.keyword_prompt = """Generate 10-15 security-related keywords from this system description:
{description}

Consider these aspects:
- Technologies mentioned
- Security mechanisms described
- Potential attack surfaces
- Compliance requirements

Return 10-15 comma-separated keywords sorted by importance:"""

    def generate_keywords(self, description: str) -> List[str]:
        conversation = [{
            "role": "user",
            "content": [{"text": self.keyword_prompt.format(description=description)}]
        }]
        
        response = self.bedrock.converse(
            modelId="anthropic.claude-3-5-haiku-20241022-v1:0",
            messages=conversation,
            inferenceConfig={"maxTokens": 512, "temperature": 0.5, "topP": 0.9}
        )
        response_text = response["output"]["message"]["content"][0]["text"]
        # Get unique keywords and limit to 15 maximum
        return list({k.strip().lower(): None for k in response_text.split(",") if k.strip()})[:15]

    def fetch_vulnerabilities(self, keywords: List[str]) -> List[dict]:
        vulnerabilities = []
        seen = set()
        for keyword in keywords:
            if keyword.lower() in seen:
                continue
            seen.add(keyword.lower())
            
            try:
                response = self.nvd_client.search_vulnerabilities(
                    keyword=keyword,
                    results_per_page=5  # Get fewer initial results since we'll take top 20 overall
                )
                
                if "error" in response:
                    logger.error(f"NVD API error for {keyword}: {response['error']}")
                    continue
                    
                if "vulnerabilities" in response:
                    vulnerabilities.extend(response["vulnerabilities"])
                               
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {keyword}: {str(e)}")
            except KeyboardInterrupt:
                logger.warning("User interrupted vulnerability search")
                break
        return self._filter_relevant(vulnerabilities, keywords)

    def _filter_relevant(self, vulns: List[dict], keywords: List[str]) -> List[dict]:
        filtered = [
            vuln for vuln in vulns
            if any(kw in vuln['cve']['descriptions'][0]['value'].lower() for kw in keywords)
        ]
        # Sort by CVSS v3 score descending, then take top 20
        filtered.sort(
            key=lambda x: x.get('metrics', {}).get('cvssMetricV3', [{}])[0].get('cvssData', {}).get('baseScore', 0.0),
            reverse=True
        )
        return filtered[:20]

    def generate_summary_prompt(self, system_desc: str, vulns: List[dict],
                              weak_points: List[str], recommendations: List[str]) -> str:
        return f"""Generate a comprehensive vulnerability analysis report based on the following data:

System Description:
{system_desc}

Identified Vulnerabilities:
{vulns}  

Key Security Weak Points:
{weak_points}

Recommended Actions:
{recommendations}

Structure the report with these sections:
1. System Overview - Analyze the described components and architecture
2. Key Findings - Critical vulnerabilities and their potential impact
3. Weak Point Analysis - How vulnerabilities relate to system components
4. Recommendations - Prioritized security improvements

Use markdown formatting and include specific CVE references."""
    
    def analyze_vulnerabilities(self, vulns: List[dict]) -> VulnerabilityReport:
        weak_points = set()
        recommendations = []
        
        for vuln in vulns:
            # Analyze weak points from vulnerability data
            description = vuln['cve']['descriptions'][0]['value'].lower()
            if "configuration" in description:
                weak_points.add("System Configuration")
            if "authentication" in description:
                recommendations.append("Implement multi-factor authentication")
            if "redis" in description:
                weak_points.add("Redis Cache Security")
                
        # Generate detailed report summary
        conversation = [{
            "role": "user",
            "content": [{"text": self.generate_summary_prompt(
                system_desc="Web application using Django 3.2 with PostgreSQL and Redis",
                vulns=vulns,
                weak_points=list(weak_points),
                recommendations=recommendations
            )}]
        }]
        
        response = self.bedrock.converse(
            modelId="anthropic.claude-3-5-haiku-20241022-v1:0",
            messages=conversation,
            inferenceConfig={"maxTokens": 1024, "temperature": 0.7, "topP": 0.9}
        )
        summary = response["output"]["message"]["content"][0]["text"]
        
        return VulnerabilityReport(
            system_summary=summary,
            keywords=[],
            vulnerabilities=vulns,
            weak_points=list(weak_points),
            recommendations=list(set(recommendations))
        )

    def process(self, system_description: str) -> VulnerabilityReport:
        keywords = self.generate_keywords(system_description)
        print(keywords)
        vulnerabilities = self.fetch_vulnerabilities(keywords)
        return self.analyze_vulnerabilities(vulnerabilities)

if __name__ == "__main__":
    agent = DocAnalyzerAgent()
    sample_description = "A web application using Django 3.2 with PostgreSQL backend and Redis caching"
    report = agent.process(sample_description)
    print(report.system_summary)
    print(f"Generated report with {len(report.vulnerabilities)} vulnerabilities found")
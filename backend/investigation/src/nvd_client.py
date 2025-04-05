"""
NVD API Client for fetching vulnerability data.
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any

import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class CVSSv3(BaseModel):
    """CVSS v3 score details."""
    version: str
    vector_string: str
    attack_vector: str
    attack_complexity: str
    privileges_required: str
    user_interaction: str
    scope: str
    confidentiality_impact: str
    integrity_impact: str
    availability_impact: str
    base_score: float
    base_severity: str


class CVSSv2(BaseModel):
    """CVSS v2 score details."""
    version: str
    vector_string: str
    access_vector: str
    access_complexity: str
    authentication: str
    confidentiality_impact: str
    integrity_impact: str
    availability_impact: str
    base_score: float
    severity: str


class CVEReference(BaseModel):
    """Reference for a CVE."""
    url: str
    source: str
    tags: List[str] = Field(default_factory=list)


class CVEDescription(BaseModel):
    """Description of a CVE."""
    lang: str
    value: str


class CVEVulnerability(BaseModel):
    """Vulnerability information from NVD."""
    id: str
    source_identifier: str
    published: str
    last_modified: str
    vuln_status: str
    descriptions: List[CVEDescription]
    references: List[CVEReference] = Field(default_factory=list)
    cvss_v3: Optional[CVSSv3] = None
    cvss_v2: Optional[CVSSv2] = None
    cwe_ids: List[str] = Field(default_factory=list)


class NVDClient:
    """Client for interacting with the NVD API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the NVD API client.
        
        Args:
            api_key: Optional API key for NVD API
        """
        self.base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.api_key = api_key
        self.rate_limit_delay = 6  # Default delay between requests in seconds
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for NVD API requests.
        
        Returns:
            Dictionary of headers
        """
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            headers["apiKey"] = self.api_key
            
        return headers
    
    def search_vulnerabilities(
        self,
        keyword: Optional[str] = None,
        cpe_name: Optional[str] = None,
        cve_id: Optional[str] = None,
        start_index: int = 0,
        results_per_page: int = 20
    ) -> Dict:
        """
        Search for vulnerabilities in the NVD database.
        
        Args:
            keyword: Keyword to search for
            cpe_name: CPE name to search for
            cve_id: Specific CVE ID to search for
            start_index: Starting index for pagination
            results_per_page: Number of results per page
            
        Returns:
            Dictionary containing search results
        """
        # Using Any for the dictionary value type to avoid mypy errors
        params: Dict[str, Any] = {
            "startIndex": start_index,
            "resultsPerPage": results_per_page
        }
        
        if keyword:
            params["keywordSearch"] = keyword
            
        if cpe_name:
            params["cpeName"] = cpe_name
            
        if cve_id:
            params["cveId"] = cve_id
        
        try:
            response = requests.get(
                self.base_url,
                headers=self._get_headers(),
                params=params
            )
            
            # Respect rate limiting
            time.sleep(self.rate_limit_delay)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error searching vulnerabilities: {response.status_code} - {response.text}")
                return {"error": f"API error: {response.status_code}", "vulnerabilities": []}
                
        except Exception as e:
            logger.error(f"Exception searching vulnerabilities: {e}")
            return {"error": str(e), "vulnerabilities": []}
    
    def get_vulnerability(self, cve_id: str) -> Optional[CVEVulnerability]:
        """
        Get details for a specific vulnerability by CVE ID.
        
        Args:
            cve_id: The CVE ID to get details for
            
        Returns:
            CVEVulnerability object or None if not found
        """
        result = self.search_vulnerabilities(cve_id=cve_id)
        
        if "error" in result:
            return None
            
        vulnerabilities = result.get("vulnerabilities", [])
        
        if not vulnerabilities:
            return None
            
        try:
            cve_item = vulnerabilities[0].get("cve", {})
            
            # Extract CVSS v3 data if available
            cvss_v3 = None
            metrics = cve_item.get("metrics", {})
            cvss_v3_data = metrics.get("cvssMetricV31", [])
            if not cvss_v3_data:
                cvss_v3_data = metrics.get("cvssMetricV30", [])
                
            if cvss_v3_data:
                cvss_v3_metric = cvss_v3_data[0].get("cvssData", {})
                cvss_v3 = CVSSv3(
                    version=cvss_v3_metric.get("version", "3.0"),
                    vector_string=cvss_v3_metric.get("vectorString", ""),
                    attack_vector=cvss_v3_metric.get("attackVector", ""),
                    attack_complexity=cvss_v3_metric.get("attackComplexity", ""),
                    privileges_required=cvss_v3_metric.get("privilegesRequired", ""),
                    user_interaction=cvss_v3_metric.get("userInteraction", ""),
                    scope=cvss_v3_metric.get("scope", ""),
                    confidentiality_impact=cvss_v3_metric.get("confidentialityImpact", ""),
                    integrity_impact=cvss_v3_metric.get("integrityImpact", ""),
                    availability_impact=cvss_v3_metric.get("availabilityImpact", ""),
                    base_score=cvss_v3_metric.get("baseScore", 0.0),
                    base_severity=cvss_v3_metric.get("baseSeverity", "")
                )
            
            # Extract CVSS v2 data if available
            cvss_v2 = None
            cvss_v2_data = metrics.get("cvssMetricV2", [])
            if cvss_v2_data:
                cvss_v2_metric = cvss_v2_data[0].get("cvssData", {})
                cvss_v2 = CVSSv2(
                    version=cvss_v2_metric.get("version", "2.0"),
                    vector_string=cvss_v2_metric.get("vectorString", ""),
                    access_vector=cvss_v2_metric.get("accessVector", ""),
                    access_complexity=cvss_v2_metric.get("accessComplexity", ""),
                    authentication=cvss_v2_metric.get("authentication", ""),
                    confidentiality_impact=cvss_v2_metric.get("confidentialityImpact", ""),
                    integrity_impact=cvss_v2_metric.get("integrityImpact", ""),
                    availability_impact=cvss_v2_metric.get("availabilityImpact", ""),
                    base_score=cvss_v2_metric.get("baseScore", 0.0),
                    severity=cvss_v2_metric.get("baseSeverity", "")
                )
            
            # Extract references
            references = []
            for ref in cve_item.get("references", []):
                references.append(CVEReference(
                    url=ref.get("url", ""),
                    source=ref.get("source", ""),
                    tags=ref.get("tags", [])
                ))
            
            # Extract descriptions
            descriptions = []
            for desc in cve_item.get("descriptions", []):
                descriptions.append(CVEDescription(
                    lang=desc.get("lang", ""),
                    value=desc.get("value", "")
                ))
            
            # Extract CWE IDs
            cwe_ids = []
            for weakness in cve_item.get("weaknesses", []):
                for desc in weakness.get("description", []):
                    if desc.get("value", "").startswith("CWE-"):
                        cwe_ids.append(desc.get("value", ""))
            
            return CVEVulnerability(
                id=cve_item.get("id", ""),
                source_identifier=cve_item.get("sourceIdentifier", ""),
                published=cve_item.get("published", ""),
                last_modified=cve_item.get("lastModified", ""),
                vuln_status=cve_item.get("vulnStatus", ""),
                descriptions=descriptions,
                references=references,
                cvss_v3=cvss_v3,
                cvss_v2=cvss_v2,
                cwe_ids=cwe_ids
            )
            
        except Exception as e:
            logger.error(f"Exception parsing vulnerability data: {e}")
            return None
    
    def search_by_keywords(self, keywords: List[str], max_results: int = 10) -> List[CVEVulnerability]:
        """
        Search for vulnerabilities by keywords.
        
        Args:
            keywords: List of keywords to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of CVEVulnerability objects
        """
        keyword_str = " ".join(keywords)
        result = self.search_vulnerabilities(keyword=keyword_str, results_per_page=max_results)
        
        if "error" in result:
            return []
            
        vulnerabilities = []
        for vuln_data in result.get("vulnerabilities", []):
            try:
                cve_item = vuln_data.get("cve", {})
                
                # Extract descriptions
                descriptions = []
                for desc in cve_item.get("descriptions", []):
                    descriptions.append(CVEDescription(
                        lang=desc.get("lang", ""),
                        value=desc.get("value", "")
                    ))
                
                # Create a minimal vulnerability object
                vuln = CVEVulnerability(
                    id=cve_item.get("id", ""),
                    source_identifier=cve_item.get("sourceIdentifier", ""),
                    published=cve_item.get("published", ""),
                    last_modified=cve_item.get("lastModified", ""),
                    vuln_status=cve_item.get("vulnStatus", ""),
                    descriptions=descriptions
                )
                
                vulnerabilities.append(vuln)
                
            except Exception as e:
                logger.error(f"Exception parsing vulnerability in search results: {e}")
                continue
                
        return vulnerabilities[:max_results]
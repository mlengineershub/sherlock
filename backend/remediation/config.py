"""
Configuration for remediation advisory component.
"""

from typing import Dict, Any, List

# Default model configurations
MODEL_CONFIG: Dict[str, Any] = {
    "perspective_generation": {
        "model_id": "anthropic.claude-3-5-haiku-20241022-v1:0",  # Using the same model as investigation agent
        "max_tokens": 300,
        "temperature": 0.7
    },
    "roadmap_generation": {
        "model_id": "anthropic.claude-3-5-haiku-20241022-v1:0",  # Using the same model as investigation agent
        "max_tokens": 1500,
        "temperature": 0.5
    }
}

# Remediation priorities configuration
PRIORITY_CONFIG: Dict[str, Dict[str, Any]] = {
    "immediate": {
        "timeframe": "24-48 hours",
        "color": "#f44336",
        "severity": "critical"
    },
    "short_term": {
        "timeframe": "1 week",
        "color": "#ff9800",
        "severity": "high"
    },
    "medium_term": {
        "timeframe": "1 month",
        "color": "#4caf50",
        "severity": "medium"
    }
}

# UI defaults
UI_CONFIG: Dict[str, Any] = {
    "max_nodes_display": 50,
    "default_perspectives": ["expert", "attacker", "business", "compliance"],
    "roadmap_export_formats": ["json", "markdown", "pdf"]
}

# Validation rules
VALIDATION_RULES: Dict[str, List[str]] = {
    "required_node_fields": ["id", "title", "description", "type", "status"],
    "allowed_status_values": ["confirmed", "plausible", "unverified"]
}

def get_config() -> Dict[str, Any]:
    """Get merged configuration."""
    return {
        "models": MODEL_CONFIG,
        "priorities": PRIORITY_CONFIG,
        "ui": UI_CONFIG,
        "validation": VALIDATION_RULES
    }
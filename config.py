"""
Configuration for US Company Dossier skill.
"""

import os
from typing import List, Dict

# Default configuration values
DEFAULT_CONFIG = {
    # Workspace and dossier root
    "WORKSPACE_ROOT": os.path.expanduser("~/openclaw-workspace"),
    "DOSSIER_ROOT": os.path.join(os.path.expanduser("~/openclaw-workspace"), "dossiers"),
    
    # SEC API configuration
    "SEC_USER_AGENT": "OpenClawResearchBot/1.0 (contact@example.com)",
    "SEC_RPS_LIMIT": 5,  # Requests per second (max 10 per SEC rules)
    "SEC_MAX_CONCURRENCY": 3,
    "SEC_RETRY_MAX": 5,
    "SEC_RETRY_BACKOFF_MAX": 60,
    
    # IR configuration
    "INCLUDE_IR": True,
    "DOMAIN_ALLOWLIST": [
        "sec.gov",
        "data.sec.gov"
    ],
    
    # IR base URL mapping (ticker -> IR homepage)
    "IR_BASE_URL_MAP": {},
    
    # Normalization level
    "NORMALIZE_LEVEL": "light",  # none, light, deep
    
    # Other settings
    "MAX_FILINGS_PER_FORM": 50,
    "FORCE_REBUILD": False,
}

def get_config() -> Dict:
    """Get configuration with environment variable overrides."""
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables if set
    for key in config:
        env_key = f"US_COMPANY_DOSSIER_{key}"
        if env_key in os.environ:
            value = os.environ[env_key]
            # Handle different types
            if key in ["SEC_RPS_LIMIT", "SEC_MAX_CONCURRENCY", "SEC_RETRY_MAX", 
                      "SEC_RETRY_BACKOFF_MAX", "MAX_FILINGS_PER_FORM"]:
                config[key] = int(value)
            elif key in ["INCLUDE_IR", "FORCE_REBUILD"]:
                config[key] = value.lower() in ("true", "1", "yes", "on")
            else:
                config[key] = value
                
    return config
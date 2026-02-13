"""
Configuration for US Company Dossier skill (Simplified - Links Only).
"""

import os
from typing import Dict

# Default configuration values
DEFAULT_CONFIG = {
    # Workspace and dossier root
    "WORKSPACE_ROOT": os.path.expanduser("~/openclaw-workspace"),
    "DOSSIER_ROOT": os.path.join(os.path.expanduser("~/openclaw-workspace"), "dossiers"),
    
    # SEC API configuration
    "SEC_USER_AGENT": "OpenClawResearchBot/1.0 (contact@example.com)",
    "SEC_RPS_LIMIT": 3,  # Requests per second (max 10 per SEC rules)
    
    # Filing settings
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
            if key in ["SEC_RPS_LIMIT", "MAX_FILINGS_PER_FORM"]:
                config[key] = int(value)
            elif key in ["FORCE_REBUILD"]:
                config[key] = value.lower() in ("true", "1", "yes", "on")
            else:
                config[key] = value
    
    # Also check for direct env vars (without prefix)
    if "SEC_USER_AGENT" in os.environ:
        config["SEC_USER_AGENT"] = os.environ["SEC_USER_AGENT"]
    if "SEC_RPS_LIMIT" in os.environ:
        config["SEC_RPS_LIMIT"] = int(os.environ["SEC_RPS_LIMIT"])
    if "DOSSIER_ROOT" in os.environ:
        config["DOSSIER_ROOT"] = os.environ["DOSSIER_ROOT"]
    if "WORKSPACE_ROOT" in os.environ:
        config["WORKSPACE_ROOT"] = os.environ["WORKSPACE_ROOT"]
                
    return config

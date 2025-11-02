"""Configuration loader for MCP Server"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


class ConfigLoader:
    """Load and merge configuration from YAML and environment variables"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize config loader
        
        Args:
            config_path: Path to YAML config file
        """
        self.config_path = Path(config_path)
        
        # Load .env file
        load_dotenv()
        
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from YAML and override with env vars
        
        Returns:
            Configuration dictionary
        """
        # Load YAML config
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Override with environment variables
        config = self._override_with_env(config)
        
        return config
    
    def _override_with_env(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Override config values with environment variables"""
        
        # API Keys
        if 'api_keys' in config:
            config['api_keys']['openai'] = os.getenv('OPENAI_API_KEY', config['api_keys'].get('openai', ''))
            config['api_keys']['gemini'] = os.getenv('GEMINI_API_KEY', config['api_keys'].get('gemini', ''))
            config['api_keys']['crossref_email'] = os.getenv('CROSSREF_EMAIL', config['api_keys'].get('crossref_email', ''))
        
        # Database
        if 'storage' in config and 'database' in config['storage']:
            db_config = config['storage']['database']
            if db_config.get('type') == 'postgresql':
                db_config['host'] = os.getenv('DB_HOST', db_config.get('host', 'localhost'))
                db_config['port'] = int(os.getenv('DB_PORT', db_config.get('port', 5432)))
                db_config['database'] = os.getenv('DB_NAME', db_config.get('database', 'mcp_research'))
                db_config['user'] = os.getenv('DB_USER', db_config.get('user', ''))
                db_config['password'] = os.getenv('DB_PASSWORD', db_config.get('password', ''))
        
        # Notifications
        if 'notifications' in config:
            if 'slack' in config['notifications']:
                config['notifications']['slack']['webhook_url'] = os.getenv(
                    'SLACK_WEBHOOK_URL',
                    config['notifications']['slack'].get('webhook_url', '')
                )
            
            if 'email' in config['notifications']:
                email_config = config['notifications']['email']
                email_config['smtp_host'] = os.getenv('SMTP_HOST', email_config.get('smtp_host', ''))
                email_config['smtp_port'] = int(os.getenv('SMTP_PORT', email_config.get('smtp_port', 587)))
                email_config['username'] = os.getenv('SMTP_USERNAME', email_config.get('username', ''))
                email_config['password'] = os.getenv('SMTP_PASSWORD', email_config.get('password', ''))
        
        # Logging
        if 'logging' in config:
            config['logging']['level'] = os.getenv('LOG_LEVEL', config['logging'].get('level', 'INFO'))
        
        return config

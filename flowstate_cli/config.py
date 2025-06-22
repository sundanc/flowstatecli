import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".flowstate"
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(exist_ok=True)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Return default config
        return {
            "api_base_url": "https://flowstate-cli-production.up.railway.app",
            "auth_token": None,
            "pomo_duration": 25,
            "short_break_duration": 5,
            "long_break_duration": 15,
            "notifications_enabled": True,
            "sound_enabled": True,
            "blocked_sites": [
                "facebook.com",
                "instagram.com", 
                "twitter.com",
                "reddit.com",
                "youtube.com",
                "tiktok.com"
            ]
        }
    
    def _save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self._config, f, indent=2)
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self._config[key] = value
        self._save_config()
    
    def get_auth_token(self) -> Optional[str]:
        """Get authentication token"""
        return self.get("auth_token")
    
    def set_auth_token(self, token: str):
        """Set authentication token"""
        self.set("auth_token", token)
    
    def get_api_base_url(self) -> str:
        """Get API base URL"""
        return self.get("api_base_url", "http://localhost:8000")

# Global config instance
config = Config()

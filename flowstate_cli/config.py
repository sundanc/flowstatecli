import os
import json
import httpx
import asyncio
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
            "mode": "hybrid",  # cloud, local, hybrid
            "api_base_url": "https://flowstate-cli-production.up.railway.app",
            "auto_sync": True,
            "sync_interval": 300,  # seconds
            "auth_token": None,
            "local_user_id": None,
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
    
    async def check_connectivity(self) -> bool:
        """Check if we can connect to the cloud API"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.get_api_base_url()}/")
                return response.status_code == 200
        except Exception:
            return False
    
    def get_mode(self) -> str:
        """Get current operating mode"""
        return self._config.get("mode", "hybrid")
    
    def set_mode(self, mode: str):
        """Set operating mode (cloud, local, hybrid)"""
        if mode not in ["cloud", "local", "hybrid"]:
            raise ValueError("Mode must be 'cloud', 'local', or 'hybrid'")
        self.set("mode", mode)
    
    def is_cloud_mode(self) -> bool:
        """Check if in cloud-only mode"""
        return self.get_mode() == "cloud"
    
    def is_local_mode(self) -> bool:
        """Check if in local-only mode"""
        return self.get_mode() == "local"
    
    def is_hybrid_mode(self) -> bool:
        """Check if in hybrid mode"""
        return self.get_mode() == "hybrid"
    
    async def should_use_cloud(self) -> bool:
        """Determine if cloud should be used based on mode and connectivity"""
        mode = self.get_mode()
        
        if mode == "local":
            return False
        elif mode == "cloud":
            return True
        else:  # hybrid
            return await self.check_connectivity()
    
    def get_auto_sync(self) -> bool:
        """Get auto sync setting"""
        return self._config.get("auto_sync", True)
    
    def set_auto_sync(self, enabled: bool):
        """Set auto sync setting"""
        self.set("auto_sync", enabled)
    
    def get_sync_interval(self) -> int:
        """Get sync interval in seconds"""
        return self._config.get("sync_interval", 300)
    
    def set_sync_interval(self, interval: int):
        """Set sync interval in seconds"""
        self.set("sync_interval", interval)
    
    def get_local_user_id(self) -> Optional[int]:
        """Get local user ID"""
        return self._config.get("local_user_id")
    
    def set_local_user_id(self, user_id: int):
        """Set local user ID"""
        self.set("local_user_id", user_id)

# Global config instance
config = Config()

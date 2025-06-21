import os
import platform
import subprocess
from typing import List
from flowstate_cli.config import config

class FlowStateMode:
    def __init__(self):
        self.hosts_file = self._get_hosts_file_path()
        self.backup_file = os.path.expanduser("~/.flowstate/hosts_backup")
        self.flowstate_marker = "# FlowState blocked sites"
    
    def _get_hosts_file_path(self) -> str:
        """Get the path to the system hosts file"""
        system = platform.system().lower()
        if system == "windows":
            return r"C:\Windows\System32\drivers\etc\hosts"
        else:
            return "/etc/hosts"
    
    def is_active(self) -> bool:
        """Check if flow state mode is currently active"""
        try:
            with open(self.hosts_file, 'r') as f:
                content = f.read()
                return self.flowstate_marker in content
        except (FileNotFoundError, PermissionError):
            return False
    
    def activate(self) -> tuple[bool, str]:
        """Activate flow state mode by blocking distracting sites"""
        if self.is_active():
            return False, "Flow state mode is already active"
        
        try:
            # Create backup of hosts file
            self._backup_hosts_file()
            
            # Get blocked sites from config
            blocked_sites = config.get("blocked_sites", [])
            
            # Add blocked sites to hosts file
            self._add_blocked_sites(blocked_sites)
            
            return True, f"Flow state mode activated. Blocked {len(blocked_sites)} sites."
        
        except PermissionError:
            return False, "Permission denied. Try running with sudo/administrator privileges."
        except Exception as e:
            return False, f"Failed to activate flow state mode: {str(e)}"
    
    def deactivate(self) -> tuple[bool, str]:
        """Deactivate flow state mode by restoring hosts file"""
        if not self.is_active():
            return False, "Flow state mode is not active"
        
        try:
            # Remove blocked sites from hosts file
            self._remove_blocked_sites()
            
            return True, "Flow state mode deactivated. Sites unblocked."
        
        except PermissionError:
            return False, "Permission denied. Try running with sudo/administrator privileges."
        except Exception as e:
            return False, f"Failed to deactivate flow state mode: {str(e)}"
    
    def _backup_hosts_file(self):
        """Create a backup of the hosts file"""
        os.makedirs(os.path.dirname(self.backup_file), exist_ok=True)
        
        with open(self.hosts_file, 'r') as src:
            with open(self.backup_file, 'w') as dst:
                dst.write(src.read())
    
    def _add_blocked_sites(self, sites: List[str]):
        """Add blocked sites to hosts file"""
        blocked_entries = [f"\n{self.flowstate_marker}"]
        
        for site in sites:
            blocked_entries.extend([
                f"127.0.0.1 {site}",
                f"127.0.0.1 www.{site}",
                f"0.0.0.0 {site}",
                f"0.0.0.0 www.{site}"
            ])
        
        blocked_entries.append(f"{self.flowstate_marker} END\n")
        
        with open(self.hosts_file, 'a') as f:
            f.write('\n'.join(blocked_entries))
        
        # Flush DNS cache
        self._flush_dns_cache()
    
    def _remove_blocked_sites(self):
        """Remove blocked sites from hosts file"""
        with open(self.hosts_file, 'r') as f:
            lines = f.readlines()
        
        # Filter out FlowState blocked entries
        filtered_lines = []
        in_flowstate_block = False
        
        for line in lines:
            if self.flowstate_marker in line:
                if line.strip().endswith("END"):
                    in_flowstate_block = False
                else:
                    in_flowstate_block = True
            elif not in_flowstate_block:
                filtered_lines.append(line)
        
        with open(self.hosts_file, 'w') as f:
            f.writelines(filtered_lines)
        
        # Flush DNS cache
        self._flush_dns_cache()
    
    def _flush_dns_cache(self):
        """Flush DNS cache to apply hosts file changes"""
        try:
            system = platform.system().lower()
            if system == "darwin":  # macOS
                subprocess.run(["sudo", "dscacheutil", "-flushcache"], 
                             check=False, capture_output=True)
            elif system == "linux":
                subprocess.run(["sudo", "systemctl", "restart", "systemd-resolved"], 
                             check=False, capture_output=True)
            elif system == "windows":
                subprocess.run(["ipconfig", "/flushdns"], 
                             check=False, capture_output=True)
        except Exception:
            # If flush fails, the hosts file changes will still work eventually
            pass
    
    def get_blocked_sites(self) -> List[str]:
        """Get list of currently blocked sites"""
        return config.get("blocked_sites", [])
    
    def add_blocked_site(self, site: str) -> tuple[bool, str]:
        """Add a site to the blocked list"""
        blocked_sites = config.get("blocked_sites", [])
        
        if site in blocked_sites:
            return False, f"{site} is already in the blocked list"
        
        blocked_sites.append(site)
        config.set("blocked_sites", blocked_sites)
        
        # If mode is active, update hosts file
        if self.is_active():
            self.deactivate()
            self.activate()
        
        return True, f"Added {site} to blocked sites"
    
    def remove_blocked_site(self, site: str) -> tuple[bool, str]:
        """Remove a site from the blocked list"""
        blocked_sites = config.get("blocked_sites", [])
        
        if site not in blocked_sites:
            return False, f"{site} is not in the blocked list"
        
        blocked_sites.remove(site)
        config.set("blocked_sites", blocked_sites)
        
        # If mode is active, update hosts file
        if self.is_active():
            self.deactivate()
            self.activate()
        
        return True, f"Removed {site} from blocked sites"

# Global flow state mode instance
flow_mode = FlowStateMode()

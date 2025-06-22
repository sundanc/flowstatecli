import httpx
from typing import List, Dict, Any, Optional
from flowstate_cli.config import config

class FlowStateAPI:
    def __init__(self):
        self.base_url = config.get_api_base_url()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        # Refresh auth header on each request to pick up new tokens
        headers = {}
        token = config.get_auth_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        # Merge with any additional headers
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            kwargs["headers"] = headers
        else:
            kwargs["headers"] = headers
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                **kwargs
            )
            
            if response.status_code == 401:
                raise Exception("Authentication required. Run 'flowstate auth login' first.")
            
            response.raise_for_status()
            return response.json()
    
    # Auth methods
    async def send_magic_link(self, email: str) -> bool:
        """Send magic link for authentication"""
        try:
            await self._request("POST", "/auth/magic-link", json={"email": email})
            return True
        except Exception as e:
            print(f"Error sending magic link: {e}")
            return False
    
    # User methods
    async def get_current_user(self) -> Dict[str, Any]:
        """Get current user information"""
        return await self._request("GET", "/users/me")
    
    async def update_user_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update user settings"""
        return await self._request("PUT", "/users/me", json=settings)
    
    # Task methods
    async def get_tasks(self, include_completed: bool = False) -> List[Dict[str, Any]]:
        """Get user's tasks"""
        params = {"include_completed": include_completed}
        return await self._request("GET", "/tasks", params=params)
    
    async def create_task(self, description: str) -> Dict[str, Any]:
        """Create a new task"""
        data = {"description": description}
        return await self._request("POST", "/tasks", json=data)
    
    async def start_task(self, task_id: int) -> Dict[str, Any]:
        """Set task as active"""
        return await self._request("PUT", f"/tasks/{task_id}/start")
    
    async def complete_task(self, task_id: int) -> Dict[str, Any]:
        """Mark task as completed"""
        return await self._request("PUT", f"/tasks/{task_id}/complete")
    
    async def delete_task(self, task_id: int) -> Dict[str, Any]:
        """Delete a task"""
        return await self._request("DELETE", f"/tasks/{task_id}")
    
    async def get_active_task(self) -> Optional[Dict[str, Any]]:
        """Get currently active task"""
        try:
            return await self._request("GET", "/tasks/active")
        except Exception:
            return None
    
    # Pomodoro methods
    async def start_pomodoro(self, task_id: Optional[int], session_type: str, duration: int) -> Dict[str, Any]:
        """Start a pomodoro session"""
        data = {
            "task_id": task_id,
            "session_type": session_type,
            "duration_minutes": duration
        }
        return await self._request("POST", "/pomodoros", json=data)
    
    async def complete_pomodoro(self, pomodoro_id: int) -> Dict[str, Any]:
        """Complete a pomodoro session"""
        return await self._request("PUT", f"/pomodoros/{pomodoro_id}/complete")
    
    # Analytics methods
    async def get_analytics(self) -> Dict[str, Any]:
        """Get analytics summary"""
        return await self._request("GET", "/analytics/summary")
    
    # Billing methods
    async def create_checkout_session(self) -> Dict[str, Any]:
        """Create Stripe checkout session"""
        return await self._request("POST", "/billing/create-checkout-session")

# Global API instance
api = FlowStateAPI()

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from flowstate_cli.config import config
from flowstate_cli.local_db import LocalUser, LocalTask, LocalPomodoro, SyncQueue, get_local_db_session
from flowstate_cli.api import FlowStateAPI
from flowstate_cli.auth import local_auth

logger = logging.getLogger(__name__)

class SyncEngine:
    def __init__(self):
        self.api = FlowStateAPI()
    
    async def sync_all(self) -> Dict[str, Any]:
        """Perform full bidirectional sync - simplified version"""
        if config.is_local_mode():
            return {"error": "Cannot sync in local-only mode"}
        
        if not await config.check_connectivity():
            return {"error": "No internet connection"}
        
        if not config.get_auth_token():
            return {"error": "Not authenticated with cloud"}
        
        try:
            results = {
                "tasks_synced": 0,
                "pomodoros_synced": 0,
                "errors": []
            }
            
            # Simple sync: push local changes to cloud
            await self._sync_tasks_to_cloud(results)
            await self._sync_pomodoros_to_cloud(results)
            
            return results
        
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return {"error": str(e)}
    
    async def _sync_tasks_to_cloud(self, results: Dict[str, Any]):
        """Push local tasks that need sync to cloud"""
        try:
            with next(get_local_db_session()) as db:
                # Get local tasks that need sync
                local_tasks = db.query(LocalTask).filter(
                    LocalTask.user_id == config.get_local_user_id(),
                    LocalTask.needs_sync == True
                ).all()
                
                for local_task in local_tasks:
                    try:
                        if not local_task.cloud_task_id:
                            # Create new cloud task
                            cloud_task = await self.api.create_task(local_task.description)
                            local_task.cloud_task_id = cloud_task['id']
                        
                        # Mark as synced
                        local_task.needs_sync = False
                        local_task.last_synced_at = datetime.utcnow()
                        results["tasks_synced"] += 1
                    
                    except Exception as e:
                        results["errors"].append(f"Task sync error (ID {local_task.id}): {e}")
                
                db.commit()
        
        except Exception as e:
            results["errors"].append(f"Tasks sync error: {e}")
    
    async def _sync_pomodoros_to_cloud(self, results: Dict[str, Any]):
        """Push local pomodoros that need sync to cloud"""
        try:
            with next(get_local_db_session()) as db:
                # Get local pomodoros that need sync
                local_pomodoros = db.query(LocalPomodoro).filter(
                    LocalPomodoro.user_id == config.get_local_user_id(),
                    LocalPomodoro.needs_sync == True
                ).all()
                
                for local_pom in local_pomodoros:
                    try:
                        if not local_pom.cloud_pomodoro_id:
                            # Create new cloud pomodoro
                            cloud_pom = await self.api.start_pomodoro(
                                local_pom.task_id, 
                                local_pom.session_type, 
                                local_pom.duration_minutes
                            )
                            local_pom.cloud_pomodoro_id = cloud_pom['id']
                            
                            if local_pom.completed:
                                await self.api.complete_pomodoro(cloud_pom['id'])
                        
                        # Mark as synced
                        local_pom.needs_sync = False
                        local_pom.last_synced_at = datetime.utcnow()
                        results["pomodoros_synced"] += 1
                    
                    except Exception as e:
                        results["errors"].append(f"Pomodoro sync error (ID {local_pom.id}): {e}")
                
                db.commit()
        
        except Exception as e:
            results["errors"].append(f"Pomodoros sync error: {e}")

# Global sync engine instance
sync_engine = SyncEngine()

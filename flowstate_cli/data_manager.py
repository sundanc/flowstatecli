from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from flowstate_cli.config import config
from flowstate_cli.local_db import LocalUser, LocalTask, LocalPomodoro, get_local_db_session
from flowstate_cli.api import FlowStateAPI
from flowstate_cli.auth import local_auth

class DataManager(ABC):
    """Abstract base class for data management"""
    
    @abstractmethod
    async def get_current_user(self) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_tasks(self, include_completed: bool = False) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def create_task(self, description: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def start_task(self, task_id: int) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def complete_task(self, task_id: int) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def delete_task(self, task_id: int) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def get_active_task(self) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def start_pomodoro(self, task_id: Optional[int], session_type: str, duration: int) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def complete_pomodoro(self, pomodoro_id: int) -> Dict[str, Any]:
        pass

class LocalDataManager(DataManager):
    """Local SQLite data manager"""
    
    def __init__(self):
        self.current_user_id = local_auth.get_local_user_id()
    
    def _ensure_user(self) -> int:
        """Ensure we have a local user and return user ID"""
        if not self.current_user_id:
            # Create default local user with simple username
            import getpass
            default_username = getpass.getuser()  # Get system username
            user = local_auth.create_local_user(default_username)
            self.current_user_id = user.id
            config.set_local_user_id(user.id)
        return self.current_user_id
    
    async def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current local user"""
        user_id = self._ensure_user()
        with next(get_local_db_session()) as db:
            user = db.query(LocalUser).filter(LocalUser.id == user_id).first()
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_pro": user.is_pro,
                    "pomo_duration": user.pomo_duration,
                    "short_break_duration": user.short_break_duration,
                    "long_break_duration": user.long_break_duration,
                    "notifications_enabled": user.notifications_enabled
                }
            return None
            return None
    
    async def get_tasks(self, include_completed: bool = False) -> List[Dict[str, Any]]:
        """Get user's tasks from local database"""
        user_id = self._ensure_user()
        with next(get_local_db_session()) as db:
            query = db.query(LocalTask).filter(LocalTask.user_id == user_id)
            if not include_completed:
                query = query.filter(LocalTask.is_completed == False)
            
            tasks = query.order_by(LocalTask.created_at.desc()).all()
            return [self._task_to_dict(task) for task in tasks]
    
    async def create_task(self, description: str) -> Dict[str, Any]:
        """Create a new task in local database"""
        user_id = self._ensure_user()
        with next(get_local_db_session()) as db:
            task = LocalTask(
                user_id=user_id,
                description=description,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                needs_sync=True
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            return self._task_to_dict(task)
    
    async def start_task(self, task_id: int) -> Dict[str, Any]:
        """Set task as active in local database"""
        user_id = self._ensure_user()
        with next(get_local_db_session()) as db:
            # Deactivate all other tasks
            db.query(LocalTask).filter(
                LocalTask.user_id == user_id,
                LocalTask.is_active == True
            ).update({"is_active": False, "updated_at": datetime.utcnow(), "needs_sync": True})
            
            # Activate the specified task
            task = db.query(LocalTask).filter(
                LocalTask.id == task_id,
                LocalTask.user_id == user_id
            ).first()
            
            if not task:
                raise ValueError("Task not found")
            
            task.is_active = True
            task.updated_at = datetime.utcnow()
            task.needs_sync = True
            db.commit()
            db.refresh(task)
            return self._task_to_dict(task)
    
    async def complete_task(self, task_id: int) -> Dict[str, Any]:
        """Mark task as completed in local database"""
        user_id = self._ensure_user()
        with next(get_local_db_session()) as db:
            task = db.query(LocalTask).filter(
                LocalTask.id == task_id,
                LocalTask.user_id == user_id
            ).first()
            
            if not task:
                raise ValueError("Task not found")
            
            task.is_completed = True
            task.is_active = False
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            task.needs_sync = True
            db.commit()
            db.refresh(task)
            return self._task_to_dict(task)
    
    async def delete_task(self, task_id: int) -> Dict[str, Any]:
        """Delete a task from local database"""
        user_id = self._ensure_user()
        with next(get_local_db_session()) as db:
            task = db.query(LocalTask).filter(
                LocalTask.id == task_id,
                LocalTask.user_id == user_id
            ).first()
            
            if not task:
                raise ValueError("Task not found")
            
            task_dict = self._task_to_dict(task)
            db.delete(task)
            db.commit()
            return task_dict
    
    async def get_active_task(self) -> Optional[Dict[str, Any]]:
        """Get currently active task from local database"""
        user_id = self._ensure_user()
        with next(get_local_db_session()) as db:
            task = db.query(LocalTask).filter(
                LocalTask.user_id == user_id,
                LocalTask.is_active == True
            ).first()
            
            return self._task_to_dict(task) if task else None
    
    async def start_pomodoro(self, task_id: Optional[int], session_type: str, duration: int) -> Dict[str, Any]:
        """Start a pomodoro session in local database"""
        user_id = self._ensure_user()
        with next(get_local_db_session()) as db:
            pomodoro = LocalPomodoro(
                user_id=user_id,
                task_id=task_id,
                session_type=session_type,
                duration_minutes=duration,
                started_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                needs_sync=True
            )
            db.add(pomodoro)
            db.commit()
            db.refresh(pomodoro)
            return self._pomodoro_to_dict(pomodoro)
    
    async def complete_pomodoro(self, pomodoro_id: int) -> Dict[str, Any]:
        """Complete a pomodoro session in local database"""
        user_id = self._ensure_user()
        with next(get_local_db_session()) as db:
            pomodoro = db.query(LocalPomodoro).filter(
                LocalPomodoro.id == pomodoro_id,
                LocalPomodoro.user_id == user_id
            ).first()
            
            if not pomodoro:
                raise ValueError("Pomodoro not found")
            
            pomodoro.completed = True
            pomodoro.completed_at = datetime.utcnow()
            pomodoro.updated_at = datetime.utcnow()
            pomodoro.needs_sync = True
            db.commit()
            db.refresh(pomodoro)
            return self._pomodoro_to_dict(pomodoro)
    
    def _task_to_dict(self, task: LocalTask) -> Dict[str, Any]:
        """Convert LocalTask to dictionary"""
        return {
            "id": task.id,
            "description": task.description,
            "is_completed": task.is_completed,
            "is_active": task.is_active,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }
    
    def _pomodoro_to_dict(self, pomodoro: LocalPomodoro) -> Dict[str, Any]:
        """Convert LocalPomodoro to dictionary"""
        return {
            "id": pomodoro.id,
            "task_id": pomodoro.task_id,
            "session_type": pomodoro.session_type,
            "duration_minutes": pomodoro.duration_minutes,
            "completed": pomodoro.completed,
            "started_at": pomodoro.started_at.isoformat() if pomodoro.started_at else None,
            "completed_at": pomodoro.completed_at.isoformat() if pomodoro.completed_at else None
        }

class CloudDataManager(DataManager):
    """Cloud API data manager"""
    
    def __init__(self):
        self.api = FlowStateAPI()
    
    async def get_current_user(self) -> Optional[Dict[str, Any]]:
        return await self.api.get_current_user()
    
    async def get_tasks(self, include_completed: bool = False) -> List[Dict[str, Any]]:
        return await self.api.get_tasks(include_completed)
    
    async def create_task(self, description: str) -> Dict[str, Any]:
        return await self.api.create_task(description)
    
    async def start_task(self, task_id: int) -> Dict[str, Any]:
        return await self.api.start_task(task_id)
    
    async def complete_task(self, task_id: int) -> Dict[str, Any]:
        return await self.api.complete_task(task_id)
    
    async def delete_task(self, task_id: int) -> Dict[str, Any]:
        return await self.api.delete_task(task_id)
    
    async def get_active_task(self) -> Optional[Dict[str, Any]]:
        return await self.api.get_active_task()
    
    async def start_pomodoro(self, task_id: Optional[int], session_type: str, duration: int) -> Dict[str, Any]:
        return await self.api.start_pomodoro(task_id, session_type, duration)
    
    async def complete_pomodoro(self, pomodoro_id: int) -> Dict[str, Any]:
        return await self.api.complete_pomodoro(pomodoro_id)

class HybridDataManager(DataManager):
    """Hybrid data manager with cloud fallback to local"""
    
    def __init__(self):
        self.cloud_manager = CloudDataManager()
        self.local_manager = LocalDataManager()
    
    async def _try_cloud_fallback_local(self, operation, *args, **kwargs):
        """Try cloud operation first, fallback to local on failure"""
        if await config.should_use_cloud():
            try:
                return await getattr(self.cloud_manager, operation)(*args, **kwargs)
            except Exception:
                # Cloud failed, fallback to local
                pass
        
        # Use local
        return await getattr(self.local_manager, operation)(*args, **kwargs)
    
    async def get_current_user(self) -> Optional[Dict[str, Any]]:
        return await self._try_cloud_fallback_local('get_current_user')
    
    async def get_tasks(self, include_completed: bool = False) -> List[Dict[str, Any]]:
        return await self._try_cloud_fallback_local('get_tasks', include_completed)
    
    async def create_task(self, description: str) -> Dict[str, Any]:
        return await self._try_cloud_fallback_local('create_task', description)
    
    async def start_task(self, task_id: int) -> Dict[str, Any]:
        return await self._try_cloud_fallback_local('start_task', task_id)
    
    async def complete_task(self, task_id: int) -> Dict[str, Any]:
        return await self._try_cloud_fallback_local('complete_task', task_id)
    
    async def delete_task(self, task_id: int) -> Dict[str, Any]:
        return await self._try_cloud_fallback_local('delete_task', task_id)
    
    async def get_active_task(self) -> Optional[Dict[str, Any]]:
        return await self._try_cloud_fallback_local('get_active_task')
    
    async def start_pomodoro(self, task_id: Optional[int], session_type: str, duration: int) -> Dict[str, Any]:
        return await self._try_cloud_fallback_local('start_pomodoro', task_id, session_type, duration)
    
    async def complete_pomodoro(self, pomodoro_id: int) -> Dict[str, Any]:
        return await self._try_cloud_fallback_local('complete_pomodoro', pomodoro_id)

# Factory function to get appropriate data manager
def get_data_manager() -> DataManager:
    """Get data manager based on current mode"""
    mode = config.get_mode()
    
    if mode == "cloud":
        return CloudDataManager()
    elif mode == "local":
        return LocalDataManager()
    else:  # hybrid
        return HybridDataManager()

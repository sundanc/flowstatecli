import os
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional, List, Dict, Any

Base = declarative_base()

class LocalUser(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)  # Changed from email to username
    email = Column(String, nullable=True)  # Optional email for cloud sync
    password_hash = Column(String, nullable=True)  # For local auth
    cloud_user_id = Column(String, nullable=True)  # Link to cloud user
    is_pro = Column(Boolean, default=False)
    pomo_duration = Column(Integer, default=25)
    short_break_duration = Column(Integer, default=5)
    long_break_duration = Column(Integer, default=15)
    notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = Column(DateTime, nullable=True)
    
    tasks = relationship("LocalTask", back_populates="user", cascade="all, delete-orphan")
    pomodoros = relationship("LocalPomodoro", back_populates="user", cascade="all, delete-orphan")

class LocalTask(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    cloud_task_id = Column(Integer, nullable=True)  # Link to cloud task
    description = Column(Text)
    is_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = Column(DateTime, nullable=True)
    needs_sync = Column(Boolean, default=True)  # Flag for pending sync
    
    user = relationship("LocalUser", back_populates="tasks")

class LocalPomodoro(Base):
    __tablename__ = "pomodoros"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    cloud_pomodoro_id = Column(Integer, nullable=True)  # Link to cloud pomodoro
    session_type = Column(String)  # 'focus', 'short_break', 'long_break'
    duration_minutes = Column(Integer)
    completed = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = Column(DateTime, nullable=True)
    needs_sync = Column(Boolean, default=True)
    
    user = relationship("LocalUser", back_populates="pomodoros")

class SyncQueue(Base):
    __tablename__ = "sync_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String)  # 'user', 'task', 'pomodoro'
    entity_id = Column(Integer)
    operation = Column(String)  # 'create', 'update', 'delete'
    data = Column(Text)  # JSON data
    created_at = Column(DateTime, default=datetime.utcnow)
    attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

class LocalDatabase:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            config_dir = Path.home() / ".flowstate"
            config_dir.mkdir(exist_ok=True)
            db_path = str(config_dir / "local.db")
        
        self.db_path = db_path
        # Use simple SQLite connection
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()

# Global instance
local_db = LocalDatabase()

def get_local_db_session():
    """Dependency to get local database session"""
    session = local_db.get_session()
    try:
        yield session
    finally:
        session.close()

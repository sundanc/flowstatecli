import os
import jwt
import bcrypt
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from flowstate_cli.local_db import LocalUser, get_local_db_session

class LocalAuth:
    def __init__(self):
        self.config_dir = Path.home() / ".flowstate"
        self.auth_file = self.config_dir / "auth.json"
        self.config_dir.mkdir(exist_ok=True)
        
        # JWT secret key (generated once and stored locally)
        self.secret_key = self._get_or_create_secret_key()
    
    def _get_or_create_secret_key(self) -> str:
        """Get or create JWT secret key"""
        secret_file = self.config_dir / "jwt_secret"
        
        if secret_file.exists():
            return secret_file.read_text().strip()
        else:
            # Generate new secret key
            import secrets
            secret = secrets.token_urlsafe(32)
            secret_file.write_text(secret)
            return secret
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_local_user(self, username: str, password: Optional[str] = None, email: Optional[str] = None) -> LocalUser:
        """Create local user account with username"""
        with next(get_local_db_session()) as db:
            # Check if user already exists
            existing_user = db.query(LocalUser).filter(LocalUser.username == username).first()
            if existing_user:
                return existing_user
            
            # Create new user
            user = LocalUser(
                username=username,
                email=email,
                password_hash=self.hash_password(password) if password else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
    
    def authenticate_local_user(self, username: str, password: str) -> Optional[LocalUser]:
        """Authenticate local user with username/password"""
        with next(get_local_db_session()) as db:
            user = db.query(LocalUser).filter(LocalUser.username == username).first()
            if user and user.password_hash and self.verify_password(password, user.password_hash):
                return user
            return None
    
    def generate_local_token(self, user: LocalUser) -> str:
        """Generate JWT token for local user"""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(days=30),
            'iat': datetime.utcnow(),
            'type': 'local'
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_local_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_current_local_user(self, token: str) -> Optional[LocalUser]:
        """Get current user from token"""
        payload = self.verify_local_token(token)
        if not payload:
            return None
        
        with next(get_local_db_session()) as db:
            return db.query(LocalUser).filter(LocalUser.id == payload['user_id']).first()
    
    def save_auth_state(self, auth_data: Dict[str, Any]):
        """Save authentication state to file"""
        with open(self.auth_file, 'w') as f:
            json.dump(auth_data, f, indent=2)
    
    def load_auth_state(self) -> Dict[str, Any]:
        """Load authentication state from file"""
        if self.auth_file.exists():
            try:
                with open(self.auth_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}
    
    def clear_auth_state(self):
        """Clear authentication state"""
        if self.auth_file.exists():
            self.auth_file.unlink()
    
    def is_authenticated_locally(self) -> bool:
        """Check if user is authenticated locally"""
        auth_state = self.load_auth_state()
        token = auth_state.get('local_token')
        if not token:
            return False
        
        payload = self.verify_local_token(token)
        return payload is not None
    
    def get_local_user_id(self) -> Optional[int]:
        """Get current local user ID"""
        auth_state = self.load_auth_state()
        token = auth_state.get('local_token')
        if not token:
            return None
        
        payload = self.verify_local_token(token)
        return payload.get('user_id') if payload else None

# Global instance
local_auth = LocalAuth()

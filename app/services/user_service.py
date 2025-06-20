from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from .base_service import BaseService


class UserService(BaseService):
    """
    Service for user-related operations
    """
    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        """
        Get user by phone number
        """
        return self.db.query(User).filter(User.phone == phone_number).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email
        """
        if not email:
            return None
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, phone_number: str) -> User:
        """
        Create a new user with phone number
        """
        user = User(
            phone=phone_number,
            is_active=True,
            is_verified=False
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def verify_user(self, user: User) -> User:
        """
        Mark user as verified
        """
        user.is_verified = True
        user.verified_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_last_login(self, user: User) -> User:
        """
        Update user's last login timestamp
        """
        user.last_login = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_user(self, user: User, user_in: UserUpdate) -> User:
        """
        Update user data
        """
        update_data = user_in.dict(exclude_unset=True)
        
        # Handle password hashing if provided
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def set_user_email(self, user: User, email: str) -> User:
        """
        Set user's email
        """
        user.email = email
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def deactivate_user(self, user: User) -> User:
        """
        Deactivate a user
        """
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def reactivate_user(self, user: User) -> User:
        """
        Reactivate a user
        """
        user.is_active = True
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all active users
        """
        return self.db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
    
    def get_users_by_subscription_type(self, subscription_type: str, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get users by subscription type
        """
        return self.db.query(User).filter(User.subscription_type == subscription_type).offset(skip).limit(limit).all()
    
    def update_subscription(self, user: User, subscription_type: str, expires_at: datetime) -> User:
        """
        Update user's subscription
        """
        user.subscription_type = subscription_type
        user.subscription_expires_at = expires_at
        self.db.commit()
        self.db.refresh(user)
        return user

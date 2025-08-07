from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi import status as http_status

from app.core.security import utc_now
from app.models.user import User
from app.schemas.user import UserUpdate

from .base_service import BaseService


class UserService(BaseService):
    """
    Service for user-related operations
    """

    def get_user_by_id(self, user_id: UUID, raise_exc: bool = True) -> Optional[User]:
        """
        Get user by ID
        """
        user = self.session.get(User, user_id)
        if not user and raise_exc:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"no User with id: {user_id}",
            )
        return user

    def get_user_by_phone(self, phone_number: str, raise_exc: bool = True) -> Optional[User]:
        """
        Get user by phone number
        """
        user = self.session.query(User).filter(User.phone_number == phone_number).first()
        if not user and raise_exc:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"no User with Phone Number: {phone_number}",
            )
        return user

    def get_user_by_email(self, email: str, raise_exc: bool = True) -> Optional[User]:
        """
        Get user by email
        """
        user = self.session.query(User).filter(User.email == email).first()
        if not user and raise_exc:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"no User with Email: {email}",
            )
        return user

    def create_user(self, phone_number: str) -> User:
        """
        Create a new user with phone number
        """
        user = User(phone=phone_number, is_active=True, is_verified=False)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def verify_user(self, user: User) -> User:
        """
        Mark user as verified
        """
        user.is_verified = True
        user.verified_at = utc_now()
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_last_login(self, user: User) -> User:
        """
        Update user's last login timestamp
        """
        user.last_login = utc_now()
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_user(self, user: User, user_in: UserUpdate) -> User:
        """
        Update user data
        """
        update_data = user_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        self.session.commit()
        self.session.refresh(user)
        return user

    def set_user_email(self, user: User, email: str) -> User:
        """
        Set user's email
        """
        user.email = email
        self.session.commit()
        self.session.refresh(user)
        return user

    def deactivate_user(self, user: User) -> User:
        """
        Deactivate a user
        """
        user.is_active = False
        self.session.commit()
        self.session.refresh(user)
        return user

    def reactivate_user(self, user: User) -> User:
        """
        Reactivate a user
        """
        user.is_active = True
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all active users
        """
        return (
            self.session.query(User)
            .filter(User.is_active.is_(True))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_users_by_subscription_type(
        self, subscription_type: str, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """
        Get users by subscription type
        """
        return (
            self.session.query(User)
            .filter(User.subscription_type == subscription_type)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_subscription(self, user: User, subscription_type: str, expires_at: datetime) -> User:
        """
        Update user's subscription
        """
        user.subscription_type = subscription_type
        user.subscription_expires_at = expires_at
        self.session.commit()
        self.session.refresh(user)
        return user

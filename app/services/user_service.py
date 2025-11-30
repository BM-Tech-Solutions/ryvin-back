from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import utc_now
from app.models.token import RefreshToken
from app.models.user import User
from app.schemas.user import UserUpdate

from .base_service import BaseService
from .twilio_service import TwilioService


class UserService(BaseService):
    """
    Service for user-related operations
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.session = db

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID
        """
        return self.session.get(User, user_id)

    def get_user_or_404(self, user_id: UUID) -> User:
        user = self.session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User Not Found")
        return user

    def get_user_by_phone(self, phone_region: str, phone_number: str) -> Optional[User]:
        """
        Get user by phone number
        """
        return (
            self.session.query(User)
            .filter(User.phone_region == phone_region, User.phone_number == phone_number)
            .first()
        )

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email
        """
        if not email:
            return None
        return self.session.query(User).filter(User.email == email).first()

    def create_user(self, phone_region: str, phone_number: str) -> User:
        """
        Create a new user with phone number
        """
        user = User(
            phone_region=phone_region,
            phone_number=phone_number,
            is_active=True,
            is_verified=False,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        self.create_twilio_user(user)
        return user

    def create_twilio_user(self, user: User):
        twilio_service = TwilioService()
        twilio_user = twilio_service.get_user(str(user.id))
        if not twilio_user:
            twilio_user = twilio_service.create_user(str(user.id))
        return twilio_user

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
        user.deactivated_at = utc_now()
        self.session.commit()
        self.session.refresh(user)
        self.revoke_all_tokens(user_id=user.id)
        return user

    def reactivate_user(self, user: User) -> User:
        """
        Reactivate a user
        """
        user.is_active = True
        user.deactivated_at = None
        self.session.commit()
        self.session.refresh(user)
        return user

    def delete_user(self, user: User) -> User:
        """
        Soft Delete a User
        """
        user.is_deleted = True
        user.deleted_at = utc_now()
        user.is_active = False
        user.deactivated_at = utc_now()

        self.session.commit()
        self.session.refresh(user)
        self.revoke_all_tokens(user_id=user.id)

        # TODO: delete User related resources

        return user

    def restore_user(self, user: User) -> User:
        """
        Soft Delete a User
        """
        user.is_deleted = False
        user.deleted_at = None
        user.deletion_requested_at = None
        user.is_active = True
        user.deactivated_at = None

        self.session.commit()
        self.session.refresh(user)

        # TODO: restore User related resources

        return user

    def request_deletion(self, user: User) -> User:
        user.deletion_requested_at = utc_now()
        self.session.commit()
        self.session.refresh(user)
        return user

    def cancel_request_deletion(self, user: User) -> User:
        user.deletion_requested_at = None
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
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
    ) -> list[User]:
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

    def revoke_all_tokens(self, user_id: UUID) -> None:
        tokens = self.session.query(RefreshToken).filter(RefreshToken.user_id == user_id).all()
        for token in tokens:
            token.is_revoked = True
        self.session.commit()

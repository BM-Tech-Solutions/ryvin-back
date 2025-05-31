from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import random
import string
from uuid import UUID

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.user import User
from app.models.token import RefreshToken
from .base_service import BaseService
from .user_service import UserService


class AuthService(BaseService):
    """
    Service for authentication-related operations
    """
    def register_user(self, phone_number: str) -> User:
        """
        Register a new user with phone number
        """
        # Check if user already exists
        user_service = UserService(self.db)
        existing_user = user_service.get_user_by_phone(phone_number)
        
        if existing_user:
            if existing_user.is_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this phone number already exists"
                )
            # Return existing unverified user
            return existing_user
        
        # Create new user
        return user_service.create_user(phone_number)
    
    def generate_verification_code(self) -> str:
        """
        Generate a 6-digit verification code
        """
        return ''.join(random.choices(string.digits, k=6))
    
    def send_verification_code(self, phone_number: str, code: str) -> bool:
        """
        Send verification code via SMS
        In a real application, this would integrate with an SMS service
        """
        # In development, just print the code
        print(f"Sending verification code {code} to {phone_number}")
        # In production, integrate with SMS service like Twilio
        return True
    
    def verify_user(self, phone_number: str, code: str) -> User:
        """
        Verify user with verification code
        """
        # In a real app, we would check the code against what was sent
        # For now, we'll just verify the user
        
        user_service = UserService(self.db)
        user = user_service.get_user_by_phone(phone_number)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # For demo purposes, accept any 6-digit code
        if not code or len(code) != 6 or not code.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
        
        return user_service.verify_user(user)
    
    def authenticate_user(self, phone_number: str, password: str = None) -> User:
        """
        Authenticate a user by phone number and password
        """
        user_service = UserService(self.db)
        user = user_service.get_user_by_phone(phone_number)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive"
            )
        
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not verified"
            )
        
        # If password is set and provided, verify it
        if user.hashed_password and password:
            if not verify_password(password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
        elif user.hashed_password and not password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password required"
            )
        
        # Update last login
        return user_service.update_last_login(user)
    
    def create_tokens(self, user: User) -> Dict[str, str]:
        """
        Create access and refresh tokens for user
        """
        access_token = create_access_token(
            data={"sub": str(user.id)}
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # Store refresh token in database
        db_token = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        self.db.add(db_token)
        self.db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        """
        Create new access and refresh tokens using a valid refresh token
        """
        # Find the token in the database
        db_token = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.expires_at > datetime.utcnow(),
            RefreshToken.is_revoked == False
        ).first()
        
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Revoke the old token
        db_token.is_revoked = True
        self.db.commit()
        
        # Get the user
        user_service = UserService(self.db)
        user = user_service.get_user_by_id(db_token.user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive or deleted"
            )
        
        # Create new tokens
        return self.create_tokens(user)
    
    def logout(self, refresh_token: str) -> bool:
        """
        Revoke a refresh token to logout
        """
        db_token = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.is_revoked == False
        ).first()
        
        if db_token:
            db_token.is_revoked = True
            self.db.commit()
            return True
        
        return False

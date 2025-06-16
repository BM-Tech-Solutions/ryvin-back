from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import random
import string
import json
import requests
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
    def send_otp(self, phone_number: str) -> Dict[str, Any]:
        """
        Send OTP to user's phone number using Firebase Auth
        Returns verification ID from Firebase
        """
        # Check if user already exists
        user_service = UserService(self.db)
        existing_user = user_service.get_user_by_phone(phone_number)
        
        # In a real implementation, we would integrate with Firebase Auth REST API
        # to send the verification code
        # For now, we'll simulate it with a mock verification ID
        verification_id = f"firebase-{phone_number}-{self.generate_verification_code()}"
        
        # Store verification ID if user exists
        if existing_user:
            existing_user.verification_id = verification_id
            self.db.commit()
            self.db.refresh(existing_user)
            
            return {
                "message": "OTP sent successfully",
                "verification_id": verification_id,
                "user_exists": True
            }
        
        # Create a new unverified user
        new_user = user_service.create_user(phone_number)
        new_user.verification_id = verification_id
        self.db.commit()
        self.db.refresh(new_user)
        
        return {
            "message": "OTP sent successfully",
            "verification_id": verification_id,
            "user_exists": False
        }
    
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
    
    def verify_otp(self, verification_id: str, code: str) -> Dict[str, Any]:
        """
        Verify OTP code and return user information
        """
        # Find user with this verification ID
        user = self.db.query(User).filter(User.verification_id == verification_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid verification ID"
            )
        
        # In a real implementation, we would validate the OTP with Firebase Auth
        # For now, we'll accept any 6-digit code
        if not code or len(code) != 6 or not code.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
        
        # Check if user is already verified (has completed registration)
        user_service = UserService(self.db)
        user_exists = user.is_verified and user.name is not None and user.email is not None
        
        # Mark phone as verified
        user.is_verified = True
        user.verification_id = None  # Clear verification ID after successful verification
        self.db.commit()
        self.db.refresh(user)
        
        # Create tokens
        tokens = self.create_tokens(user)
        
        return {
            "user_exists": user_exists,
            "user_id": str(user.id),
            **tokens
        }
    
    def register_user(self, user_id: UUID, name: str, email: str) -> Dict[str, Any]:
        """
        Complete user registration with name and email
        """
        user_service = UserService(self.db)
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number not verified"
            )
        
        # Check if email is already in use
        existing_email_user = user_service.get_user_by_email(email)
        if existing_email_user and existing_email_user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        
        # Update user information
        user.name = name
        user.email = email
        self.db.commit()
        self.db.refresh(user)
        
        # Create tokens
        tokens = self.create_tokens(user)
        
        return {
            "message": "User registered successfully",
            "user_id": str(user.id),
            **tokens
        }
    
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
        
    def social_login(self, access_token: str, provider: str) -> Dict[str, Any]:
        """
        Handle social login (Google)
        """
        if provider != "google.com":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported provider"
            )
        
        # Verify the token with Google
        user_info = self._verify_google_token(access_token)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token"
            )
        
        # Check if user exists by provider ID
        user = self.db.query(User).filter(
            User.provider == provider,
            User.provider_user_id == user_info["sub"]
        ).first()
        
        user_service = UserService(self.db)
        user_exists = True
        
        if not user:
            # Check if user exists by email
            user = user_service.get_user_by_email(user_info["email"])
            
            if not user:
                # Create new user
                user = User(
                    email=user_info["email"],
                    name=user_info["name"],
                    is_active=True,
                    is_verified=True,
                    provider=provider,
                    provider_user_id=user_info["sub"]
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
                user_exists = False
            else:
                # Update existing user with provider info
                user.provider = provider
                user.provider_user_id = user_info["sub"]
                self.db.commit()
                self.db.refresh(user)
        
        # Update last login
        user = user_service.update_last_login(user)
        
        # Create tokens
        tokens = self.create_tokens(user)
        
        return {
            "user_exists": user_exists,
            "user_id": str(user.id),
            **tokens
        }
        
    def _verify_google_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Google access token and get user info
        """
        try:
            # In a real implementation, we would verify the token with Google
            # https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=YOUR_TOKEN
            response = requests.get(
                f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}"
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

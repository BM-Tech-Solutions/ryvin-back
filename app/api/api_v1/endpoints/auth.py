from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.token import Token
from app.services.auth_service import AuthService


# Request models
class SendOTPRequest(BaseModel):
    phone_number: str


class VerifyOTPRequest(BaseModel):
    verification_id: str
    code: str


class RegisterUserRequest(BaseModel):
    user_id: UUID
    name: str
    email: EmailStr


class SocialLoginRequest(BaseModel):
    access_token: str
    provider: str = Field(..., description="Provider name, e.g. 'google.com'")


router = APIRouter()


@router.post("/send-otp", status_code=status.HTTP_200_OK)
def send_otp(
    request: SendOTPRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Send OTP to user's phone number
    """
    auth_service = AuthService(db)
    return auth_service.send_otp(request.phone_number)


@router.post("/verify", status_code=status.HTTP_200_OK)
def verify_otp(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verify OTP code and return user information
    """
    auth_service = AuthService(db)
    return auth_service.verify_otp(request.verification_id, request.code)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(
    request: RegisterUserRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Complete user registration with name and email
    """
    auth_service = AuthService(db)
    return auth_service.register_user(request.user_id, request.name, request.email)


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token
    """
    auth_service = AuthService(db)
    
    try:
        # Refresh tokens using the auth service
        tokens = auth_service.refresh_tokens(refresh_token)
        return tokens
    except HTTPException:
        # Re-raise HTTP exceptions from the service
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token",
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Logout user by revoking refresh token
    """
    auth_service = AuthService(db)
    
    # Revoke the refresh token
    success = auth_service.logout(refresh_token)
    
    if success:
        return {"message": "Logged out successfully"}
    else:
        return {"message": "Token already revoked or not found"}


@router.post("/social-login", status_code=status.HTTP_200_OK)
def social_login(
    request: SocialLoginRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Handle social login (Google)
    """
    auth_service = AuthService(db)
    return auth_service.social_login(request.access_token, request.provider)

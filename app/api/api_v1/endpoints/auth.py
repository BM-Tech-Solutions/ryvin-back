from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.token import Token
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    phone_number: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user with phone number
    """
    auth_service = AuthService(db)
    
    # Register user
    user = auth_service.register_user(phone_number)
    
    # Generate verification code
    verification_code = auth_service.generate_verification_code()
    
    # Send SMS verification
    auth_service.send_verification_code(phone_number, verification_code)
    
    return {
        "message": "User registered successfully. Verification code sent.",
        "user_id": user.id,
        "verification_code": verification_code  # In production, don't return this
    }


@router.post("/verify", status_code=status.HTTP_200_OK)
def verify_phone(
    phone_number: str,
    verification_code: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Verify user's phone number with verification code
    """
    auth_service = AuthService(db)
    
    # Verify user with code
    user = auth_service.verify_user(phone_number, verification_code)
    
    # Create tokens
    tokens = auth_service.create_tokens(user)
    
    return {
        "message": "Phone number verified successfully",
        **tokens
    }


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    auth_service = AuthService(db)
    
    # Authenticate user
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    
    # Create tokens
    tokens = auth_service.create_tokens(user)
    
    return tokens


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

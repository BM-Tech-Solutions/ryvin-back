"""Authentication Service
--------------------
Service for Firebase authentication operations with simplified flow.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import requests
import json
import uuid
import random
import string
from uuid import UUID

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from jose import jwt, JWTError
from firebase_admin import auth as firebase_auth, credentials, initialize_app

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User
from app.models.token import RefreshToken
from app.services.base_service import BaseService
from app.services.user_service import UserService


# Initialize Firebase Admin SDK
firebase_app = None

# Try to initialize Firebase with environment variables first
if (settings.FIREBASE_TYPE and settings.FIREBASE_PROJECT_ID_ENV and 
    settings.FIREBASE_PRIVATE_KEY and settings.FIREBASE_CLIENT_EMAIL):
    try:
        # Create credentials dictionary from environment variables
        firebase_cred_dict = {
            "type": settings.FIREBASE_TYPE,
            "project_id": settings.FIREBASE_PROJECT_ID_ENV,
            "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
            "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),  # Fix newlines in private key
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
            "client_id": settings.FIREBASE_CLIENT_ID,
            "auth_uri": settings.FIREBASE_AUTH_URI,
            "token_uri": settings.FIREBASE_TOKEN_URI,
            "auth_provider_x509_cert_url": settings.FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
            "client_x509_cert_url": settings.FIREBASE_CLIENT_X509_CERT_URL
        }
        firebase_cred = credentials.Certificate(firebase_cred_dict)
        firebase_app = initialize_app(firebase_cred)
        print("Firebase Admin SDK initialized successfully from environment variables")
    except Exception as e:
        print(f"Failed to initialize Firebase from environment variables: {e}")

# Fall back to file-based credentials if environment variables are not available
if firebase_app is None and settings.FIREBASE_SERVICE_ACCOUNT_PATH:
    try:
        import os
        # Check if file exists
        if os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
            firebase_cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
            firebase_app = initialize_app(firebase_cred)
            print("Firebase Admin SDK initialized successfully from credentials file")
        else:
            print(f"Firebase credentials file not found at: {settings.FIREBASE_SERVICE_ACCOUNT_PATH}")
    except Exception as e:
        print(f"Firebase initialization error: {str(e)}")
        # Continue without Firebase initialization for development environments
else:
    print("FIREBASE_SERVICE_ACCOUNT_PATH not set in environment variables")
    # Continue without Firebase initialization


class AuthService(BaseService):
    """
    Service for authentication operations with simplified flow
    """
    
    def verify_user_exists(self, phone_number: str) -> Dict[str, Any]:
        """
        Verify if a user exists with the given phone number
        """
        try:
            # Check if user exists in Firebase
            try:
                firebase_user = firebase_auth.get_user_by_phone_number(phone_number)
                firebase_exists = True
            except firebase_auth.UserNotFoundError:
                firebase_exists = False
            
            # Check if user exists in our database
            user = self.db.query(User).filter(User.phone == phone_number).first()
            
            response = {
                "exists": firebase_exists or user is not None,
                "phone_number": phone_number
            }
            
            if user:
                response["user_id"] = str(user.id)
            
            return response
            
        except Exception as e:
            print(f"Error in verify_user_exists: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to verify user: {str(e)}"
            )
    
    def verify_phone_token(self, firebase_token: str) -> Dict[str, Any]:
        """
        Verify phone number with Firebase ID token (only verification, no user creation)
        """
        try:
            # Verify Firebase token
            decoded_token = firebase_auth.verify_id_token(firebase_token)
            firebase_uid = decoded_token.get("uid")
            phone_number = decoded_token.get("phone_number")
            
            if not firebase_uid or not phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Firebase token: missing uid or phone_number"
                )
            
            # Get Firebase user to verify it exists
            firebase_user = firebase_auth.get_user(firebase_uid)
            
            return {
                "firebase_uid": firebase_uid,
                "phone_number": phone_number,
                "is_verified": True
            }
            
        except firebase_auth.InvalidIdTokenError as e:
            print(f"Invalid Firebase token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Firebase token: {str(e)}"
            )
        except Exception as e:
            print(f"Error in verify_phone_token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to verify phone token: {str(e)}"
            )
    
    def register_user(self, firebase_token: str, device_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Register a new user with Firebase token after verification
        """
        try:
            # Verify Firebase token
            decoded_token = firebase_auth.verify_id_token(firebase_token)
            firebase_uid = decoded_token.get("uid")
            phone_number = decoded_token.get("phone_number")
            
            if not firebase_uid or not phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Firebase token: missing uid or phone_number"
                )
            
            # Check if user already exists
            user = self.db.query(User).filter(User.phone == phone_number).first()
            if user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this phone number already exists"
                )
            
            # Create new user with null profile fields
            user = User(
                phone=phone_number,
                firebase_uid=firebase_uid,
                is_verified=True,
                last_login=datetime.utcnow(),
                name=None,
                email=None,
                profile_image=None
            )
            
            # Add device info if provided
            if device_info:
                if "device_id" in device_info:
                    user.device_id = device_info.get("device_id")
                if "platform" in device_info:
                    user.platform = device_info.get("platform")
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # Generate tokens
            access_token = create_access_token(subject=str(user.id))
            refresh_token = self._generate_unique_refresh_token(str(user.id))
            
            # Store the refresh token in the database
            expires_at = datetime.utcnow() + timedelta(days=30)
            db_refresh_token = RefreshToken(
                id=uuid.uuid4(),
                user_id=user.id,
                token=refresh_token,
                expires_at=expires_at,
                is_revoked=False
            )
            self.db.add(db_refresh_token)
            self.db.commit()
            
            return {
                "user_id": str(user.id),
                "phone_number": phone_number,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
        except firebase_auth.InvalidIdTokenError as e:
            print(f"Invalid Firebase token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Firebase token: {str(e)}"
            )
        except Exception as e:
            print(f"Error in register_user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to register user: {str(e)}"
            )
    
    def login_user(self, firebase_token: str, device_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Login with Firebase token
        """
        try:
            # Verify Firebase token
            decoded_token = firebase_auth.verify_id_token(firebase_token)
            firebase_uid = decoded_token.get("uid")
            phone_number = decoded_token.get("phone_number")
            
            if not firebase_uid or not phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Firebase token: missing uid or phone_number"
                )
            
            # Check if user exists in our database
            user = self.db.query(User).filter(User.phone == phone_number).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found. Please register first."
                )
            
            # Update user's Firebase UID if it has changed
            if user.firebase_uid != firebase_uid:
                user.firebase_uid = firebase_uid
            
            # Update last login and device info
            user.last_login = datetime.utcnow()
            
            if device_info:
                if "device_id" in device_info:
                    user.device_id = device_info.get("device_id")
                if "platform" in device_info:
                    user.platform = device_info.get("platform")
            
            self.db.commit()
            self.db.refresh(user)
            
            # Check if profile is complete
            profile_complete = user.name is not None and user.email is not None
            
            # Generate tokens
            access_token = create_access_token(subject=str(user.id))
            refresh_token = self._generate_unique_refresh_token(str(user.id))
            
            # Store the refresh token in the database
            expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Check if a refresh token already exists for this user
            existing_token = self.db.query(RefreshToken).filter(RefreshToken.user_id == user.id).first()
            
            if existing_token:
                # Update existing token
                existing_token.token = refresh_token
                existing_token.expires_at = expires_at
                existing_token.is_revoked = False
            else:
                # Create new refresh token record
                db_refresh_token = RefreshToken(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    token=refresh_token,
                    expires_at=expires_at,
                    is_revoked=False
                )
                self.db.add(db_refresh_token)
            
            self.db.commit()
            
            return {
                "user_id": str(user.id),
                "phone_number": user.phone,
                "name": user.name,
                "email": user.email,
                "profile_image": user.profile_image,
                "profile_complete": profile_complete,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
        except firebase_auth.InvalidIdTokenError as e:
            print(f"Invalid Firebase token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Firebase token: {str(e)}"
            )
        except Exception as e:
            print(f"Error in login_user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to login user: {str(e)}"
            )
    
    def verify_phone(self, firebase_token: str, device_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Verify phone number with Firebase ID token and create or update user
        """
        try:
            # Verify Firebase token
            decoded_token = firebase_auth.verify_id_token(firebase_token)
            firebase_uid = decoded_token.get("uid")
            phone_number = decoded_token.get("phone_number")
            
            if not firebase_uid or not phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Firebase token: missing uid or phone_number"
                )
            
            # Get Firebase user
            firebase_user = firebase_auth.get_user(firebase_uid)
            
            # Check if user exists in our database
            user = self.db.query(User).filter(User.phone == phone_number).first()
            
            user_exists = user is not None
            profile_complete = user is not None and user.name is not None and user.email is not None
            
            if not user:
                # Create new user
                user = User(
                    phone=phone_number,
                    firebase_uid=firebase_uid,
                    is_verified=True,
                    last_login=datetime.utcnow()
                )
                
                # Add device info if provided
                if device_info:
                    if "device_id" in device_info:
                        user.device_id = device_info.get("device_id")
                    if "platform" in device_info:
                        user.platform = device_info.get("platform")
                
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
            else:
                # Update existing user
                user.firebase_uid = firebase_uid
                user.is_verified = True
                user.last_login = datetime.utcnow()
                
                # Update device info if provided
                if device_info:
                    if "device_id" in device_info:
                        user.device_id = device_info.get("device_id")
                    if "platform" in device_info:
                        user.platform = device_info.get("platform")
                
                self.db.commit()
                self.db.refresh(user)
            
            # Generate tokens
            access_token = create_access_token(subject=str(user.id))
            refresh_token = self._generate_unique_refresh_token(str(user.id))
            
            # Store the refresh token in the database
            expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Check if a refresh token already exists for this user
            existing_token = self.db.query(RefreshToken).filter(RefreshToken.user_id == user.id).first()
            
            if existing_token:
                # Update existing token
                existing_token.token = refresh_token
                existing_token.expires_at = expires_at
                existing_token.is_revoked = False
            else:
                # Create new refresh token record
                db_refresh_token = RefreshToken(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    token=refresh_token,
                    expires_at=expires_at,
                    is_revoked=False
                )
                self.db.add(db_refresh_token)
            
            self.db.commit()
            
            response = {
                "user_exists": user_exists,
                "profile_complete": profile_complete,
                "user_id": str(user.id),
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
            # Include user data if profile is complete
            if profile_complete:
                response["user"] = {
                    "id": str(user.id),
                    "phone": user.phone,
                    "name": user.name,
                    "email": user.email,
                    "is_verified": user.is_verified,
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None
                }
            
            return response
            
        except firebase_auth.InvalidIdTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Firebase token: {str(e)}"
            )
        except Exception as e:
            print(f"Error in verify_phone: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to verify phone: {str(e)}"
            )
    
    def complete_profile(
        self,
        access_token: str,
        name: str,
        email: str,
        profile_image: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete user profile after phone verification
        """
        try:
            # Verify access token
            try:
                payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=["HS256"])
                
                # Check token type
                if payload.get("type") != "access":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid token type"
                    )
                    
                user_id = UUID(payload.get("sub"))
                
            except (JWTError, ValueError) as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid or expired token: {str(e)}"
                )
            
            # Get user by ID
            user = self.db.query(User).filter(User.id == user_id).first()
            
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
            existing_email_user = self.db.query(User).filter(
                User.email == email,
                User.id != user.id
            ).first()
            
            if existing_email_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            
            # Update user information
            user.name = name
            user.email = email
            if profile_image:
                user.profile_image = profile_image
            
            self.db.commit()
            self.db.refresh(user)
            
            # Generate new tokens
            access_token = create_access_token(subject=str(user.id))
            refresh_token = self._generate_unique_refresh_token(str(user.id))
            
            # Store the refresh token in the database
            expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Check if a refresh token already exists for this user
            existing_token = self.db.query(RefreshToken).filter(RefreshToken.user_id == user.id).first()
            
            if existing_token:
                # Update existing token
                existing_token.token = refresh_token
                existing_token.expires_at = expires_at
                existing_token.is_revoked = False
            else:
                # Create new refresh token record
                db_refresh_token = RefreshToken(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    token=refresh_token,
                    expires_at=expires_at,
                    is_revoked=False
                )
                self.db.add(db_refresh_token)
            
            self.db.commit()
            
            return {
                "user_id": str(user.id),
                "name": user.name,
                "email": user.email,
                "profile_image": user.profile_image,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            print(f"Error in complete_profile: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to complete profile: {str(e)}"
            )
    
    def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """
        Create new access and refresh tokens using a valid refresh token
        """
        try:
            # Find the refresh token in the database
            db_refresh_token = self.db.query(RefreshToken).filter(
                RefreshToken.token == refresh_token,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            ).first()
            
            if not db_refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token"
                )
            
            # Create new tokens
            access_token = create_access_token(subject=str(db_refresh_token.user_id))
            new_refresh_token = self._generate_unique_refresh_token(str(db_refresh_token.user_id))
            
            # Update the refresh token in the database
            db_refresh_token.token = new_refresh_token
            db_refresh_token.expires_at = datetime.utcnow() + timedelta(days=30)
            
            self.db.commit()
            
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            print(f"Error in refresh_tokens: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to refresh tokens: {str(e)}"
            )
    
    def logout(self, refresh_token: str) -> Dict[str, Any]:
        """
        Revoke a refresh token to logout
        """
        try:
            # Find the refresh token in the database
            db_refresh_token = self.db.query(RefreshToken).filter(
                RefreshToken.token == refresh_token
            ).first()
            
            if not db_refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Token not found"
                )
            
            # Revoke the token
            db_refresh_token.is_revoked = True
            self.db.commit()
            
            return {"message": "Successfully logged out"}
            
        except Exception as e:
            print(f"Error in logout: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to logout: {str(e)}"
            )
    
    def _generate_unique_refresh_token(self, user_id: str) -> str:
        """
        Generate a unique refresh token with a random suffix to ensure uniqueness
        """
        # Generate a random suffix (8 characters)
        suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        # Create a refresh token with the user ID and random suffix
        return create_refresh_token(subject=f"{user_id}:{suffix}")
        
    def generate_test_token(self, phone_number: str) -> Optional[str]:
        """
        Generate a test Firebase ID token for a given phone number.
        This is for testing purposes only.
        """
        try:
            # Check if user exists in Firebase
            try:
                user = firebase_auth.get_user_by_phone_number(phone_number)
                print(f"Found existing Firebase user with phone: {phone_number}")
            except firebase_auth.UserNotFoundError:
                # Create user if not exists
                user = firebase_auth.create_user(
                    phone_number=phone_number
                )
                print(f"Created new Firebase user with phone: {phone_number}")
            
            # Create custom token
            custom_token = firebase_auth.create_custom_token(user.uid)
            print(f"Created custom token for user: {user.uid}")
            
            # Exchange for ID token
            response = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={settings.FIREBASE_API_KEY}",
                json={
                    "token": custom_token.decode('utf-8'),
                    "returnSecureToken": True
                }
            )
            
            if response.status_code == 200:
                id_token = response.json().get("idToken")
                print(f"Successfully exchanged for ID token")
                return id_token
            else:
                print(f"Error exchanging token: {response.text}")
                return None
        except Exception as e:
            print(f"Error generating test token: {e}")
            return None

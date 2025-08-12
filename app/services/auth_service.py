"""Authentication Service
--------------------
Service for Firebase authentication operations with simplified flow.
"""

import random
import string
import uuid
from datetime import timedelta
from typing import Any, Dict, Optional
from uuid import UUID

import requests
from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, utc_now
from app.models.token import RefreshToken
from app.models.user import User
from app.services.base_service import BaseService
from firebase import init_firebase


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
                # unused variable
                firebase_user = firebase_auth.get_user_by_phone_number(phone_number)  # noqa: F841
                firebase_exists = True
            except firebase_auth.UserNotFoundError:
                firebase_exists = False

            # Check if user exists in our database
            user = self.db.query(User).filter(User.phone_number == phone_number).first()

            response = {"exists": firebase_exists or user is not None, "phone_number": phone_number}

            if user:
                response["user_id"] = str(user.id)

            return response

        except Exception as e:
            print(f"Error in verify_user_exists: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to verify user: {str(e)}",
            )

    def verify_phone_token(self, phone_number: str) -> Dict[str, Any]:
        """
        Verify phone number (token verification is handled in the frontend)

        This method is kept for backward compatibility but doesn't perform verification
        as it's now handled in the frontend.
        """
        try:
            if not phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is required"
                )

            return {"phone_number": phone_number, "is_verified": True}

        except firebase_auth.InvalidIdTokenError as e:
            print(f"Invalid Firebase token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Firebase token: {str(e)}"
            )
        except Exception as e:
            print(f"Error in verify_phone_token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to verify phone token: {str(e)}",
            )

    def register_user(
        self, phone_number: str, device_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a new user with phone number after verification

        Note: Firebase token verification is handled in the frontend
        """
        try:
            if not phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is required"
                )

            # Check if user already exists
            user = self.db.query(User).filter(User.phone_number == phone_number).first()
            if user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this phone number already exists",
                )

            # Create new user with null profile fields
            user = User(
                phone_number=phone_number,
                is_verified=True,
                last_login=utc_now,
                email=None,
            )

            # Device info fields are not stored on User model currently

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            # Generate tokens
            access_token = create_access_token(subject=str(user.id))
            refresh_token = self._generate_unique_refresh_token(str(user.id))

            # Store the refresh token in the database
            expires_at = utc_now() + timedelta(days=30)
            db_refresh_token = RefreshToken(
                id=uuid.uuid4(),
                user_id=user.id,
                token=refresh_token,
                expires_at=expires_at,
                is_revoked=False,
            )
            self.db.add(db_refresh_token)
            self.db.commit()

            return {
                "user_id": str(user.id),
                "phone_number": phone_number,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }

        except firebase_auth.InvalidIdTokenError as e:
            print(f"Invalid Firebase token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Firebase token: {str(e)}"
            )
        except Exception as e:
            print(f"Error in register_user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to register user: {str(e)}",
            )

    def login_user(
        self, phone_number: str, device_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Login with phone number

        Note: Firebase token verification is handled in the frontend
        """
        try:
            if not phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is required"
                )

            # Check if user exists in our database
            user = self.db.query(User).filter(User.phone_number == phone_number).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found. Please register first.",
                )

            # Update last login and device info
            user.last_login = utc_now()

            if device_info:
                if "device_id" in device_info:
                    user.device_id = device_info.get("device_id")
                if "platform" in device_info:
                    user.platform = device_info.get("platform")

            self.db.commit()
            self.db.refresh(user)

            # Check if profile is complete (based on available fields)
            profile_complete = user.email is not None

            # Generate tokens
            access_token = create_access_token(subject=str(user.id))
            refresh_token = self._generate_unique_refresh_token(str(user.id))

            # Store the refresh token in the database
            expires_at = utc_now() + timedelta(days=30)

            # Check if a refresh token already exists for this user
            existing_token = (
                self.db.query(RefreshToken).filter(RefreshToken.user_id == user.id).first()
            )

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
                    is_revoked=False,
                )
                self.db.add(db_refresh_token)

            self.db.commit()

            return {
                "user_id": str(user.id),
                "phone_number": user.phone_number,
                "email": user.email,
                "profile_complete": profile_complete,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }

        except firebase_auth.InvalidIdTokenError as e:
            print(f"Invalid Firebase token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Firebase token: {str(e)}"
            )
        except Exception as e:
            print(f"Error in login_user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to login user: {str(e)}",
            )

    def verify_phone(
        self, phone_number: str, device_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Verify phone number and create or update user

        Note: Firebase token verification is handled in the frontend
        """
        try:
            if not phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is required"
                )

            # Check if user exists in our database
            user = self.db.query(User).filter(User.phone_number == phone_number).first()

            user_exists = user is not None
            profile_complete = user is not None and user.email is not None

            if not user:
                # Create new user
                user = User(
                    phone_number=phone_number,
                    is_verified=True,
                    last_login=utc_now(),
                    email=None,
                )

                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
            else:
                # Update existing user
                user.is_verified = True
                user.last_login = utc_now()

                # Device info fields are not stored on User model currently

                self.db.commit()
                self.db.refresh(user)

            # Generate tokens
            access_token = create_access_token(subject=str(user.id))
            refresh_token = self._generate_unique_refresh_token(str(user.id))

            # Store the refresh token in the database
            expires_at = utc_now() + timedelta(days=30)

            # Check if a refresh token already exists for this user
            existing_token = (
                self.db.query(RefreshToken).filter(RefreshToken.user_id == user.id).first()
            )

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
                    is_revoked=False,
                )
                self.db.add(db_refresh_token)

            self.db.commit()

            response = {
                "user_exists": user_exists,
                "profile_complete": profile_complete,
                "user_id": str(user.id),
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
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
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                }

            return response

        except firebase_auth.InvalidIdTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Firebase token: {str(e)}"
            )
        except Exception as e:
            print(f"Error in verify_phone: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to verify phone: {str(e)}",
            )

    def complete_profile(
        self, access_token: str, name: str, email: str, profile_image: Optional[str] = None
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
                        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type"
                    )

                user_id = UUID(payload.get("sub"))

            except (JWTError, ValueError) as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid or expired token: {str(e)}",
                )

            # Get user by ID
            user = self.db.query(User).filter(User.id == user_id).first()

            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            if not user.is_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number not verified"
                )

            # Check if email is already in use
            existing_email_user = (
                self.db.query(User).filter(User.email == email, User.id != user.id).first()
            )

            if existing_email_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use"
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
            expires_at = utc_now() + timedelta(days=30)

            # Check if a refresh token already exists for this user
            existing_token = (
                self.db.query(RefreshToken).filter(RefreshToken.user_id == user.id).first()
            )

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
                    is_revoked=False,
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
                "token_type": "bearer",
            }

        except Exception as e:
            print(f"Error in complete_profile: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to complete profile: {str(e)}",
            )

    def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """
        Create new access and refresh tokens using a valid refresh token
        """
        try:
            # Find the refresh token in the database
            db_refresh_token = (
                self.db.query(RefreshToken)
                .filter(
                    RefreshToken.token == refresh_token,
                    RefreshToken.is_revoked.is_(False),
                    RefreshToken.expires_at > utc_now(),
                )
                .first()
            )

            if not db_refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token",
                )

            # Create new tokens
            access_token = create_access_token(subject=str(db_refresh_token.user_id))
            new_refresh_token = self._generate_unique_refresh_token(str(db_refresh_token.user_id))

            # Update the refresh token in the database
            db_refresh_token.token = new_refresh_token
            db_refresh_token.expires_at = utc_now() + timedelta(days=30)

            self.db.commit()

            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
            }

        except Exception as e:
            print(f"Error in refresh_tokens: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to refresh tokens: {str(e)}",
            )

    def phone_auth(
        self, phone_number: str, device_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Unified phone authentication method that handles both new and existing users.

        1. Checks if user exists
        2. Creates account if user doesn't exist
        3. Returns login info in both cases

        Note: Firebase token verification is handled in the frontend
        """
        try:
            if not phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is required"
                )

            # Check if user exists in our database
            user = self.db.query(User).filter(User.phone_number == phone_number).first()
            is_new_user = user is None

            if is_new_user:
                # Create new user with null profile fields
                user = User(
                    phone_number=phone_number,
                    is_verified=True,
                    last_login=utc_now(),
                    name=None,
                    email=None,
                    profile_image=None,
                )
            else:
                # Update last login timestamp
                user.last_login = utc_now()

            # Device info is accepted but not stored as the User model has no such columns

            # Save user to database
            if is_new_user:
                self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            # Check if profile is complete
            is_profile_complete = user.name is not None and user.email is not None

            # Generate tokens
            access_token = create_access_token(subject=str(user.id))
            refresh_token = self._generate_unique_refresh_token(str(user.id))

            # Store the refresh token in the database
            expires_at = utc_now() + timedelta(days=30)

            # Check if a refresh token already exists for this user
            existing_token = (
                self.db.query(RefreshToken).filter(RefreshToken.user_id == user.id).first()
            )

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
                    is_revoked=False,
                )
                self.db.add(db_refresh_token)

            self.db.commit()

            return {
                "user_id": str(user.id),
                "phone_number": phone_number,
                "email": user.email,
                "name": user.name,
                "profile_image": user.profile_image,
                "is_new_user": is_new_user,
                "is_profile_complete": is_profile_complete,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }

        except firebase_auth.InvalidIdTokenError as e:
            print(f"Invalid Firebase token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Firebase token: {str(e)}"
            )
        except Exception as e:
            print(f"Error in phone_auth: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to authenticate user: {str(e)}",
            )

    def google_auth(
        self, google_token: str, device_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Unified Google authentication method that handles both new and existing users.

        1. Verifies Google token using Firebase Admin SDK
        2. Retrieves user data from the verified token
        3. Checks if email exists in our system
        4. Creates account if user doesn't exist
        5. Returns login info in both cases
        """
        try:
            # Ensure Firebase is initialized with proper project ID/options
            init_firebase()
            # Verify the Google ID token using Firebase Admin SDK
            try:
                decoded_token = firebase_auth.verify_id_token(google_token)

                # Extract user data from the decoded token
                email = decoded_token.get("email")
                name = decoded_token.get("name", "")
                profile_image = decoded_token.get("picture", "")
                # unused variable
                google_id = decoded_token.get("sub")  # noqa: F841

                if not email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email not found in the Google token",
                    )

            except (ValueError, firebase_auth.InvalidIdTokenError) as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid Google token: {str(e)}",
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error verifying Google token: {str(e)}",
                )

            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Email not provided by Google"
                )

            # Check if user exists by email
            user = self.db.query(User).filter(User.email == email).first()
            is_new_user = user is None

            if is_new_user:
                # Create new user with no phone number (NULL). Requires DB column to be nullable.
                user = User(
                    phone_number=None,
                    email=email,
                    name=name,
                    profile_image=profile_image,
                    is_verified=True,
                    last_login=utc_now(),
                )
            else:
                # Update existing user
                user.name = name if name else user.name
                user.profile_image = profile_image if profile_image else user.profile_image
                user.last_login = utc_now()
                user.is_verified = True

            # Device info is accepted but not stored as the User model has no such columns

            # Save user to database
            if is_new_user:
                self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            # For Google auth, profile is complete by default
            is_profile_complete = True

            # Generate tokens
            access_token = create_access_token(subject=str(user.id))
            refresh_token = self._generate_unique_refresh_token(str(user.id))

            # Store the refresh token in the database
            expires_at = utc_now() + timedelta(days=30)

            # Check if a refresh token already exists for this user
            existing_token = (
                self.db.query(RefreshToken).filter(RefreshToken.user_id == user.id).first()
            )

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
                    is_revoked=False,
                )
                self.db.add(db_refresh_token)

            self.db.commit()

            return {
                "user_id": str(user.id),
                "phone_number": user.phone_number,
                "email": email,
                "name": name,
                "profile_image": profile_image,
                "is_new_user": is_new_user,
                "is_profile_complete": is_profile_complete,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }

        except Exception as e:
            print(f"Error in google_auth: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to authenticate with Google: {str(e)}",
            )

    def _get_google_user_info(self, google_token: str) -> Dict[str, Any]:
        """
        Get user info from Google using an access token
        """
        try:
            response = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {google_token}"},
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Google API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error fetching Google user info: {e}")
            return None

    def logout(self, refresh_token: str) -> Dict[str, Any]:
        """
        Revoke a refresh token to logout
        """
        try:
            # Find the refresh token in the database
            db_refresh_token = (
                self.db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
            )

            if not db_refresh_token:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

            # Revoke the token
            db_refresh_token.is_revoked = True
            self.db.commit()

            return {"message": "Successfully logged out"}

        except Exception as e:
            print(f"Error in logout: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to logout: {str(e)}",
            )

    def _generate_unique_refresh_token(self, user_id: str) -> str:
        """
        Generate a unique refresh token with a random suffix to ensure uniqueness
        """
        # Generate a random suffix (8 characters)
        suffix = "".join(random.choices(string.ascii_letters + string.digits, k=8))

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
                user = firebase_auth.create_user(phone_number=phone_number)
                print(f"Created new Firebase user with phone: {phone_number}")

            # Create custom token
            custom_token = firebase_auth.create_custom_token(user.uid)
            print(f"Created custom token for user: {user.uid}")

            # Exchange for ID token
            response = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={settings.FIREBASE_API_KEY}",
                json={"token": custom_token.decode("utf-8"), "returnSecureToken": True},
            )

            if response.status_code == 200:
                id_token = response.json().get("idToken")
                print("Successfully exchanged for ID token")
                return id_token
            else:
                print(f"Error exchanging token: {response.text}")
                return None
        except Exception as e:
            print(f"Error generating test token: {e}")
            return None

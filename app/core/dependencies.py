from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request
from fastapi import status as http_status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import ValidationError
import logging

from app.core.config import settings
from app.core.database import SessionDep
from app.models.user import User
from app.schemas.token import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

logger = logging.getLogger(__name__)


async def get_current_user(
    session: SessionDep,
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Get the current user from the token
    """
    credentials_exception = HTTPException(
        status_code=http_status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        token_data = TokenPayload(**payload)
        if token_data.type != "access":
            raise credentials_exception
    except (JWTError, ValidationError):
        raise credentials_exception

    user = session.get(User, token_data.sub)
    if not user:
        raise credentials_exception
    return user


CurrUserDep = Annotated[User, Depends(get_current_user)]


# Flexible current user dependency
# - Accepts Authorization header containing either:
#   - "Bearer <JWT>" (case-insensitive), or
#   - a raw JWT token value without the Bearer prefix (to support Swagger input fields)
# - Note: API-Token is validated by middleware for access control, but it does not convey user identity.
async def get_current_user_flexible(
    session: SessionDep,
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
) -> User:
    # Prefer token provided via Swagger "Authorize" (HTTP Bearer)
    token: Optional[str] = None
    if credentials and credentials.credentials:
        logger.debug(
            "HTTPBearer credentials provided: scheme=%s, length=%s",
            getattr(credentials, "scheme", None),
            len(credentials.credentials) if credentials.credentials else 0,
        )
        token = credentials.credentials
    else:
        # Fallback to raw Authorization header (if provided directly)
        header_val = request.headers.get("authorization") or request.headers.get("Authorization")
        logger.debug(
            "Authorization header present: %s",
            bool(header_val),
        )
        if not header_val:
            header_val = None
        raw = header_val.strip() if header_val else None
        # Accept both Bearer-prefixed and raw token values
        if raw:
            if raw.lower().startswith("bearer "):
                token = raw.split(" ", 1)[1].strip()
            else:
                token = raw

    if token:
        logger.debug("Extracted token (masked): %s... (len=%d)", token[:8], len(token))
    else:
        logger.debug("No Bearer token extracted from request")

    credentials_exception = HTTPException(
        status_code=http_status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            token_data = TokenPayload(**payload)
            if token_data.type != "access":
                raise credentials_exception
        except (JWTError, ValidationError):
            raise credentials_exception

        user = session.get(User, token_data.sub)
        if not user:
            raise credentials_exception
        return user

    # No Bearer token provided; API-Token alone is not tied to a user identity
    raise HTTPException(
        status_code=http_status.HTTP_401_UNAUTHORIZED,
        detail="Missing Bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )


FlexUserDep = Annotated[User, Depends(get_current_user_flexible)]

async def get_current_active_user(current_user: FlexUserDep) -> User:
    """
    Get the current active user
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


ActiveUserDep = Annotated[User, Depends(get_current_active_user)]


async def get_current_verified_user(current_user: ActiveUserDep) -> User:
    """
    Get the current verified user
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User not verified",
        )
    return current_user


VerifiedUserDep = Annotated[User, Depends(get_current_verified_user)]


async def get_current_admin_user(current_user: VerifiedUserDep) -> User:
    """
    Get the current admin user
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


AdminUserDep = Annotated[User, Depends(get_current_admin_user)]

# Admin via API-Token + Admin-ID (no user Authorization required)
async def get_admin_via_api_token(
    session: SessionDep,
    api_token: Optional[str] = Header(default=None, alias="API-Token"),
    admin_id: Optional[UUID] = Header(default=None, alias="Admin-ID"),
) -> User:
    if not api_token or api_token != settings.API_TOKEN:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API-Token",
        )
    if not admin_id:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Missing Admin-ID header",
        )
    admin = session.get(User, admin_id)
    if not admin or not admin.is_admin:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return admin

# Alternative admin dependency for admin router
AdminViaTokenDep = Annotated[User, Depends(get_admin_via_api_token)]

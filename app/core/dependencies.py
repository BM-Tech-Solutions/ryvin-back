from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import settings
from app.core.database import SessionDep
from app.models.user import User
from app.schemas.token import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


# this dependency is for testing only, we'll remove this later
async def test_get_user(
    session: SessionDep,
    id_header: Annotated[
        UUID,
        Header(description="for testing only (instead of using 'Authorization')"),
    ] = "8131dbdf-e7a3-4197-bea8-19005ed8d520",
):
    user = session.query(User).filter(User.id == id_header).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not find user with id: {id_header}",
        )
    return user


TestGetUserDep = Annotated[User, Depends(test_get_user)]


async def get_current_user(
    session: SessionDep,
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Get the current user from the token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
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

    user = session.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise credentials_exception
    return user


CurrUserDep = Annotated[User, Depends(get_current_user)]


# this should be "current_user: CurrUserDep" not "current_user: TestGetUserDep"
async def get_current_active_user(current_user: TestGetUserDep) -> User:
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
            status_code=status.HTTP_403_FORBIDDEN,
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


AdminUserDep = Annotated[User, Depends(get_current_admin_user)]

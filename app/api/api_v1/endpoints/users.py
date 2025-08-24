from fastapi import APIRouter, Security
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.core.dependencies import FlexUserDep
from app.main import api_key_header, http_bearer

router = APIRouter()


class CurrentUserResponse(BaseModel):
    id: str
    name: str | None = None
    phone_region: str | None = None
    phone_number: str | None = None
    email: str | None = None
    is_admin: bool
    is_verified: bool


@router.get("/get_current_user", response_model=CurrentUserResponse)
async def get_current_user(
    current_user: FlexUserDep,
    api_key: str = Security(api_key_header),
    bearer: HTTPAuthorizationCredentials = Security(http_bearer),
) -> CurrentUserResponse:
    """
    Return the current authenticated user's details along with a freshly generated access token.
    Authentication: Bearer access token (no Admin-ID required).
    """
    return current_user

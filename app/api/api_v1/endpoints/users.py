from fastapi import APIRouter, Security
from fastapi.security import HTTPAuthorizationCredentials

from app.core.dependencies import FlexUserDep
from app.main import api_key_header, http_bearer
from app.schemas.user import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_current_user(
    current_user: FlexUserDep,
    api_key: str = Security(api_key_header),
    bearer: HTTPAuthorizationCredentials = Security(http_bearer),
) -> UserOut:
    """
    Return the current authenticated user's details along with a freshly generated access token.
    Authentication: Bearer access token (no Admin-ID required).
    """
    return current_user

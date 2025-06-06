from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """
    Schema for access token response
    """
    access_token: str
    refresh_token: str
    token_type: str


class TokenPayload(BaseModel):
    """
    Schema for JWT token payload
    """
    sub: Optional[str] = None  # User ID
    type: Optional[str] = None  # Token type: access or refresh

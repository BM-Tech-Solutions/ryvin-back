from typing import Any, Dict, Optional

from fastapi import Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


def _is_protected_path(path: str) -> bool:
    """
    Keep the same rules used previously: protect all API v1 paths, skip docs and root.
    """
    if (
        path.endswith("/docs")
        or path.endswith("/openapi.json")
        or path.endswith("/redoc")
        or path == "/"
    ):
        return False
    return path.startswith(f"{settings.API_V1_STR}/")


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token using HS256 and SECRET_KEY from settings.
    Raises HTTP 401 on failure.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        # jose raises if expired; ensure minimal expected fields
        if "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT payload"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired JWT token"
        )


async def get_jwt_payload(
    authorization: Optional[str] = Header(
        default=None, description="Authorization: Bearer <token>"
    ),
) -> Dict[str, Any]:
    """
    Dependency that requires a valid Bearer JWT and returns its payload.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
    token = authorization.split(" ", 1)[1].strip()
    return decode_jwt_token(token)


class CombinedAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that authorizes requests to protected paths if EITHER:
    - a valid API-Token/X-API-Key header equals settings.API_TOKEN (backward compatible), OR
    - a valid Authorization: Bearer <JWT> signed with SECRET_KEY (HS256).

    On successful JWT validation, the decoded payload is attached to request.state.jwt_payload.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip for non-protected paths
        if not _is_protected_path(request.url.path):
            return await call_next(request)

        # 1) API-Token compatibility path
        api_token = request.headers.get("API-Token") or request.headers.get("X-API-Key")
        if api_token and api_token == settings.API_TOKEN:
            return await call_next(request)

        # 2) Authorization: Bearer <JWT>
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            try:
                payload = decode_jwt_token(token)
                # attach payload for downstream usage if needed
                request.state.jwt_payload = payload
                return await call_next(request)
            except HTTPException:
                # fall through to 401 below
                pass

        # Neither valid API-Token nor valid JWT provided
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or missing credentials (API-Token or Bearer JWT required)"},
        )

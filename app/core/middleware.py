from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class APITokenMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate API token for protected endpoints
    """

    async def dispatch(self, request: Request, call_next):
        # Skip API token validation for non-protected paths
        if not self._is_protected_path(request.url.path):
            return await call_next(request)

        # Get API token from headers
        api_token = request.headers.get("API-Token")

        # Validate API token
        if not api_token or api_token != settings.API_TOKEN:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or missing API token"},
            )

        # Continue processing the request
        return await call_next(request)

    def _is_protected_path(self, path: str) -> bool:
        """
        Check if the path requires API token validation
        """
        # Skip validation for docs and openapi.json
        if path.endswith("/docs") or path.endswith("/openapi.json") or path.endswith("/redoc"):
            return False

        # List of API paths that require token validation
        protected_paths = [
            f"{settings.API_V1_STR}/auth/verify-phone",
            f"{settings.API_V1_STR}/auth/register-with-token",
            f"{settings.API_V1_STR}/auth/social-login",
        ]

        return any(path.startswith(prefix) for prefix in protected_paths)

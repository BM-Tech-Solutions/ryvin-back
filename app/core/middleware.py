from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class APITokenMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate API token for protected endpoints
    """

    async def dispatch(self, request: Request, call_next):
        if self._is_protected_path(request.url.path):
            # Get API token from headers (support both API-Token and X-API-Key)
            api_token = request.headers.get("API-Token") or request.headers.get("X-API-Key")

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
        # Skip validation for docs, openapi.json, redoc, and root path
        if (
            path.endswith("/docs")
            or path.endswith("/openapi.json")
            or path.endswith("/redoc")
            or path.endswith("/twilio/chat-webhook")
            or path.endswith("/twilio/video-webhook")
            or path.endswith("/twilio/voice-webhook")
            or path.endswith("/twilio/voice-request")
            or path == "/"
        ):
            return False

        # Protect all API v1 endpoints
        return path.startswith(f"{settings.API_V1_STR}/")

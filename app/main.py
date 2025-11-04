from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.exceptions import ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader, HTTPBearer
from fastapi.staticfiles import StaticFiles
from psycopg2.errors import UniqueViolation
from pydantic_core import ValidationError
from sqlalchemy.exc import IntegrityError

from firebase import init_firebase

from .core.auth import CombinedAuthMiddleware
from .core.config import settings
from .cron_jobs import scheduler
from .services.twilio_service import TwilioService

# Define security schemes for Swagger docs
api_key_header = APIKeyHeader(name="API-Token", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


# code to run before app startup & after app shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # firebase
    init_firebase()
    print("firebase initialized successfuly")

    # register twilio webhook
    twilio_service = TwilioService()
    twilio_service.register_chat_webhook()
    twilio_service.register_voice_webhook()

    # periodic jobs schedule
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API for Ryvin Dating Application",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan,
)


# Custom OpenAPI schema with security
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Merge security schemes (API key and Bearer JWT) without clobbering FastAPI defaults
    components = openapi_schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})

    # Ensure API key header scheme exists (keep existing if already present)
    security_schemes.setdefault(
        "APIKeyHeader",
        {
            "type": "apiKey",
            "in": "header",
            "name": "API-Token",
            "description": "API token for protected endpoints",
        },
    )

    # Ensure Bearer scheme name matches FastAPI's default: 'HTTPBearer'
    security_schemes.setdefault(
        "HTTPBearer",
        {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Bearer token (Authorization: Bearer <token>)",
        },
    )

    # Apply security globally as AND (require both API key and Bearer)
    # Use the exact scheme names present in components
    openapi_schema["security"] = [{"APIKeyHeader": [], "HTTPBearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the media directory at the /media URL path
app.mount("/media", StaticFiles(directory="media"), name="media")

# Add combined auth middleware (accepts API-Token or Bearer JWT)
app.add_middleware(CombinedAuthMiddleware)


# exception handlers
@app.exception_handler(IntegrityError)
async def sa_integrity_exception_handler(request, exc: IntegrityError):
    if isinstance(exc.orig, UniqueViolation):
        return JSONResponse({"detail": exc.orig.pgerror}, status_code=status.HTTP_401_UNAUTHORIZED)
    return JSONResponse({"detail": exc.args}, status_code=status.HTTP_400_BAD_REQUEST)


@app.exception_handler(ValidationError)
async def pydantic_validation_error_handler(request, exc: ValidationError):
    return JSONResponse({"detail": exc.errors()}, status_code=status.HTTP_400_BAD_REQUEST)


@app.exception_handler(ResponseValidationError)
async def response_validation_error_handler(request, exc: ResponseValidationError):
    return JSONResponse({"detail": exc.errors()}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Import and include API routers
from app.api.api_v1.api import api_router  # noqa: E402, I001

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "Welcome to Ryvin Dating API. See /docs for API documentation."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

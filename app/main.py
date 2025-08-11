from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi import status as http_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import Response
from fastapi.security import APIKeyHeader, HTTPBearer
from pydantic_core import ValidationError as PydanticValidationError

from firebase import init_firebase

from .core.auth import CombinedAuthMiddleware
from .core.config import settings
from .cron_jobs import scheduler

# Define security schemes for Swagger docs
api_key_header = APIKeyHeader(name="API-Token", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


# code to run before app startup & after app shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # firebase
    init_firebase()
    print("firebase initialized successfuly")

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

    # Add security schemes (API key and Bearer JWT)
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "API-Token",
            "description": "API token for protected endpoints",
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Bearer token (Authorization: Bearer <token>)",
        },
    }

    # Apply security globally as AND (require both API key and Bearer)
    # In OpenAPI, a single object includes schemes that are ANDed together.
    openapi_schema["security"] = [{"APIKeyHeader": [], "BearerAuth": []}]

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

# Add combined auth middleware (accepts API-Token or Bearer JWT)
app.add_middleware(CombinedAuthMiddleware)

# Import and include API routers
from app.api.api_v1.api import api_router  # noqa: E402, I001

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(PydanticValidationError)
async def pydantic_error_handler(request: Request, exc: PydanticValidationError):
    return Response(
        status_code=http_status.HTTP_400_BAD_REQUEST,
        content=exc.json(),
        media_type="application/json",
    )


@app.get("/")
async def root():
    return {"message": "Welcome to Ryvin Dating API. See /docs for API documentation."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

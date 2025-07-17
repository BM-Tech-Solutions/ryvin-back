from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader

from app.core.config import settings
from app.core.middleware import APITokenMiddleware
from firebase import init_firebase

# Define API key security scheme for Swagger docs
api_key_header = APIKeyHeader(name="API-Token", auto_error=False)


# code to run before app startup & after app shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_firebase()
    print("firebase initialized successfuly")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API for Ryvin Dating Application",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan,
)


# Custom OpenAPI schema with security
# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema

#     openapi_schema = get_openapi(
#         title=app.title,
#         version=app.version,
#         description=app.description,
#         routes=app.routes,
#     )

#     # Add API key security scheme
#     openapi_schema["components"] = openapi_schema.get("components", {})
#     openapi_schema["components"]["securitySchemes"] = {
#         "APIKeyHeader": {
#             "type": "apiKey",
#             "in": "header",
#             "name": "API-Token",
#             "description": "API token for protected endpoints",
#         }
#     }

#     # Apply security globally
#     openapi_schema["security"] = [{"APIKeyHeader": []}]

#     app.openapi_schema = openapi_schema
#     return app.openapi_schema


# app.openapi = custom_openapi

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API token middleware
app.add_middleware(APITokenMiddleware)

# Import and include API routers
from app.api.api_v1.api import api_router  # noqa: E402, I001

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "Welcome to Ryvin Dating API. See /docs for API documentation."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

from fastapi import APIRouter, Security

from app.api.api_v1.endpoints import admin, auth, journey, matches, photos, questionnaire
from app.main import api_key_header, http_bearer

api_router = APIRouter(
    dependencies=[
        Security(api_key_header),  # non-enforcing, auto_error=False
        Security(http_bearer),  # non-enforcing, auto_error=False
    ]
)

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(photos.router, prefix="/photo", tags=["photo"])
api_router.include_router(questionnaire.router, prefix="/questionnaire", tags=["questionnaire"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(journey.router, prefix="/journey", tags=["journey"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

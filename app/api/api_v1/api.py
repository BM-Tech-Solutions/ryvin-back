from fastapi import APIRouter

from app.api.api_v1.endpoints import admin, auth, journey, matches, photos, questionnaire

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(photos.router, prefix="/photos", tags=["photo"])
api_router.include_router(questionnaire.router, prefix="/questionnaire", tags=["questionnaire"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(journey.router, prefix="/journeys", tags=["journey"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

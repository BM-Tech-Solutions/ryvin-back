from fastapi import APIRouter

from app.api.api_v1.endpoints import admin, auth, journey, matches, profile, questionnaire

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(questionnaire.router, prefix="/questionnaire", tags=["questionnaire"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(journey.router, prefix="/journey", tags=["journey"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

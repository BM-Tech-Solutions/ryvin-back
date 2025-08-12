from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.schemas.questionnaire import (
    CategoryOut,
    QuestionnaireCreate,
    QuestionnaireInDB,
    QuestionnaireUpdate,
)
from app.services.questionnaire_service import QuestionnaireService

router = APIRouter()


@router.get(
    "/me",
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
def get_questionnaire(
    session: SessionDep,
    current_user: VerifiedUserDep,
):
    """
    Get current user's questionnaire
    """
    quest_service = QuestionnaireService(session)
    questionnaire = quest_service.get_questionnaire(current_user.id)
    if not questionnaire:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Questionnaire not found"
        )
    return QuestionnaireInDB.model_validate(questionnaire).model_dump()


@router.put(
    "/me",
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
def update_questionnaire(
    session: SessionDep,
    current_user: VerifiedUserDep,
    questionnaire_in: QuestionnaireUpdate,
) -> QuestionnaireInDB:
    """
    Update current user's questionnaire
    """
    quest_service = QuestionnaireService(session)
    quest = quest_service.get_or_create_questionnaire(current_user.id)
    quest = quest_service.update_questionnaire(quest, questionnaire_in)
    return quest


@router.post(
    "/me",
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
def create_questionnaire(
    session: SessionDep,
    current_user: VerifiedUserDep,
    questionnaire_in: QuestionnaireCreate,
) -> QuestionnaireInDB:
    """
    Create new Questionnaire for the current user
    """
    quest_service = QuestionnaireService(session)
    quest = quest_service.get_questionnaire(current_user.id)
    if quest:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST, detail="User already has a Questionnaire"
        )
    quest = quest_service.create_questionnaire(current_user.id, questionnaire_in)
    return quest


@router.post(
    "/complete",
    status_code=http_status.HTTP_200_OK,
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
def complete_questionnaire(
    session: SessionDep,
    current_user: VerifiedUserDep,
) -> Any:
    """
    Mark questionnaire as completed
    """
    quest_service = QuestionnaireService(session)
    quest = quest_service.get_questionnaire(current_user.id)
    if not quest:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Questionnaire not found"
        )

    quest = quest_service.complete_questionnaire(current_user.id)

    if not quest.is_complete():
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Questionnaire is incomplete. Missing field: {quest_service.get_missing_required_fields(quest)}",
        )

    return {
        "message": "Questionnaire completed successfully",
        "completed_at": quest.completed_at,
    }


@router.get("/categories", response_model=list[CategoryOut])
def get_questions_by_categories(session: SessionDep):
    """
    Get all questionnaire questions organized by categories from the database
    """
    quest_service = QuestionnaireService(session)
    return quest_service.get_questions_by_categories()

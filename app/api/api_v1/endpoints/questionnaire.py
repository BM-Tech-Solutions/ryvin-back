from fastapi import APIRouter, HTTPException
from fastapi import status as http_status

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.schemas.questionnaire import (
    CategoryOut,
    QuestionnaireCreate,
    QuestionnaireOut,
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
) -> QuestionnaireOut:
    """
    Get current user's questionnaire
    """
    quest_service = QuestionnaireService(session)
    questionnaire = quest_service.get_user_quest(current_user.id)
    return questionnaire


@router.put(
    "/me",
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
def update_questionnaire(
    session: SessionDep,
    current_user: VerifiedUserDep,
    questionnaire_in: QuestionnaireUpdate,
) -> QuestionnaireOut:
    """
    Update current user's questionnaire
    """
    quest_service = QuestionnaireService(session)
    quest = quest_service.get_user_quest(current_user.id, raise_exc=False)
    if quest:
        quest = quest_service.update_questionnaire(quest, questionnaire_in)
    else:
        quest = quest_service.create_questionnaire(current_user.id, questionnaire_in)
    return quest


@router.post(
    "/me",
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
def create_questionnaire(
    session: SessionDep,
    current_user: VerifiedUserDep,
    questionnaire_in: QuestionnaireCreate,
) -> QuestionnaireOut:
    """
    Create new Questionnaire for the current user
    """
    quest_service = QuestionnaireService(session)
    quest = quest_service.get_user_quest(current_user.id, raise_exc=False)
    if quest:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="User already has a Questionnaire",
        )
    return quest_service.create_questionnaire(current_user.id, questionnaire_in)


@router.post(
    "/complete",
    status_code=http_status.HTTP_200_OK,
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
def complete_questionnaire(
    session: SessionDep,
    current_user: VerifiedUserDep,
) -> QuestionnaireOut:
    """
    Mark questionnaire as completed
    """
    quest_service = QuestionnaireService(session)
    quest = quest_service.get_user_quest(current_user.id)
    quest = quest_service.complete_questionnaire(quest)

    if not quest.is_complete():
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Questionnaire is incomplete. Missing field: {quest_service.get_missing_required_fields(quest)}",
        )

    return quest


@router.get("/all-fields", response_model=list[CategoryOut])
def get_all_fields(session: SessionDep, current_user: VerifiedUserDep) -> list[CategoryOut]:
    """
    Get all questionnaire questions organized by categories from the database
    """
    quest_service = QuestionnaireService(session)
    return quest_service.get_questions_by_categories()


@router.get("/null-fields", response_model=list[CategoryOut])
def get_null_field(session: SessionDep, current_user: VerifiedUserDep) -> list[CategoryOut]:
    """
    Get all null fields (not answered questions) by current user
    """
    if not current_user.questionnaire:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Current User has no Questionnaire",
        )

    quest_service = QuestionnaireService(session)
    categories = quest_service.get_questions_by_categories()
    for category in categories:
        category.fields = [
            f for f in category.fields if not current_user.questionnaire.is_field_answered(f.name)
        ]

    return categories

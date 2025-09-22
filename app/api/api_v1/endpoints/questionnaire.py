from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.schemas.questionnaire import (
    AnsweredCategoryOut,
    CategoryOut,
    QuestionnaireCreate,
    QuestionnaireOut,
    QuestionnaireUpdate,
)
from app.services.questionnaire_service import QuestionnaireService

router = APIRouter()


@router.get(
    "/me",
    response_model=QuestionnaireOut,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_questionnaire(
    session: SessionDep,
    current_user: VerifiedUserDep,
) -> QuestionnaireOut:
    """
    Get current user's questionnaire
    """
    quest_service = QuestionnaireService(session)
    questionnaire = quest_service.get_questionnaire(current_user.id)
    if not questionnaire:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Questionnaire not found"
        )
    return questionnaire


@router.put(
    "/me",
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
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
    quest = quest_service.get_or_create_questionnaire(current_user.id)
    quest = quest_service.update_questionnaire(quest, questionnaire_in)
    return quest


@router.post(
    "/me",
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
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
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
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

    quest = quest_service.complete_questionnaire(quest)

    if not quest.is_complete():
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Questionnaire is incomplete. Missing field: {quest_service.get_missing_required_fields(quest)}",
        )

    return {
        "message": "Questionnaire completed successfully",
        "completed_at": quest.completed_at,
    }


@router.get(
    "/all-fields",
    response_model=list[CategoryOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_all_fields(session: SessionDep, current_user: VerifiedUserDep) -> list[CategoryOut]:
    """
    Get all questionnaire questions organized by categories from the database
    """
    quest_service = QuestionnaireService(session)
    return quest_service.get_all_categories()


@router.get(
    "/me/null-fields",
    response_model=list[CategoryOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_null_field(session: SessionDep, current_user: VerifiedUserDep) -> list[CategoryOut]:
    """
    Get all null fields (not answered questions) by current user
    """
    quest_service = QuestionnaireService(session)
    categories = quest_service.get_all_categories()
    if not current_user.questionnaire:
        return categories
    for category in categories:
        for sub_category in category.sub_categories:
            sub_category.fields = [
                f
                for f in sub_category.fields
                if not current_user.questionnaire.is_field_answered(f.name)
            ]

    return categories


@router.get(
    "/me/answered-fields",
    response_model=list[AnsweredCategoryOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_answered_field(
    session: SessionDep, current_user: VerifiedUserDep
) -> list[AnsweredCategoryOut]:
    """
    Get all answered fields by current user
    """
    quest_service = QuestionnaireService(session)
    categories = quest_service.get_all_categories()
    if not current_user.questionnaire:
        return categories
    for category in categories:
        for sub_category in category.sub_categories:
            fields = []
            for field in sub_category.fields:
                if current_user.questionnaire.is_field_answered(field.name):
                    field.answer = getattr(current_user.questionnaire, field.name)
                    fields.append(field)
            sub_category.fields = fields

    return categories

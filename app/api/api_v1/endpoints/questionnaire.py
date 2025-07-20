from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.schemas.questionnaire import QuestionnaireCreate, QuestionnaireInDB, QuestionnaireUpdate
from app.services.questionnaire_service import QuestionnaireService

router = APIRouter()


@router.get("/me")
def get_questionnaire(
    session: SessionDep,
    current_user: VerifiedUserDep,
    exclude_null: bool = False,
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
    return QuestionnaireInDB.model_validate(questionnaire).model_dump(exclude_none=exclude_null)


@router.put("/me")
def update_questionnaire(
    session: SessionDep,
    current_user: VerifiedUserDep,
    questionnaire_in: QuestionnaireUpdate,
) -> QuestionnaireInDB:
    """
    Update current user's questionnaire
    """
    quest_service = QuestionnaireService(session)
    quest = quest_service.update_questionnaire(current_user.id, questionnaire_in)
    return quest


@router.post("/me")
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


@router.post("/complete", status_code=http_status.HTTP_200_OK)
def complete_questionnaire(
    session: SessionDep,
    current_user: VerifiedUserDep,
) -> Any:
    """
    Mark questionnaire as completed
    """
    quest_service = QuestionnaireService(session)
    quest = quest_service.complete_questionnaire(current_user.id)

    if not quest:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Questionnaire not found"
        )

    if not quest.is_complete():
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Questionnaire is incomplete. Missing field: {quest_service.get_missing_fields(quest)}",
        )

    return {
        "message": "Questionnaire completed successfully",
        "completed_at": quest.completed_at,
    }


@router.get("/categories", response_model=Dict[str, Any])
def get_questions_by_categories(session: SessionDep) -> Any:
    """
    Get all questionnaire questions organized by categories from the database
    """
    quest_service = QuestionnaireService(session)
    categories = quest_service.get_questions_by_categories()
    return {"categories": categories}

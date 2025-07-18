from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.schemas.questionnaire import QuestionnaireCreate, QuestionnaireInDB, QuestionnaireUpdate
from app.services.questionnaire_service import QuestionnaireService

router = APIRouter()


@router.get("/me")
def get_questionnaire(
    db: SessionDep,
    current_user: VerifiedUserDep,
    exclude_null: bool = False,
):
    """
    Get current user's questionnaire
    """
    questionnaire_service = QuestionnaireService(db)
    questionnaire = questionnaire_service.get_questionnaire(current_user.id)
    if not questionnaire:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found")
    return QuestionnaireInDB.model_validate(questionnaire).model_dump(exclude_none=exclude_null)


@router.put("/me")
def update_questionnaire(
    db: SessionDep,
    current_user: VerifiedUserDep,
    questionnaire_in: QuestionnaireUpdate,
) -> QuestionnaireInDB:
    """
    Update current user's questionnaire
    """
    questionnaire_service = QuestionnaireService(db)
    questionnaire = questionnaire_service.update_questionnaire(current_user.id, questionnaire_in)
    return questionnaire


@router.post("/me")
def create_questionnaire(
    db: SessionDep,
    current_user: VerifiedUserDep,
    questionnaire_in: QuestionnaireCreate,
) -> QuestionnaireInDB:
    """
    Create new Questionnaire for the current user
    """
    questionnaire_service = QuestionnaireService(db)
    quest = questionnaire_service.get_questionnaire(current_user.id)
    if quest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already has a Questionnaire"
        )
    quest = questionnaire_service.create_questionnaire(current_user.id, questionnaire_in)
    return quest


@router.post("/complete", status_code=status.HTTP_200_OK)
def complete_questionnaire(
    db: SessionDep,
    current_user: VerifiedUserDep,
) -> Any:
    """
    Mark questionnaire as completed
    """
    quest_service = QuestionnaireService(db)
    quest = quest_service.complete_questionnaire(current_user.id)

    if not quest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found")

    if not quest.is_complete():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Questionnaire is incomplete. Missing field: {quest_service.get_missing_fields(quest)}",
        )

    return {
        "message": "Questionnaire completed successfully",
        "completed_at": quest.completed_at,
    }


@router.get("/categories", response_model=Dict[str, Any])
def get_questions_by_categories(db: SessionDep) -> Any:
    """
    Get all questionnaire questions organized by categories from the database
    """
    questionnaire_service = QuestionnaireService(db)
    categories = questionnaire_service.get_questions_by_categories()
    return {"categories": categories}

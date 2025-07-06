from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_verified_user
from app.models.user import User
from app.schemas.questionnaire import QuestionnaireCreate, QuestionnaireUpdate
from app.services.questionnaire_service import QuestionnaireService

router = APIRouter()


@router.get("/me")
def get_questionnaire(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get current user's questionnaire
    """
    questionnaire_service = QuestionnaireService(db)
    questionnaire = questionnaire_service.get_questionnaire(current_user.id)
    return questionnaire


@router.put("/me")
def update_questionnaire(
    questionnaire_in: QuestionnaireUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update current user's questionnaire
    """
    questionnaire_service = QuestionnaireService(db)
    questionnaire = questionnaire_service.update_questionnaire(current_user.id, questionnaire_in)
    return questionnaire


@router.post("/complete", status_code=status.HTTP_200_OK)
def complete_questionnaire(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Mark questionnaire as completed
    """
    questionnaire_service = QuestionnaireService(db)
    result = questionnaire_service.complete_questionnaire(current_user.id)
    
    return {
        "message": "Questionnaire completed successfully",
        "completed_at": result.completed_at
    }


@router.get("/categories", response_model=Dict[str, Any])
def get_questions_by_categories(
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all questionnaire questions organized by categories from the database
    """
    questionnaire_service = QuestionnaireService(db)
    categories = questionnaire_service.get_questions_by_categories()
    return {"categories": categories}

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.security import utc_now
from app.models import (
    Questionnaire,
    QuestionnaireCategory,
    QuestionnaireField,
    QuestionnaireSubCategory,
)
from app.schemas.questionnaire import QuestionnaireCreate, QuestionnaireUpdate

from .base_service import BaseService


class QuestionnaireService(BaseService):
    """
    Service for questionnaire-related operations
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.session = db

    def get_questionnaire(self, user_id: UUID) -> Optional[Questionnaire]:
        """
        Get user questionnaire by user ID
        """
        return self.session.query(Questionnaire).filter(Questionnaire.user_id == user_id).first()

    def create_questionnaire(self, user_id: UUID, quest_in: QuestionnaireCreate) -> Questionnaire:
        """
        Create an empty questionnaire for a user
        """
        quest_data = quest_in.model_dump(exclude_unset=True)
        questionnaire = Questionnaire(**quest_data, user_id=user_id)
        self.session.add(questionnaire)
        self.session.commit()
        self.session.refresh(questionnaire)
        return questionnaire

    def get_or_create_questionnaire(self, user_id: UUID) -> Questionnaire:
        """
        Get existing questionnaire or create a new one
        """
        questionnaire = self.get_questionnaire(user_id)
        if not questionnaire:
            # Create an empty questionnaire with default values
            questionnaire = Questionnaire(user_id=user_id)
            self.session.add(questionnaire)
            self.session.commit()
            self.session.refresh(questionnaire)
        return questionnaire

    def update_questionnaire(
        self, quest: Questionnaire, questionnaire_data: QuestionnaireUpdate
    ) -> Questionnaire:
        """
        Update user questionnaire
        """
        update_data = questionnaire_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(quest, field, value)

        self.session.commit()
        self.session.refresh(quest)
        return quest

    def complete_questionnaire(self, quest: Questionnaire) -> Optional[Questionnaire]:
        """
        Mark questionnaire as completed and update user record
        """
        # Check if all required fields are filled
        completed = not self.get_missing_required_fields(quest)

        # Mark questionnaire as completed
        quest.completed_at = utc_now() if completed else None

        # Update user record
        quest.user.has_completed_questionnaire = completed

        self.session.commit()
        self.session.refresh(quest)
        return quest

    def get_all_categories(self) -> list[QuestionnaireCategory]:
        stmt = select(QuestionnaireCategory).options(
            selectinload(QuestionnaireCategory.sub_categories).options(
                selectinload(QuestionnaireSubCategory.fields).options(
                    selectinload(QuestionnaireField.children)
                )
            )
        )

        return self.session.execute(stmt).scalars().all()

    def get_required_fields(self) -> list[QuestionnaireField]:
        return (
            self.session.query(QuestionnaireField)
            .filter(QuestionnaireField.required.is_(True))
            .all()
        )

    def get_missing_required_fields(self, quest: Questionnaire):
        return [
            field.name
            for field in self.get_required_fields()
            if getattr(quest, field.name, None) in (None, "", [])
        ]

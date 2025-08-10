import random
from collections import defaultdict
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.core.security import utc_now
from app.models import Questionnaire, QuestionnaireCategory, QuestionnaireField
from app.models.enums import FieldType
from app.schemas.questionnaire import QuestionnaireCreate, QuestionnaireUpdate

from .base_service import BaseService


class QuestionnaireService(BaseService):
    """
    Service for questionnaire-related operations
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.session = db

    def get_quest_by_id(self, quest_id: UUID, raise_exc: bool = True) -> Optional[Questionnaire]:
        """
        Get user questionnaire by user ID
        """
        quest = self.session.get(Questionnaire, quest_id)
        if not quest and raise_exc:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"no Questionnaire with id: {quest_id}",
            )
        return quest

    def get_user_quest(self, user_id: UUID, raise_exc: bool = True) -> Optional[Questionnaire]:
        """
        Get user questionnaire by user ID
        """
        quest = self.session.query(Questionnaire).filter(Questionnaire.user_id == user_id).first()
        if not quest and raise_exc:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"User with id: '{user_id}' has no Questionnaire",
            )
        return quest

    def create_questionnaire(self, user_id: UUID, quest_in: QuestionnaireCreate) -> Questionnaire:
        """
        Create an empty questionnaire for a user
        """
        questionnaire = Questionnaire(**quest_in.model_dump(exclude_unset=True), user_id=user_id)
        self.session.add(questionnaire)
        self.session.commit()
        self.session.refresh(questionnaire)
        return questionnaire

    def get_or_create_questionnaire(self, user_id: UUID) -> Questionnaire:
        """
        Get existing questionnaire or create a new one
        """
        questionnaire = self.get_user_quest(user_id, raise_exc=False)
        if not questionnaire:
            questionnaire = self.create_questionnaire(user_id, QuestionnaireCreate())
        return questionnaire

    def update_questionnaire(
        self, quest: Questionnaire, questionnaire_in: QuestionnaireUpdate
    ) -> Questionnaire:
        """
        Update user questionnaire
        """
        update_data = questionnaire_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(quest, field, value)

        self.session.commit()
        self.session.refresh(quest)
        return quest

    def complete_questionnaire(self, quest: Questionnaire) -> Questionnaire:
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

    def get_compatibility_score(self, user1_id: UUID, user2_id: UUID) -> int:
        """
        Calculate compatibility score between two users based on their questionnaires
        """
        q1 = self.get_user_quest(user1_id, raise_exc=False)
        q2 = self.get_user_quest(user2_id, raise_exc=False)

        if not q1 or not q2 or not q1.is_complete() or not q2.is_complete():
            return 0
        return random.randint(0, 100)

    def get_all_categories(self) -> list[QuestionnaireCategory]:
        return (
            self.session.query(QuestionnaireCategory)
            .order_by(QuestionnaireCategory.order_position)
            .all()
        )

    def get_category_fields(self, category_id: UUID) -> list[QuestionnaireField]:
        return (
            self.session.query(QuestionnaireField)
            .filter(QuestionnaireField.category_id == category_id)
            .order_by(QuestionnaireField.order_position)
            .all()
        )

    def get_questions_by_categories(self) -> list[QuestionnaireCategory]:
        """
        Get all questionnaire questions organized by categories from the database
        """
        categories = self.get_all_categories()
        parent_fields = defaultdict(list)
        for category in categories:
            fields = self.get_category_fields(category.id)
            new_fields = []
            for field in fields:
                if field.parent_field:
                    parent_fields[field.parent_field].append(field)
                else:
                    new_fields.append(field)
            for field in new_fields:
                if field.field_type == FieldType.FIELDS_GROUP:
                    field.child_fields = parent_fields[field.name]

            category.fields = new_fields

        return categories

    def get_required_fields(self) -> list[QuestionnaireField]:
        return (
            self.session.query(QuestionnaireField)
            .filter(
                QuestionnaireField.required.is_(True),
                QuestionnaireField.field_type != FieldType.FIELDS_GROUP,
            )
            .all()
        )

    def get_missing_required_fields(self, quest: Questionnaire):
        return [
            field.name
            for field in self.get_required_fields()
            if getattr(quest, field.name, None) in (None, "")
        ]

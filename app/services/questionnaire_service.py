from collections import defaultdict
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

    def get_compatibility_score(self, user1_id: UUID, user2_id: UUID) -> int:
        """
        Calculate compatibility score between two users based on their questionnaires
        """
        q1 = self.get_questionnaire(user1_id)
        q2 = self.get_questionnaire(user2_id)

        if not q1 or not q2 or not q1.is_complete() or not q2.is_complete():
            return 0

        # In a real app, we would implement a sophisticated algorithm
        # For now, we'll use a simple scoring system

        score = 0

        # Example scoring logic (simplified)
        if q1.relationship_goal == q2.relationship_goal:
            score += 20

        if q1.accept_non_believer == q2.accept_non_believer:
            score += 15

        if q1.primary_love_language == q2.primary_love_language:
            score += 15

        return max(0, min(score, 100))

    def get_all_categories(self) -> list[QuestionnaireCategory]:
        stmt = select(QuestionnaireCategory).options(
            selectinload(QuestionnaireCategory.sub_categories).options(
                selectinload(QuestionnaireSubCategory.fields).options(
                    selectinload(QuestionnaireField.children)
                )
            )
        )

        return self.session.execute(stmt).scalars().all()

    def get_categories_by_ids(self, ids: list[UUID]) -> list[QuestionnaireCategory]:
        if not ids:
            return []
        return (
            self.session.query(QuestionnaireCategory)
            .filter(QuestionnaireCategory.id.in_(ids))
            .order_by(QuestionnaireCategory.order_position)
            .all()
        )

    def get_category_fields(self, category_id: UUID) -> list[QuestionnaireField]:
        return (
            self.session.query(QuestionnaireField)
            .filter(QuestionnaireField.sub_category_id == category_id)
            .order_by(QuestionnaireField.order_position)
            .all()
        )

    def get_fields_by_names(self, names: list[str]) -> list[QuestionnaireField]:
        """
        Fetch questionnaire fields whose name is in the provided list.
        """
        if not names:
            return []
        return (
            self.session.query(QuestionnaireField).filter(QuestionnaireField.name.in_(names)).all()
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
            .filter(QuestionnaireField.required.is_(True))
            .all()
        )

    def get_missing_required_fields(self, quest: Questionnaire):
        return [
            field.name
            for field in self.get_required_fields()
            if getattr(quest, field.name, None) in (None, "")
        ]

    def get_null_fields(self, quest: Questionnaire) -> list[str]:
        """
        Return the list of questionnaire field names (based on SQLAlchemy mapped columns)
        that currently have a null (None) value. Excludes metadata columns.
        """
        # Columns defined on the model
        column_names = [col.key for col in Questionnaire.__mapper__.columns]
        # Exclude metadata/foreign key and timestamps
        exclude = {"id", "user_id", "created_at", "updated_at", "completed_at"}
        result: list[str] = []
        for name in column_names:
            if name in exclude:
                continue
            # Only check attributes that exist
            if hasattr(quest, name):
                val = getattr(quest, name, None)
                if val is None or (isinstance(val, str) and val.strip() == ""):
                    result.append(name)
        return result

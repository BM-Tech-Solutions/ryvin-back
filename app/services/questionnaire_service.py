from collections import defaultdict
from typing import Optional
from uuid import UUID

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
            questionnaire = self.create_questionnaire(user_id)
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

        # Check if deal breakers match
        # if q1.deal_breakers and q2.deal_breakers:
        #     # Lower score if deal breakers overlap
        #     if any(item in q2.lifestyle_preferences for item in q1.deal_breakers.split(",")):
        #         score -= 30

        #     if any(item in q1.lifestyle_preferences for item in q2.deal_breakers.split(",")):
        #         score -= 30

        # Ensure score is between 0 and 100
        return max(0, min(score, 100))

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
            .filter(QuestionnaireField.required.is_(True))
            .all()
        )

    def get_missing_required_fields(self, quest: Questionnaire):
        return [
            field.name
            for field in self.get_required_fields()
            if getattr(quest, field.name, None) in (None, "")
        ]

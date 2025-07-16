from typing import Any, Dict, Optional
from uuid import UUID

from app.core.security import utc_now
from app.models import Questionnaire, QuestionnaireCategory, QuestionnaireField, User
from app.models.enums import FieldType, get_field_enum
from app.schemas.questionnaire import QuestionnaireCreate, QuestionnaireUpdate

from .base_service import BaseService


class QuestionnaireService(BaseService):
    """
    Service for questionnaire-related operations
    """

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
        self, user_id: UUID, questionnaire_data: QuestionnaireUpdate
    ) -> Questionnaire:
        """
        Update user questionnaire
        """
        questionnaire = self.get_or_create_questionnaire(user_id)

        update_data = questionnaire_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(questionnaire, field, value)

        self.session.commit()
        self.session.refresh(questionnaire)
        return questionnaire

    def complete_questionnaire(self, user_id: UUID) -> Optional[Questionnaire]:
        """
        Mark questionnaire as completed and update user record
        """
        questionnaire = self.get_questionnaire(user_id)
        if not questionnaire:
            return None

        # Check if all required fields are filled
        completed = not questionnaire.get_missing_fields()

        # Mark questionnaire as completed
        questionnaire.completed_at = utc_now() if completed else None

        # Update user record
        user = self.session.query(User).filter(User.id == user_id).first()
        if user:
            user.has_completed_questionnaire = completed

        self.session.commit()
        self.session.refresh(questionnaire)
        return questionnaire

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
        max_score = 100

        # Example scoring logic (simplified)
        if q1.relationship_goals == q2.relationship_goals:
            score += 20

        if q1.communication_style == q2.communication_style:
            score += 15

        if q1.love_language == q2.love_language:
            score += 15

        # Check if deal breakers match
        if q1.deal_breakers and q2.deal_breakers:
            # Lower score if deal breakers overlap
            if any(item in q2.lifestyle_preferences for item in q1.deal_breakers.split(",")):
                score -= 30

            if any(item in q1.lifestyle_preferences for item in q2.deal_breakers.split(",")):
                score -= 30

        # Ensure score is between 0 and 100
        return max(0, min(score, max_score))

    def get_questions_by_categories(self) -> Dict[str, Any]:
        """
        Get all questionnaire questions organized by categories from the database
        """
        # Query all categories ordered by their order_position field
        categories_db = (
            self.session.query(QuestionnaireCategory)
            .order_by(QuestionnaireCategory.order_position)
            .all()
        )

        # Build the response dictionary
        categories = {}

        for category in categories_db:
            # Query all fields for this category ordered by their order_position field
            fields_db = (
                self.session.query(QuestionnaireField)
                .filter(QuestionnaireField.category_id == category.id)
                .order_by(QuestionnaireField.order_position)
                .all()
            )

            # Build the fields list for this category
            fields = []
            for field in fields_db:
                field_data = {
                    "name": field.name,
                    "label": field.label,
                    "field_type": field.field_type,
                    "required": field.required,
                    "description": field.description or "",
                    "order_position": field.order_position,
                }

                # Add options if available
                if field.field_type in [FieldType.SELECT, FieldType.NESTED_SELECT]:
                    field_enum = get_field_enum(field.name)
                    field_data["options"] = field_enum.options() if field_enum else []

                fields.append(field_data)

            # Add the category to the response
            categories[category.name] = {
                "label": category.label,
                "description": category.description or "",
                "order_position": category.order_position,
                "fields": fields,
            }

        return categories

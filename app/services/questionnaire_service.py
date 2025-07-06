from typing import Optional, Dict, Any, List
from uuid import UUID

from fastapi import HTTPException, status

from app.models.user import User
from app.models.questionnaire import Questionnaire
from app.models.questionnaire_category import QuestionnaireCategory
from app.models.questionnaire_field import QuestionnaireField
from app.schemas.questionnaire import QuestionnaireUpdate
from .base_service import BaseService


class QuestionnaireService(BaseService):
    """
    Service for questionnaire-related operations
    """
    def get_questionnaire(self, user_id: UUID) -> Optional[Questionnaire]:
        """
        Get user questionnaire by user ID
        """
        return self.db.query(Questionnaire).filter(Questionnaire.user_id == user_id).first()
    
    def create_questionnaire(self, user_id: UUID) -> Questionnaire:
        """
        Create an empty questionnaire for a user
        """
        questionnaire = Questionnaire(user_id=user_id)
        self.db.add(questionnaire)
        self.db.commit()
        self.db.refresh(questionnaire)
        return questionnaire
    
    def get_or_create_questionnaire(self, user_id: UUID) -> Questionnaire:
        """
        Get existing questionnaire or create a new one
        """
        questionnaire = self.get_questionnaire(user_id)
        if not questionnaire:
            questionnaire = self.create_questionnaire(user_id)
        return questionnaire
    
    def update_questionnaire(self, user_id: UUID, questionnaire_data: QuestionnaireUpdate) -> Questionnaire:
        """
        Update user questionnaire
        """
        questionnaire = self.get_or_create_questionnaire(user_id)
        
        update_data = questionnaire_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(questionnaire, field, value)
        
        self.db.commit()
        self.db.refresh(questionnaire)
        return questionnaire
    
    def complete_questionnaire(self, user_id: UUID) -> bool:
        """
        Mark questionnaire as completed and update user record
        """
        questionnaire = self.get_questionnaire(user_id)
        if not questionnaire:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Questionnaire not found"
            )
        
        # Check if all required fields are filled
        required_fields = [
            "relationship_goals", "communication_style", "conflict_resolution",
            "love_language", "lifestyle_preferences", "values_and_beliefs",
            "future_plans", "deal_breakers"
        ]
        
        for field in required_fields:
            if getattr(questionnaire, field) is None or getattr(questionnaire, field) == "":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Questionnaire is incomplete. Missing field: {field}"
                )
        
        # Mark questionnaire as completed
        questionnaire.is_completed = True
        
        # Update user record
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.has_completed_questionnaire = True
        
        self.db.commit()
        return True
    
    def get_compatibility_score(self, user1_id: UUID, user2_id: UUID) -> int:
        """
        Calculate compatibility score between two users based on their questionnaires
        """
        q1 = self.get_questionnaire(user1_id)
        q2 = self.get_questionnaire(user2_id)
        
        if not q1 or not q2 or not q1.is_completed or not q2.is_completed:
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
            if any(item in q2.lifestyle_preferences for item in q1.deal_breakers.split(',')):
                score -= 30
            
            if any(item in q1.lifestyle_preferences for item in q2.deal_breakers.split(',')):
                score -= 30
        
        # Ensure score is between 0 and 100
        return max(0, min(score, max_score))
    
    def get_questions_by_categories(self) -> Dict[str, Any]:
        """
        Get all questionnaire questions organized by categories from the database
        """
        # Query all categories ordered by their order_position field
        categories_db = self.db.query(QuestionnaireCategory).order_by(QuestionnaireCategory.order_position).all()
        
        # Build the response dictionary
        categories = {}
        
        for category in categories_db:
            # Query all fields for this category ordered by their order_position field
            fields_db = self.db.query(QuestionnaireField).filter(
                QuestionnaireField.category_id == category.id
            ).order_by(QuestionnaireField.order_position).all()
            
            # Build the fields list for this category
            fields = []
            for field in fields_db:
                field_data = {
                    "name": field.name,
                    "label": field.label,
                    "field_type": field.field_type,
                    "required": field.required
                }
                
                # Add options if available
                if field.options:
                    field_data["options"] = field.options
                
                # Add description if available
                if field.description:
                    field_data["description"] = field.description
                    
                fields.append(field_data)
            
            # Add the category to the response
            categories[category.name] = {
                "title": category.display_name,
                "description": category.description,
                "fields": fields
            }
        
        return categories

from typing import Optional
from uuid import UUID

from app.models import Photo, Profile
from app.schemas.profile import ProfileCompletion, ProfileCreate, ProfileUpdate

from .base_service import BaseService
from .questionnaire_service import QuestionnaireService


class ProfileService(BaseService):
    """
    Service for profile-related operations
    """

    def get_profile(self, user_id: UUID) -> Optional[Profile]:
        """
        Get user profile by user id
        """
        return self.session.query(Profile).filter(Profile.user_id == user_id).first()

    def create_profile(self, user_id: UUID, profile_in: ProfileCreate) -> Profile:
        """
        Create new profile
        """
        profile_data = profile_in.model_dump(exclude_unset=True)
        profile = Profile(**profile_data, user_id=user_id)
        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def update_profile(self, profile: Profile, profile_in: ProfileUpdate) -> Profile:
        """
        Update user profile
        """
        update_data = profile_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(profile, field, value)

        self.session.commit()
        self.session.refresh(profile)
        return profile

    def get_profile_completion(self, user_id: UUID) -> Optional[ProfileCompletion]:
        """
        Calculate profile completion percentage and missing fields
        """
        profile = self.get_profile(user_id)
        if not profile:
            return None

        quest_service = QuestionnaireService(self.session)
        questionnaire = quest_service.get_questionnaire(user_id)
        if not questionnaire:
            return None

        # Check if user has photos
        has_photos = self.session.query(Photo).filter(Photo.user_id == user_id).count() > 0

        # check profile fields & count completed fields
        completed_fields = len(self.get_required_fields()) - len(self.get_missing_fields(profile))

        # Calculate completion percentage
        # Profile fields (60%), Photos (20%), Questionnaire (20%)
        profile_completion = (completed_fields / len(self.get_required_fields())) * 60
        photo_completion = 20 if has_photos else 0
        questionnaire_completion = 20 if questionnaire.is_complete() else 0

        total_completion = int(profile_completion + photo_completion + questionnaire_completion)

        return ProfileCompletion(
            completion_percentage=total_completion,
            missing_profile_fields=self.get_missing_fields(profile),
            missing_questionnaire_fields=quest_service.get_missing_fields(questionnaire),
            has_photos=has_photos,
            has_completed_questionnaire=questionnaire.is_complete(),
        )

    def get_required_fields(self):
        return [
            "first_name",
            "gender",
            "relationship_goal",
            "age",
            "city_of_residence",
            "nationality_cultural_origin",
            "languages_spoken",
            "professional_situation",
            "education_level",
            "previously_married",
        ]

    def get_missing_fields(self, profile: Profile):
        return [
            field_name
            for field_name in self.get_required_fields()
            if getattr(profile, field_name) in (None, "")
        ]

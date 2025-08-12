from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.security import utc_now
from app.models.journey import Journey
from app.models.match import Match
from app.models.user import User

from .base_service import BaseService
from .notification_service import NotificationService
from .questionnaire_service import QuestionnaireService


class MatchService(BaseService):
    """
    Service for match-related operations
    """

    def __init__(self, db: Session):
        # Initialize BaseService (sets self.db)
        super().__init__(db)
        # Backward-compatibility: methods reference self.session
        self.session = db

    def get_match_by_id(self, match_id: UUID) -> Optional[Match]:
        """
        Get match by ID
        """
        return self.session.get(Match, match_id)

    def get_match_by_users(self, user1_id: UUID, user2_id: UUID) -> Optional[Match]:
        """
        Get match between two users if it exists
        """
        return (
            self.session.query(Match)
            .filter(
                or_(
                    and_(Match.user1_id == user1_id, Match.user2_id == user2_id),
                    and_(Match.user1_id == user2_id, Match.user2_id == user1_id),
                )
            )
            .first()
        )

    def get_all_matches(self, skip: int = 0, limit: int = 100) -> List[Match]:
        """
        Get all matches in the system
        """
        return self.session.query(Match).offset(skip).limit(limit).all()

    def get_user_matches(
        self, user_id: UUID, status: str = None, skip: int = 0, limit: int = 100
    ) -> List[Match]:
        """
        Get all matches for a user
        """
        query = self.session.query(Match).filter(
            or_(Match.user1_id == user_id, Match.user2_id == user_id)
        )

        if status:
            query = query.filter(Match.status == status)

        return query.offset(skip).limit(limit).all()

    def create_match(self, user1_id: UUID, user2_id: UUID, compatibility_score: int) -> Match:
        """
        Create a new potential match
        """
        # Check if match already exists
        existing_match = self.get_match_by_users(user1_id, user2_id)
        if existing_match:
            return existing_match

        # Create new match
        match = Match(
            user1_id=user1_id,
            user2_id=user2_id,
            compatibility_score=compatibility_score,
            status="pending",
            user1_accepted=False,
            user2_accepted=False,
        )

        self.session.add(match)
        self.session.commit()
        self.session.refresh(match)

        # Send notification to user2
        user2 = self.session.get(User, user2_id)
        if user2:
            NotificationService().send_new_match_notification(user2, match)

        return match

    def discover_potential_matches(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Discover potential matches for a user
        """
        user = self.session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")

        # Get existing matches to exclude
        existing_match_users = []
        existing_matches = self.get_user_matches(user_id)
        for match in existing_matches:
            if match.user1_id == user_id:
                existing_match_users.append(match.user2_id)
            else:
                existing_match_users.append(match.user1_id)

        # Query for potential matches
        potential_matches_query = self.session.query(User).filter(
            User.id != user_id,
            User.is_active.is_(True),
            User.is_verified.is_(True),
            User.has_completed_questionnaire.is_(True),
        )

        # Filter by gender preference (simplified)
        if user.interested_in:
            potential_matches_query = potential_matches_query.filter(
                User.gender == user.interested_in
            )

        # Exclude existing matches
        if existing_match_users:
            potential_matches_query = potential_matches_query.filter(
                User.id.notin_(existing_match_users)
            )

        # Get potential matches
        potential_matches = potential_matches_query.offset(skip).limit(limit).all()

        # Calculate compatibility scores
        questionnaire_service = QuestionnaireService(self.session)
        result = []

        for potential_match in potential_matches:
            compatibility_score = questionnaire_service.get_compatibility_score(
                user_id, potential_match.id
            )

            result.append({"user": potential_match, "compatibility_score": compatibility_score})

        # Sort by compatibility score
        result.sort(key=lambda x: x["compatibility_score"], reverse=True)

        return result

    def accept_match(self, match_id: UUID, user_id: UUID) -> Match:
        """
        Accept a match
        """
        match = self.get_match_by_id(match_id)
        if not match:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="Match not found"
            )

        # Check if user is part of the match
        if match.user1_id != user_id and match.user2_id != user_id:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN, detail="User is not part of this match"
            )

        # Update match acceptance status
        if match.user1_id == user_id:
            match.user1_accepted = True
        else:
            match.user2_accepted = True

        # Check if both users have accepted
        if match.user1_accepted and match.user2_accepted:
            match.status = "matched"
            match.matched_at = utc_now()

            # Create a journey for the match
            journey = Journey(
                match_id=match.id,
                current_step=1,  # First step: pre-compatibility
                status="active",
            )
            self.session.add(journey)

            # Send notifications to both users
            user1 = self.session.get(User, match.user1_id)
            user2 = self.session.get(User, match.user2_id)

            if user1 and user2:
                NotificationService().send_match_confirmed_notification(user1, match)
                NotificationService().send_match_confirmed_notification(user2, match)

        self.session.commit()
        self.session.refresh(match)
        return match

    def decline_match(self, match_id: UUID, user_id: UUID) -> Match:
        """
        Decline a match
        """
        match = self.get_match_by_id(match_id)
        if not match:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="Match not found"
            )

        # Check if user is part of the match
        if match.user1_id != user_id and match.user2_id != user_id:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN, detail="User is not part of this match"
            )

        # Update match status
        match.status = "declined"

        # Set which user declined
        if match.user1_id == user_id:
            match.user1_accepted = False
        else:
            match.user2_accepted = False

        self.session.commit()
        self.session.refresh(match)
        return match

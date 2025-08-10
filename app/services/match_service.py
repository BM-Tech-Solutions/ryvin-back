from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.security import utc_now
from app.models.enums import JourneyStatus, JourneyStep, MatchStatus
from app.models.journey import Journey
from app.models.match import Match
from app.models.user import User
from app.schemas.match import MatchCreate, PotentialMatch

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

    def get_user_match(
        self, user_id: UUID, match_id: UUID, raise_exc: bool = True
    ) -> Optional[Match]:
        """
        Get User match by ID
        """
        match = (
            self.session.query(Match)
            .filter(
                Match.id == match_id,
                or_(
                    Match.user1_id == user_id,
                    Match.user2_id == user_id,
                ),
            )
            .first()
        )

        if not match and raise_exc:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"User has no Match with id: {match_id}",
            )
        return match

    def get_all_matches(self, skip: int = 0, limit: int = 100) -> List[Match]:
        """
        Get all matches in the system
        """
        return self.session.query(Match).offset(skip).limit(limit).all()

    def get_match_by_users(
        self, user1_id: UUID, user2_id: UUID, raise_exc: bool = True
    ) -> Optional[Match]:
        """
        Get match between two users if it exists
        """
        match = (
            self.session.query(Match)
            .filter(
                or_(
                    and_(Match.user1_id == user1_id, Match.user2_id == user2_id),
                    and_(Match.user1_id == user2_id, Match.user2_id == user1_id),
                )
            )
            .first()
        )

        if not match and raise_exc:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"No Match between users: {user1_id} and {user2_id}",
            )
        return match

    def get_user_matches(
        self,
        user_id: UUID,
        status: MatchStatus = None,
        skip: int = 0,
        limit: int = 100,
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

    def create_match(self, match_in: MatchCreate) -> Match:
        """
        Create a new potential match
        """
        # Create new match
        match = Match(
            user1_id=match_in.user1_id,
            user2_id=match_in.user2_id,
            compatibility_score=match_in.compatibility_score,
            user1_accepted=False,
            user2_accepted=False,
            status=MatchStatus.PENDING,
        )

        self.session.add(match)
        self.session.commit()
        self.session.refresh(match)

        # Send notifications to both users
        notif_service = NotificationService()
        notif_service.send_new_match_notification(match.user1, match)
        notif_service.send_new_match_notification(match.user2, match)

        return match

    def discover_potential_matches(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> List[PotentialMatch]:
        """
        Discover potential matches for a user
        """
        # Get existing matches to exclude
        existing_match_users = []
        existing_matches = self.get_user_matches(user_id)
        for match in existing_matches:
            if match.user1_id == user_id:
                existing_match_users.append(match.user2_id)
            else:
                existing_match_users.append(match.user1_id)

        # get all potential matches
        potential_matches = (
            self.session.query(User)
            .filter(
                User.is_active.is_(True),
                User.is_verified.is_(True),
                User.has_completed_questionnaire.is_(True),
                User.id.notin_([user_id, *existing_match_users]),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        # Calculate compatibility scores
        questionnaire_service = QuestionnaireService(self.session)
        result = []

        for potential_match in potential_matches:
            compatibility_score = questionnaire_service.get_compatibility_score(
                user_id, potential_match.id
            )

            result.append(
                PotentialMatch(
                    user_id=potential_match.id,
                    compatibility_score=compatibility_score,
                )
            )

        # Sort by compatibility score
        return sorted(result, key=lambda m: m.compatibility_score, reverse=True)

    def accept_match(self, match: Match, user_id: UUID) -> Match:
        """
        Accept a match
        """
        # Check if user is part of the match
        if user_id not in [match.user1_id, match.user2_id]:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="User is not part of this match",
            )

        # Update match acceptance status
        if match.user1_id == user_id:
            match.user1_accepted = True
        else:
            match.user2_accepted = True

        # Check if both users have accepted
        if match.user1_accepted and match.user2_accepted:
            match.status = MatchStatus.ACTIVE
            match.matched_at = utc_now()

            # Create a journey for the match
            journey = Journey(
                match_id=match.id,
                current_step=JourneyStep.STEP_1_PRE_COMPATIBILITY,
                status=JourneyStatus.ACTIVE,
            )
            self.session.add(journey)

            # Send notifications to both users
            notif_service = NotificationService()
            notif_service.send_match_confirmed_notification(match.user1, match)
            notif_service.send_match_confirmed_notification(match.user2, match)

        self.session.commit()
        self.session.refresh(match)
        return match

    def decline_match(self, match: Match, user_id: UUID) -> Match:
        """
        Decline a match
        """
        # Check if user is part of the match
        if user_id not in [match.user1_id, match.user2_id]:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="User is not part of this match",
            )

        notif_service = NotificationService()
        # Set which user declined
        if match.user1_id == user_id:
            match.user1_accepted = False
            notif_service.send_match_declined_notification(match.user2, match)
        else:
            match.user2_accepted = False
            notif_service.send_match_declined_notification(match.user1, match)

        # Update match status
        match.status = MatchStatus.DECLINED

        self.session.commit()
        self.session.refresh(match)
        return match

from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Query, Session

from app.models.match import Match, MatchStatus
from app.models.user import User

from .base_service import BaseService
from .journey_service import JourneyService
from .notification_service import NotificationService


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

    def get_all_matches(self) -> Query[Match]:
        """
        Get all matches in the system
        """
        return self.session.query(Match)

    def get_user_matches(self, user_id: UUID, status: str = None) -> Query[Match]:
        """
        Get all matches for a user
        """
        query = self.session.query(Match).filter(
            or_(Match.user1_id == user_id, Match.user2_id == user_id)
        )

        if status:
            query = query.filter(Match.status == status)

        return query

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
            status=MatchStatus.PENDING,
            user1_accepted=False,
            user2_accepted=False,
        )

        self.session.add(match)
        self.session.commit()
        self.session.refresh(match)

        NotificationService(self.session).send_new_match_notification(match)

        return match

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
            match.status = MatchStatus.ACTIVE

            # Create a journey for the match
            journey_service = JourneyService(self.session)
            if not match.journey:
                match.journey = journey_service.create_journey(match_id)

            # Send notifications to both users
            user1 = self.session.get(User, match.user1_id)
            user2 = self.session.get(User, match.user2_id)

            if user1 and user2:
                NotificationService(self.session).send_match_confirmed_notification(user1, match)
                NotificationService(self.session).send_match_confirmed_notification(user2, match)

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
        match.status = MatchStatus.DECLINED

        # Set which user declined
        if match.user1_id == user_id:
            match.user1_accepted = False
        else:
            match.user2_accepted = False

        self.session.commit()
        self.session.refresh(match)
        return match

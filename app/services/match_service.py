from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Query

from app.models.match import Match, MatchStatus

from .base_service import BaseService
from .journey_service import JourneyService


class MatchService(BaseService):
    """
    Service for match-related operations
    """

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

            # Create a journey for the match if it doesn't exist
            if not match.journey:
                match.journey = JourneyService(self.session).create_journey(match_id)

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

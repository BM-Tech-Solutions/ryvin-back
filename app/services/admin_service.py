from datetime import timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy import func
from sqlalchemy.orm import Query

from app.core.security import utc_now
from app.models.enums import JourneyStatus, MatchStatus, MeetingStatus
from app.models.journey import Journey
from app.models.match import Match
from app.models.meeting import MeetingRequest
from app.models.message import Message
from app.models.user import User

from .base_service import BaseService


class AdminService(BaseService):
    """
    Service for admin-related operations
    """

    def get_users(
        self, search: str = None, is_active: bool = None, is_verified: bool = None
    ) -> Query[User]:
        """
        Get all users with optional search
        """
        query = self.session.query(User)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        if is_verified is not None:
            query = query.filter(User.is_verified == is_verified)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                User.phone_number.ilike(search_term) | User.email.ilike(search_term)
            )

        return query

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID
        """
        return self.session.get(User, user_id)

    def ban_user(self, user_id: UUID, reason: str = None) -> User:
        """
        Ban a user
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")

        user.is_active = False
        user.is_banned = True
        user.banned_at = utc_now()
        user.ban_reason = reason

        self.session.commit()
        self.session.refresh(user)
        return user

    def unban_user(self, user_id: UUID) -> User:
        """
        Unban a user
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")

        if not user.is_banned:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="User is not banned"
            )

        user.is_active = True
        user.is_banned = False
        user.banned_at = None
        user.ban_reason = None

        self.session.commit()
        self.session.refresh(user)
        return user

    def get_matches(
        self, status: str = None, min_compatibility_score: float = None
    ) -> Query[Match]:
        """
        Get all matches with optional status filter
        """
        query = self.session.query(Match)

        if status:
            query = query.filter(Match.status == status)

        if min_compatibility_score is not None:
            query = query.filter(Match.compatibility_score >= min_compatibility_score)

        return query.order_by(Match.created_at.desc())

    def get_journeys(self, is_completed: bool = None, current_step: int = None) -> Query[Journey]:
        """
        Get all journeys with optional filters
        """
        query = self.session.query(Journey)

        if is_completed is not None:
            query = query.filter(Journey.is_completed == is_completed)

        if current_step:
            query = query.filter(Journey.current_step == current_step)

        return query.order_by(Journey.created_at.desc())

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system statistics
        """
        # User stats
        users_query = self.session.query(func.count(User.id))
        total_users = users_query.scalar()
        active_users = users_query.filter(User.is_active.is_(True)).scalar()
        verified_users = users_query.filter(User.is_verified.is_(True)).scalar()
        banned_users = users_query.filter(User.is_banned.is_(True)).scalar()

        # New users in last 7 days
        new_users_last_week = users_query.filter(
            User.created_at >= (utc_now() - timedelta(days=7))
        ).scalar()

        # Match stats
        matches_query = self.session.query(func.count(Match.id))
        total_matches = matches_query.scalar()
        pending_matches = matches_query.filter(Match.status == MatchStatus.PENDING).scalar()
        confirmed_matches = matches_query.filter(Match.status == MatchStatus.ACTIVE).scalar()
        declined_matches = matches_query.filter(Match.status == MatchStatus.DECLINED).scalar()

        # Journey stats
        journey_query = self.session.query(func.count(Journey.id))
        total_journeys = journey_query.scalar()
        active_journeys = journey_query.filter(Journey.status == JourneyStatus.ACTIVE).scalar()
        completed_journeys = journey_query.filter(
            Journey.status == JourneyStatus.COMPLETED
        ).scalar()
        ended_journeys = journey_query.filter(Journey.status == JourneyStatus.ENDED).scalar()

        # Message stats
        msgs_query = self.session.query(func.count(Message.id))
        total_messages = msgs_query.scalar()
        messages_last_week = msgs_query.filter(
            Message.created_at >= utc_now() - timedelta(days=7)
        ).scalar()

        # Meeting stats
        meetings_query = self.session.query(func.count(MeetingRequest.id))
        total_meetings = meetings_query.scalar()
        accepted_meetings = meetings_query.filter(
            MeetingRequest.status == MeetingStatus.ACCEPTED
        ).scalar()

        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "verified": verified_users,
                "banned": banned_users,
                "new_last_week": new_users_last_week,
            },
            "matches": {
                "total": total_matches,
                "pending": pending_matches,
                "confirmed": confirmed_matches,
                "declined": declined_matches,
            },
            "journeys": {
                "total": total_journeys,
                "active": active_journeys,
                "completed": completed_journeys,
                "ended": ended_journeys,
            },
            "messages": {"total": total_messages, "last_week": messages_last_week},
            "meetings": {"total": total_meetings, "accepted": accepted_meetings},
        }

    def get_flagged_messages(self) -> Query[Message]:
        """
        Get messages flagged for moderation
        """
        return (
            self.session.query(Message)
            .filter(Message.is_flagged.is_(True))
            .order_by(Message.created_at.desc())
        )

    def moderate_message(self, message_id: UUID, action: str) -> Message:
        """
        Moderate a flagged message
        """
        message = self.session.get(Message, message_id)
        if not message:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="Message not found"
            )

        if action == "approve":
            message.is_flagged = False
            message.moderated_at = utc_now()
        elif action == "delete":
            message.is_deleted = True
            message.deleted_at = utc_now()
            message.moderated_at = utc_now()
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid moderation action"
            )

        self.session.commit()
        self.session.refresh(message)
        return message

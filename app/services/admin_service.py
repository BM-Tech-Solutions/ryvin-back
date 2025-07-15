from datetime import timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func

from app.core.security import utc_now
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

    def get_users(self, skip: int = 0, limit: int = 100, search: str = None) -> List[User]:
        """
        Get all users with optional search
        """
        query = self.db.query(User)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                User.phone.ilike(search_term)
                | User.email.ilike(search_term)
                | User.first_name.ilike(search_term)
                | User.last_name.ilike(search_term)
            )

        return query.offset(skip).limit(limit).all()

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def ban_user(self, user_id: UUID, reason: str = None) -> User:
        """
        Ban a user
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.is_active = False
        user.is_banned = True
        user.banned_at = utc_now()
        user.ban_reason = reason

        self.db.commit()
        self.db.refresh(user)
        return user

    def unban_user(self, user_id: UUID) -> User:
        """
        Unban a user
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if not user.is_banned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User is not banned"
            )

        user.is_active = True
        user.is_banned = False
        user.banned_at = None
        user.ban_reason = None

        self.db.commit()
        self.db.refresh(user)
        return user

    def get_matches(self, status: str = None, skip: int = 0, limit: int = 100) -> List[Match]:
        """
        Get all matches with optional status filter
        """
        query = self.db.query(Match)

        if status:
            query = query.filter(Match.status == status)

        return query.order_by(Match.created_at.desc()).offset(skip).limit(limit).all()

    def get_journeys(
        self, status: str = None, current_step: int = None, skip: int = 0, limit: int = 100
    ) -> List[Journey]:
        """
        Get all journeys with optional filters
        """
        query = self.db.query(Journey)

        if status:
            query = query.filter(Journey.status == status)

        if current_step:
            query = query.filter(Journey.current_step == current_step)

        return query.order_by(Journey.created_at.desc()).offset(skip).limit(limit).all()

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system statistics
        """
        # User stats
        total_users = self.db.query(func.count(User.id)).scalar()
        active_users = self.db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar()
        verified_users = (
            self.db.query(func.count(User.id)).filter(User.is_verified.is_(True)).scalar()
        )
        banned_users = self.db.query(func.count(User.id)).filter(User.is_banned.is_(True)).scalar()

        # New users in last 7 days
        new_users_last_week = (
            self.db.query(func.count(User.id))
            .filter(User.created_at >= utc_now() - timedelta(days=7))
            .scalar()
        )

        # Match stats
        total_matches = self.db.query(func.count(Match.id)).scalar()
        pending_matches = (
            self.db.query(func.count(Match.id)).filter(Match.status == "pending").scalar()
        )
        confirmed_matches = (
            self.db.query(func.count(Match.id)).filter(Match.status == "matched").scalar()
        )
        declined_matches = (
            self.db.query(func.count(Match.id)).filter(Match.status == "declined").scalar()
        )

        # Journey stats
        total_journeys = self.db.query(func.count(Journey.id)).scalar()
        active_journeys = (
            self.db.query(func.count(Journey.id)).filter(Journey.status == "active").scalar()
        )
        completed_journeys = (
            self.db.query(func.count(Journey.id)).filter(Journey.status == "completed").scalar()
        )
        ended_journeys = (
            self.db.query(func.count(Journey.id)).filter(Journey.status == "ended").scalar()
        )

        # Message stats
        total_messages = self.db.query(func.count(Message.id)).scalar()
        messages_last_week = (
            self.db.query(func.count(Message.id))
            .filter(Message.created_at >= utc_now() - timedelta(days=7))
            .scalar()
        )

        # Meeting stats
        total_meetings = self.db.query(func.count(MeetingRequest.id)).scalar()
        accepted_meetings = (
            self.db.query(func.count(MeetingRequest.id))
            .filter(MeetingRequest.status == "accepted")
            .scalar()
        )

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

    def get_flagged_messages(self, skip: int = 0, limit: int = 100) -> List[Message]:
        """
        Get messages flagged for moderation
        """
        return (
            self.db.query(Message)
            .filter(Message.is_flagged.is_(True))
            .order_by(Message.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def moderate_message(self, message_id: UUID, action: str) -> Message:
        """
        Moderate a flagged message
        """
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

        if action == "approve":
            message.is_flagged = False
            message.moderated_at = utc_now()
        elif action == "delete":
            message.is_deleted = True
            message.deleted_at = utc_now()
            message.moderated_at = utc_now()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid moderation action"
            )

        self.db.commit()
        self.db.refresh(message)
        return message

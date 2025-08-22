from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import utc_now
from app.models.enums import JourneyStatus, JourneyStep, MeetingStatus
from app.models.journey import Journey
from app.models.match import Match
from app.models.meeting import MeetingFeedback, MeetingRequest
from app.models.message import Message
from app.models.user import User
from app.schemas.meeting import MeetingFeedbackCreate, MeetingRequestCreate

from .base_service import BaseService
from .notification_service import NotificationService
from .twilio_service import TwilioService


class JourneyService(BaseService):
    """
    Service for journey-related operations
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.session = db

    def get_journey_by_id(self, journey_id: UUID) -> Optional[Journey]:
        """
        Get journey by ID
        """
        return self.session.get(Journey, journey_id)

    def get_journey_by_match(self, match_id: UUID) -> Optional[Journey]:
        """
        Get journey by match ID
        """
        return self.session.query(Journey).filter(Journey.match_id == match_id).first()

    def create_journey(self, match_id: UUID) -> Journey:
        journey = Journey(
            match_id=match_id,
            current_step=JourneyStep.STEP1_PRE_COMPATIBILITY,
            status=JourneyStatus.ACTIVE,
        )
        self.session.add(journey)
        self.session.commit()
        self.session.refresh(journey)
        twilio_service = TwilioService()
        twilio_service.create_conversation(journey)
        return journey

    def get_journeys(
        self,
        user_id: UUID = None,
        current_step: int = None,
        is_completed: bool = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Journey]:
        """
        Get all journeys for a user
        """
        query = self.session.query(Journey)
        if user_id:
            query = query.join(Match).filter(
                or_(Match.user1_id == user_id, Match.user2_id == user_id)
            )
        if current_step is not None:
            query = query.filter(Journey.current_step == current_step)
        if is_completed is not None:
            query = query.filter(Journey.is_completed == is_completed)

        return query.offset(skip).limit(limit).all()

    def check_user_in_journey(self, journey: Journey, user_id: UUID) -> bool:
        """
        Check if user is part of the journey
        """
        return journey.match.user1_id == user_id or journey.match.user2_id == user_id

    def get_other_user_id(self, journey: Journey, user_id: UUID) -> UUID:
        """
        Get the ID of the other user in the journey
        """
        if journey.match.user1_id == user_id:
            return journey.match.user2_id
        return journey.match.user1_id

    def advance_journey(self, journey_id: UUID) -> Journey:
        """
        Advance journey to the next step
        """
        journey = self.get_journey_by_id(journey_id)
        if not journey:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"No Journey with id: '{journey_id}'",
            )

        # Check if journey is active
        if journey.status != JourneyStatus.ACTIVE:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot advance journey with status '{journey.status}'",
            )

        # Check step-specific requirements
        if journey.current_step == JourneyStep.STEP1_PRE_COMPATIBILITY:
            # Pre-compatibility to Voice/Video Call
            # Check if there are enough messages exchanged
            message_count = (
                self.session.query(Message).filter(Message.journey_id == journey.id).count()
            )
            if message_count < 5:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="At least 5 messages must be exchanged before advancing",
                )

        elif journey.current_step == JourneyStep.STEP2_VOICE_VIDEO_CALL:
            # Voice/Video Call to Photos Unlocked
            # In a real app, we might check for call duration or confirmation
            pass

        elif journey.current_step == JourneyStep.STEP3_PHOTOS_UNLOCKED:
            # Photos Unlocked to Physical Meeting
            # Check if both users have photos
            match = journey.match
            user1_photos = self.session.get(User, match.user1_id).photos
            user2_photos = self.session.get(User, match.user2_id).photos

            if not user1_photos or not user2_photos:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Both users must upload photos before advancing",
                )

        elif journey.current_step == JourneyStep.STEP4_PHYSICAL_MEETING:
            # Physical Meeting to Meeting Feedback
            # Check if meeting request exists and was accepted
            meeting_request = (
                self.session.query(MeetingRequest)
                .filter(
                    MeetingRequest.journey_id == journey.id,
                    MeetingRequest.status == MeetingStatus.ACCEPTED,
                )
                .first()
            )

            if not meeting_request:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="An accepted meeting request is required before advancing",
                )

        # Check if journey is already at the final step
        if journey.current_step >= JourneyStep.STEP5_MEETING_FEEDBACK:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Journey is already at the final step",
            )

        # Advance to next step
        journey.current_step += 1
        journey.updated_at = utc_now()

        self.session.commit()
        self.session.refresh(journey)

        # Send notifications to both users
        match = journey.match
        user1 = self.session.get(User, match.user1_id)
        user2 = self.session.get(User, match.user2_id)

        if user1 and user2:
            NotificationService().send_journey_step_advanced_notification(user1, journey)
            NotificationService().send_journey_step_advanced_notification(user2, journey)

        return journey

    def complete_journey(self, journey: Journey) -> Journey:
        """
        Complete a journey (final step completed successfully)
        """
        journey.status = JourneyStatus.COMPLETED
        journey.completed_at = utc_now()
        journey.updated_at = utc_now()

        self.session.commit()
        self.session.refresh(journey)
        return journey

    def end_journey(self, journey_id: UUID, user_id: UUID, reason: str) -> Journey:
        """
        End a journey prematurely
        """
        journey = self.get_journey_by_id(journey_id)
        if not journey:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"No Journey with id: '{journey_id}'",
            )

        journey.status = JourneyStatus.ENDED
        journey.ended_at = utc_now()
        journey.ended_by = user_id
        journey.end_reason = reason
        journey.updated_at = utc_now()

        self.session.commit()
        self.session.refresh(journey)

        # Send notifications to both users
        match = journey.match
        user1 = self.session.get(User, match.user1_id)
        user2 = self.session.get(User, match.user2_id)

        if user1 and user2:
            NotificationService().send_journey_ended_notification(user1, journey, reason)
            NotificationService().send_journey_ended_notification(user2, journey, reason)

        return journey


class MessageService(BaseService):
    """
    Service for message-related operations within journeys
    """

    def get_messages(self, journey_id: UUID, skip: int = 0, limit: int = 100) -> List[Message]:
        """
        Get messages for a journey
        """
        return (
            self.session.query(Message)
            .filter(Message.journey_id == journey_id)
            .order_by(Message.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_journey_message(self, journey_id: UUID, msg_id: UUID) -> Optional[Message]:
        """
        Get message from a journey
        """
        return (
            self.session.query(Message)
            .filter(Message.id == msg_id, Message.journey_id == journey_id)
            .first()
        )

    def create_message(self, msg_data: dict) -> Message:
        """
        Create a new message in a journey (from twilio webhook) (only "Text" messages for now)
        """
        conv_id = msg_data.get("ConversationSid")
        msg_id = msg_data.get("MessageSid")
        participant_id = msg_data.get("ParticipantSid")
        content = msg_data.get("Body")

        twilio_service = TwilioService()
        journey_service = JourneyService(self.session)

        conv = twilio_service.get_conversation(conv_id)
        if not conv:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Journey with conv: '{conv_id}' not found",
            )
        journey = journey_service.get_journey_by_id(conv.unique_name)
        if not journey:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Journey with conv_id='{conv_id}' not found",
            )
        if participant_id:
            try:
                participant = (
                    twilio_service.chat_service.conversations(conv_id)
                    .participants(participant_id)
                    .fetch()
                )
            except Exception:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Participant with id={participant_id} not Found on Twilio",
                )
            sender = self.session.get(User, participant.identity)
            if sender:
                sender_id = sender.id
            else:
                sender_id = None
        else:
            sender_id = None

        # Create message
        message = Message(
            journey_id=journey.id,
            sender_id=sender_id,
            twilio_msg_id=msg_id,
            content=content,
        )

        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)

        return message

    def update_message(self, msg_data: dict) -> Message:
        """
        Update message (from twilio webhook)
        """
        msg_id = msg_data.get("MessageSid")
        content = msg_data.get("Body")

        message = self.session.query(Message).filter(Message.twilio_msg_id == msg_id).first()
        if not message:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Message with twilio_msg_id={msg_id} not Found.",
            )

        message.content = content
        self.session.commit()
        self.session.refresh(message)

        return message

    def delete_message(self, msg_data: dict) -> Message:
        """
        Set message as deleted (don't really delete the message)  (from twilio webhook)
        """
        msg_id = msg_data.get("MessageSid")

        message = self.session.query(Message).filter(Message.twilio_msg_id == msg_id).first()
        if not message:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Message with twilio_msg_id={msg_id} not Found.",
            )

        message.is_deleted = True
        message.deleted_at = utc_now()
        self.session.commit()
        self.session.refresh(message)

        return message


class MeetingService(BaseService):
    """
    Service for meeting-related operations within journeys
    """

    def get_meeting_requests(self, journey_id: UUID) -> List[MeetingRequest]:
        """
        Get meeting requests for a journey
        """
        return (
            self.session.query(MeetingRequest)
            .filter(MeetingRequest.journey_id == journey_id)
            .order_by(MeetingRequest.created_at.desc())
            .all()
        )

    def get_meeting_request_by_id(self, meeting_id: UUID) -> Optional[MeetingRequest]:
        """
        Get meeting request by ID
        """
        return self.session.get(MeetingRequest, meeting_id)

    def create_meeting_request(
        self, journey_id: UUID, requester_id: UUID, meeting_data: MeetingRequestCreate
    ) -> MeetingRequest:
        """
        Create a new meeting request
        """
        # Check if there's already an accepted meeting request
        existing_accepted = (
            self.session.query(MeetingRequest)
            .filter(
                MeetingRequest.journey_id == journey_id,
                MeetingRequest.status == MeetingStatus.ACCEPTED,
            )
            .first()
        )

        if existing_accepted:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="A meeting has already been accepted for this journey",
            )

        # Create meeting request
        meeting_request = MeetingRequest(
            journey_id=journey_id,
            requester_id=requester_id,
            proposed_date=meeting_data.proposed_date,
            status=MeetingStatus.PROPOSED,
        )

        self.session.add(meeting_request)
        self.session.commit()
        self.session.refresh(meeting_request)

        # Get journey and other user for notification
        journey = self.session.get(Journey, journey_id)
        if journey:
            match = journey.match
            other_user_id = match.user1_id if match.user1_id != requester_id else match.user2_id
            other_user = self.session.get(User, other_user_id)
            requester = self.session.get(User, requester_id)

            if other_user and requester:
                requester_name = requester.questionnaire.first_name or "Your Match"
                NotificationService().send_meeting_request_notification(
                    other_user, meeting_request, requester_name
                )

        return meeting_request

    def respond_to_meeting_request(
        self, meeting_request: MeetingRequest, user_id: UUID, accept: bool
    ) -> MeetingRequest:
        """
        Accept or decline a meeting request
        """
        # Check if meeting request is still pending
        if meeting_request.status != MeetingStatus.PROPOSED:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Meeting request is already {meeting_request.status}",
            )

        # Update status
        meeting_request.status = MeetingStatus.ACCEPTED if accept else MeetingStatus.REJECTED
        meeting_request.responded_at = utc_now()
        meeting_request.responder_id = user_id

        self.session.commit()
        self.session.refresh(meeting_request)

        # Send notification to requester
        requester = self.session.get(User, meeting_request.requested_by)
        if requester:
            NotificationService().send_meeting_response_notification(
                requester, meeting_request, accept
            )

        return meeting_request

    def get_meeting_feedback(self, meeting_request_id: UUID) -> List[MeetingFeedback]:
        """
        Get feedback for a meeting
        """
        return (
            self.session.query(MeetingFeedback)
            .filter(MeetingFeedback.meeting_request_id == meeting_request_id)
            .all()
        )

    def create_meeting_feedback(
        self, user_id: UUID, feedback_data: MeetingFeedbackCreate
    ) -> MeetingFeedback:
        """
        Create feedback for a meeting
        """
        # Check if user has already provided feedback
        existing_feedback = (
            self.session.query(MeetingFeedback)
            .filter(
                MeetingFeedback.meeting_request_id == feedback_data.meeting_request_id,
                MeetingFeedback.user_id == user_id,
            )
            .first()
        )

        if existing_feedback:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="You have already provided feedback for this meeting",
            )

        # Create feedback
        feedback = MeetingFeedback(
            meeting_request_id=feedback_data.meeting_request_id,
            user_id=user_id,
            rating=feedback_data.rating,
            feedback=feedback_data.feedback,
            wants_to_continue=feedback_data.wants_to_continue,
        )

        self.session.add(feedback)
        self.session.commit()
        self.session.refresh(feedback)

        return feedback

    def both_users_provided_feedback(self, meeting_request_id: UUID) -> bool:
        """
        Check if both users have provided feedback for a meeting
        """
        meeting_request = self.session.get(MeetingRequest, meeting_request_id)

        if not meeting_request:
            return False

        if not meeting_request.journey:
            return False

        match = meeting_request.journey.match

        if not match:
            return False

        # Count feedback from both users
        feedback_count = (
            self.session.query(MeetingFeedback)
            .filter(
                MeetingFeedback.meeting_request_id == meeting_request_id,
                MeetingFeedback.user_id.in_([match.user1_id, match.user2_id]),
            )
            .count()
        )

        return feedback_count == 2

    def both_users_want_to_continue(self, meeting_request_id: UUID) -> bool:
        """
        Check if both users want to continue after meeting
        """
        feedbacks = (
            self.session.query(MeetingFeedback)
            .filter(MeetingFeedback.meeting_request_id == meeting_request_id)
            .all()
        )

        if len(feedbacks) != 2:
            return False

        return all(feedback.want_to_continue for feedback in feedbacks)

from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from app.core.security import utc_now
from app.models.enums import JourneyStatus, JourneyStep, MeetingStatus
from app.models.journey import Journey
from app.models.match import Match
from app.models.meeting import MeetingFeedback, MeetingRequest
from app.models.message import Message
from app.models.photo import Photo
from app.models.user import User
from app.schemas.journey import JourneyCreate
from app.schemas.meeting import MeetingFeedbackCreate, MeetingFeedbackUpdate, MeetingRequestCreate
from app.schemas.message import MessageCreate

from .base_service import BaseService
from .notification_service import NotificationService


class JourneyService(BaseService):
    """
    Service for journey-related operations
    """

    def get_journey_by_id(self, journey_id: UUID, raise_exc: bool = True) -> Optional[Journey]:
        """
        Get journey by ID
        """
        journey = (
            self.session.query(Journey)
            .options(selectinload(Journey.match))
            .filter(Journey.id == journey_id)
            .first()
        )

        if not journey and raise_exc:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"no Journey with id: {journey_id}",
            )
        return journey

    def get_journey_by_match(self, match_id: UUID, raise_exc: bool = True) -> Optional[Journey]:
        """
        Get journey by match ID
        """
        journey = (
            self.session.query(Journey)
            .options(selectinload(Journey.match))
            .filter(Journey.match_id == match_id)
            .first()
        )

        if not journey and raise_exc:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Match has no Journey",
            )
        return journey

    def get_user_journey(
        self, user_id: UUID, journey_id: UUID, raise_exc: bool = True
    ) -> Optional[Journey]:
        """
        Get User journey by ID
        """
        journey = (
            self.session.query(Journey)
            .join(Journey.match)
            .options(selectinload(Journey.match))
            .filter(
                Journey.id == journey_id,
                or_(
                    Match.user1_id == user_id,
                    Match.user2_id == user_id,
                ),
            )
            .first()
        )

        if not journey and raise_exc:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"User has no Journey with id: {journey_id}",
            )
        return journey

    def get_user_journeys(
        self,
        user_id: UUID = None,
        current_step: JourneyStep = None,
        is_completed: bool = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Journey]:
        """
        Get all journeys for a user
        """
        query = self.session.query(Journey)
        if user_id:
            query = query.join(Journey.match).filter(
                or_(Match.user1_id == user_id, Match.user2_id == user_id)
            )
        if current_step:
            query = query.filter(Journey.current_step == current_step)
        if is_completed:
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

    def create_journey(self, journey_in: JourneyCreate) -> Journey:
        """
        Create new Journey
        """
        journey = Journey(**journey_in.model_dump(exclude_unset=True))

        self.session.add(journey)
        self.session.commit()
        self.session.refresh(journey)

        return journey

    def advance_journey(self, journey: Journey) -> Journey:
        """
        Advance journey to the next step
        """
        # Check if journey is active
        if journey.status != JourneyStatus.ACTIVE:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot advance journey with status: '{journey.status}'",
            )

        # Check step-specific requirements
        if journey.current_step == JourneyStep.STEP_1_PRE_COMPATIBILITY:
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

            journey.step1_completed_at = utc_now()
            journey.current_step = JourneyStep.STEP_2_VOICE_VIDEO_CALL

        elif journey.current_step == JourneyStep.STEP_2_VOICE_VIDEO_CALL:
            # Voice/Video Call to Photos Unlocked
            # In a real app, we might check for call duration or confirmation
            journey.step2_completed_at = utc_now()
            journey.current_step = JourneyStep.STEP_3_PHOTOS_UNLOCKED

        elif journey.current_step == JourneyStep.STEP_3_PHOTOS_UNLOCKED:
            # Photos Unlocked to Physical Meeting
            # Check if both users have photos
            user1_photos = (
                self.session.query(Photo).filter(Photo.user_id == journey.match.user1_id).all()
            )
            user2_photos = (
                self.session.query(Photo).filter(Photo.user_id == journey.match.user2_id).all()
            )
            if not user1_photos or not user2_photos:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Both users must upload photos before advancing",
                )
            journey.step3_completed_at = utc_now()
            journey.current_step = JourneyStep.STEP_4_PHYSICAL_MEETING

        elif journey.current_step == JourneyStep.STEP_4_PHYSICAL_MEETING:
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

            user1_feedback = (
                self.session.query(MeetingFeedback)
                .filter(
                    MeetingFeedback.user_id == journey.match.user1_id,
                    MeetingFeedback.meeting_request_id == meeting_request.id,
                )
                .first()
            )
            user2_feedback = (
                self.session.query(MeetingFeedback)
                .filter(
                    MeetingFeedback.user_id == journey.match.user2_id,
                    MeetingFeedback.meeting_request_id == meeting_request.id,
                )
                .first()
            )
            if not user1_feedback or not user2_feedback:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Both Users must provide Feedbacks before advancing",
                )
            if not user1_feedback.wants_to_continue:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="User 1 doesn't want to continue",
                )
            if not user2_feedback.wants_to_continue:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="User 2 doesn't want to continue",
                )

            journey.step4_completed_at = utc_now()
            journey.current_step = JourneyStep.STEP_5_MEETING_FEEDBACK

        # Check if journey is already at the final step
        if journey.current_step >= JourneyStep.STEP_5_MEETING_FEEDBACK:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Journey is already at the final step",
            )

        self.session.commit()
        self.session.refresh(journey)

        # Send notifications to both users
        notif_service = NotificationService()
        notif_service.send_journey_step_advanced_notification(journey.match.user1, journey)
        notif_service.send_journey_step_advanced_notification(journey.match.user2, journey)

        return journey

    def complete_journey(self, journey: Journey) -> Journey:
        """
        Complete a journey (final step completed successfully)
        """
        if journey.current_step < JourneyStep.STEP_5_MEETING_FEEDBACK:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Journey hasn't reached the final Step yet!!!",
            )
        journey.status = JourneyStatus.COMPLETED
        journey.step5_completed_at = utc_now()
        journey.completed_at = utc_now()

        self.session.commit()
        self.session.refresh(journey)
        return journey

    def end_journey(self, journey: Journey, user_id: UUID, reason: str) -> Journey:
        """
        End a journey prematurely
        """
        if journey.current_step == JourneyStatus.COMPLETED:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Can't End/Cancel Journey because it's already completed!!!",
            )
        journey.status = JourneyStatus.ENDED
        journey.ended_by = user_id
        journey.end_reason = reason
        journey.ended_at = utc_now()

        self.session.commit()
        self.session.refresh(journey)

        # Send notifications to both users
        notif_service = NotificationService()
        notif_service.send_journey_ended_notification(journey.match.user1, journey, reason)
        notif_service.send_journey_ended_notification(journey.match.user2, journey, reason)

        return journey


class MessageService(BaseService):
    """
    Service for message-related operations within journeys
    """

    def get_journey_messages(
        self, journey_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Message]:
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

    def get_journey_message(
        self, journey_id: UUID, message_id: UUID, raise_exc: bool = True
    ) -> Optional[Message]:
        """
        Get one message from a journey
        """
        message = (
            self.session.query(Message)
            .filter(Message.id == message_id, Message.journey_id == journey_id)
            .first()
        )
        if not message and raise_exc:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Journey has no message with id: {message_id}",
            )
        return message

    def create_message(self, journey: Journey, sender: User, message_in: MessageCreate) -> Message:
        """
        Create a new message in a journey
        """
        # Create message
        message = Message(
            journey_id=journey.id,
            sender_id=sender.id,
            **message_in.model_dump(exclude_unset=True),
        )

        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)

        receiver = journey.match.get_other_user(sender)

        if sender.questionnaire and sender.questionnaire.first_name:
            sender_name = sender.questionnaire.first_name
        else:
            sender_name = "Someone"
        notif_service = NotificationService()
        notif_service.send_new_message_notification(receiver, message, sender_name)

        return message


class MeetingService(BaseService):
    """
    Service for meeting-related operations within journeys
    """

    # Meeting request
    def get_all_journey_meeting_reqs(self, journey_id: UUID) -> List[MeetingRequest]:
        """
        Get all meeting requests for a journey
        """
        return (
            self.session.query(MeetingRequest)
            .filter(MeetingRequest.journey_id == journey_id)
            .order_by(MeetingRequest.created_at.desc())
            .all()
        )

    def get_journey_meeting_request(
        self, journey_id: UUID, meeting_request_id: UUID, raise_exc: bool = True
    ) -> Optional[MeetingRequest]:
        """
        Get one specific meeting request for a journey
        """
        meeting_request = (
            self.session.query(MeetingRequest)
            .filter(
                MeetingRequest.journey_id == journey_id,
                MeetingRequest.id == meeting_request_id,
            )
            .first()
        )
        if not meeting_request and raise_exc:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Journey has no Meeting Request with id: {meeting_request_id}",
            )
        return meeting_request

    def get_meeting_request_by_id(
        self, meeting_request_id: UUID, raise_exc: bool = True
    ) -> Optional[MeetingRequest]:
        """
        Get meeting request by ID
        """
        meeting_request = self.session.get(MeetingRequest, meeting_request_id)
        if not meeting_request and raise_exc:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"no Meeting Request with id: {meeting_request_id}",
            )
        return meeting_request

    def create_meeting_request(
        self, journey: Journey, requester: User, meeting_in: MeetingRequestCreate
    ) -> MeetingRequest:
        """
        Create a new meeting request
        """
        # Check if there's already an accepted or proposed meeting request
        existing_accepted = (
            self.session.query(MeetingRequest)
            .filter(
                MeetingRequest.journey_id == journey.id,
                MeetingRequest.status in [MeetingStatus.PROPOSED, MeetingStatus.ACCEPTED],
            )
            .first()
        )

        if existing_accepted:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="A meeting has already been proposed or accepted for this journey",
            )

        # Create meeting request
        meeting_request = MeetingRequest(
            journey_id=journey.id,
            requester_id=requester.id,
            proposed_date=meeting_in.proposed_date,
            proposed_location=meeting_in.proposed_location,
            status=MeetingStatus.PROPOSED,
        )

        self.session.add(meeting_request)
        self.session.commit()
        self.session.refresh(meeting_request)

        if requester.questionnaire and requester.questionnaire.first_name:
            requester_name = requester.questionnaire.first_name
        else:
            requester_name = "Your Match"

        other_user = journey.match.get_other_user(requester)

        notif_service = NotificationService()
        notif_service.send_meeting_request_notification(other_user, meeting_request, requester_name)

        return meeting_request

    def accept_meeting_request(self, user: User, meeting_request: MeetingRequest) -> MeetingRequest:
        """
        Accept a meeting request
        """
        if meeting_request.status not in [MeetingStatus.PROPOSED, MeetingStatus.DECLINED]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Meeting request is already {meeting_request.status}",
            )

        if meeting_request.requester == user.id:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Requester of meeting can't accept the request, "
                + "Only the Other User of the match can accept.",
            )

        # Update status
        meeting_request.status = MeetingStatus.ACCEPTED

        self.session.commit()
        self.session.refresh(meeting_request)

        # Send notification to requester
        notif_service = NotificationService()
        notif_service.send_meeting_response_notification(meeting_request)

        return meeting_request

    def decline_meeting_request(
        self, user: User, meeting_request: MeetingRequest
    ) -> MeetingRequest:
        """
        Decline a meeting request
        """
        if meeting_request.status not in [MeetingStatus.PROPOSED, MeetingStatus.ACCEPTED]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Meeting request is already {meeting_request.status}",
            )

        if meeting_request.requester == user.id:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Requester of meeting can't decline the request, "
                + "Only the Other User of the match can decline.",
            )

        # Update status
        meeting_request.status = MeetingStatus.DECLINED

        self.session.commit()
        self.session.refresh(meeting_request)

        # Send notification to requester
        notif_service = NotificationService()
        notif_service.send_meeting_response_notification(meeting_request)

        return meeting_request

    def cancel_meeting_request(self, user: User, meeting_request: MeetingRequest) -> MeetingRequest:
        """
        Cancel a meeting request
        """
        if meeting_request.status in [MeetingStatus.COMPLETED, MeetingStatus.CANCELLED]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Meeting request is already {meeting_request.status}",
            )

        if meeting_request.requester != user.id:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Only Requester of meeting can cancel the request.",
            )

        # Update status
        meeting_request.status = MeetingStatus.CANCELLED

        self.session.commit()
        self.session.refresh(meeting_request)

        # Send notification to requester
        notif_service = NotificationService()
        notif_service.send_meeting_response_notification(meeting_request)

        return meeting_request

    # Meeting feedback
    def get_all_meeting_request_feedbacks(self, meeting_request_id: UUID) -> List[MeetingFeedback]:
        """
        Get all feedbacks for a meeting request
        """
        return (
            self.session.query(MeetingFeedback)
            .filter(MeetingFeedback.meeting_request_id == meeting_request_id)
            .all()
        )

    def get_meeting_request_feedback(
        self, meeting_request_id: UUID, meeting_feedback_id: UUID, raise_exc: bool = True
    ) -> Optional[MeetingFeedback]:
        """
        Get specific feedback for a meeting request
        """
        meeting_feedback = (
            self.session.query(MeetingFeedback)
            .filter(
                MeetingFeedback.meeting_request_id == meeting_request_id,
                MeetingFeedback.id == meeting_feedback_id,
            )
            .all()
        )

        if not meeting_feedback and raise_exc:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"MeetingRequest has no Feedback with id: {meeting_feedback_id}",
            )

        return meeting_feedback

    def update_meeting_feedback(
        self, feedback: MeetingFeedback, feedback_in: MeetingFeedbackUpdate
    ) -> MeetingFeedback:
        """
        Update Meeting Feedback
        """
        update_data = feedback_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(feedback, field, value)

        self.session.commit()
        self.session.refresh(feedback)
        return feedback

    def create_meeting_feedback(
        self,
        user_id: UUID,
        meeting_request_id: UUID,
        feedback_in: MeetingFeedbackCreate,
    ) -> MeetingFeedback:
        """
        Create feedback for a meeting
        """
        # Check if user has already provided feedback
        existing_feedback = (
            self.session.query(MeetingFeedback)
            .filter(
                MeetingFeedback.meeting_request_id == meeting_request_id,
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
            user_id=user_id,
            meeting_request_id=meeting_request_id,
            rating=feedback_in.rating,
            feedback=feedback_in.feedback,
            wants_to_continue=feedback_in.wants_to_continue,
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

        return all(feedback.wants_to_continue for feedback in feedbacks)

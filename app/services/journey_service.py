from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from app.models.user import User
from app.models.match import Match
from app.models.journey import Journey
from app.models.message import Message
from app.models.meeting import MeetingRequest, MeetingFeedback
from app.schemas.journey import JourneyUpdate
from app.schemas.message import MessageCreate
from app.schemas.meeting import MeetingRequestCreate, MeetingFeedbackCreate
from .base_service import BaseService
from .notification_service import NotificationService


class JourneyService(BaseService):
    """
    Service for journey-related operations
    """
    def get_journey_by_id(self, journey_id: UUID) -> Optional[Journey]:
        """
        Get journey by ID
        """
        return self.db.query(Journey).filter(Journey.id == journey_id).first()
    
    def get_journey_by_match(self, match_id: UUID) -> Optional[Journey]:
        """
        Get journey by match ID
        """
        return self.db.query(Journey).filter(Journey.match_id == match_id).first()
    
    def get_user_journeys(
        self, user_id: UUID, status: str = None, 
        current_step: int = None, skip: int = 0, limit: int = 100
    ) -> List[Journey]:
        """
        Get all journeys for a user
        """
        query = self.db.query(Journey).join(Match).filter(
            or_(
                Match.user1_id == user_id,
                Match.user2_id == user_id
            )
        )
        
        if status:
            query = query.filter(Journey.status == status)
        
        if current_step:
            query = query.filter(Journey.current_step == current_step)
        
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
    
    def advance_journey(self, journey: Journey, user_id: UUID) -> Journey:
        """
        Advance journey to the next step
        """
        # Check if journey is active
        if journey.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot advance journey with status '{journey.status}'"
            )
        
        # Check if journey is already at the final step
        if journey.current_step >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Journey is already at the final step"
            )
        
        # Check step-specific requirements
        if journey.current_step == 1:
            # Pre-compatibility to Voice/Video Call
            # Check if there are enough messages exchanged
            message_count = self.db.query(Message).filter(Message.journey_id == journey.id).count()
            if message_count < 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least 5 messages must be exchanged before advancing"
                )
        
        elif journey.current_step == 2:
            # Voice/Video Call to Photos Unlocked
            # In a real app, we might check for call duration or confirmation
            pass
        
        elif journey.current_step == 3:
            # Photos Unlocked to Physical Meeting
            # Check if both users have photos
            match = journey.match
            user1_photos = self.db.query(User).filter(User.id == match.user1_id).first().photos
            user2_photos = self.db.query(User).filter(User.id == match.user2_id).first().photos
            
            if not user1_photos or not user2_photos:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Both users must upload photos before advancing"
                )
        
        elif journey.current_step == 4:
            # Physical Meeting to Meeting Feedback
            # Check if meeting request exists and was accepted
            meeting_request = self.db.query(MeetingRequest).filter(
                MeetingRequest.journey_id == journey.id,
                MeetingRequest.status == "accepted"
            ).first()
            
            if not meeting_request:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="An accepted meeting request is required before advancing"
                )
        
        # Advance to next step
        journey.current_step += 1
        journey.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(journey)
        
        # Send notifications to both users
        match = journey.match
        user1 = self.db.query(User).filter(User.id == match.user1_id).first()
        user2 = self.db.query(User).filter(User.id == match.user2_id).first()
        
        if user1 and user2:
            NotificationService().send_journey_step_advanced_notification(user1, journey)
            NotificationService().send_journey_step_advanced_notification(user2, journey)
        
        return journey
    
    def complete_journey(self, journey: Journey) -> Journey:
        """
        Complete a journey (final step completed successfully)
        """
        journey.status = "completed"
        journey.completed_at = datetime.utcnow()
        journey.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(journey)
        return journey
    
    def end_journey(self, journey: Journey, user_id: UUID, reason: str) -> Journey:
        """
        End a journey prematurely
        """
        journey.status = "ended"
        journey.ended_at = datetime.utcnow()
        journey.ended_by_user_id = user_id
        journey.end_reason = reason
        journey.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(journey)
        
        # Send notifications to both users
        match = journey.match
        user1 = self.db.query(User).filter(User.id == match.user1_id).first()
        user2 = self.db.query(User).filter(User.id == match.user2_id).first()
        
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
        return self.db.query(Message).filter(
            Message.journey_id == journey_id
        ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    def create_message(self, journey_id: UUID, sender_id: UUID, message_data: MessageCreate) -> Message:
        """
        Create a new message in a journey
        """
        # Create message
        message = Message(
            journey_id=journey_id,
            sender_id=sender_id,
            content=message_data.content,
            message_type=message_data.message_type
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        # Get journey and other user for notification
        journey = self.db.query(Journey).filter(Journey.id == journey_id).first()
        if journey:
            match = journey.match
            other_user_id = match.user1_id if match.user1_id != sender_id else match.user2_id
            other_user = self.db.query(User).filter(User.id == other_user_id).first()
            sender = self.db.query(User).filter(User.id == sender_id).first()
            
            if other_user and sender:
                sender_name = f"{sender.first_name}" if sender.first_name else "Your match"
                NotificationService().send_new_message_notification(other_user, message, sender_name)
        
        return message


class MeetingService(BaseService):
    """
    Service for meeting-related operations within journeys
    """
    def get_meeting_requests(self, journey_id: UUID) -> List[MeetingRequest]:
        """
        Get meeting requests for a journey
        """
        return self.db.query(MeetingRequest).filter(
            MeetingRequest.journey_id == journey_id
        ).order_by(MeetingRequest.created_at.desc()).all()
    
    def get_meeting_request_by_id(self, meeting_id: UUID) -> Optional[MeetingRequest]:
        """
        Get meeting request by ID
        """
        return self.db.query(MeetingRequest).filter(MeetingRequest.id == meeting_id).first()
    
    def create_meeting_request(
        self, journey_id: UUID, requester_id: UUID, meeting_data: MeetingRequestCreate
    ) -> MeetingRequest:
        """
        Create a new meeting request
        """
        # Check if there's already an accepted meeting request
        existing_accepted = self.db.query(MeetingRequest).filter(
            MeetingRequest.journey_id == journey_id,
            MeetingRequest.status == "accepted"
        ).first()
        
        if existing_accepted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A meeting has already been accepted for this journey"
            )
        
        # Create meeting request
        meeting_request = MeetingRequest(
            journey_id=journey_id,
            requester_id=requester_id,
            proposed_date=meeting_data.proposed_date,
            proposed_time=meeting_data.proposed_time,
            location_type=meeting_data.location_type,
            location_details=meeting_data.location_details,
            notes=meeting_data.notes,
            status="pending"
        )
        
        self.db.add(meeting_request)
        self.db.commit()
        self.db.refresh(meeting_request)
        
        # Get journey and other user for notification
        journey = self.db.query(Journey).filter(Journey.id == journey_id).first()
        if journey:
            match = journey.match
            other_user_id = match.user1_id if match.user1_id != requester_id else match.user2_id
            other_user = self.db.query(User).filter(User.id == other_user_id).first()
            requester = self.db.query(User).filter(User.id == requester_id).first()
            
            if other_user and requester:
                requester_name = f"{requester.first_name}" if requester.first_name else "Your match"
                NotificationService().send_meeting_request_notification(other_user, meeting_request, requester_name)
        
        return meeting_request
    
    def respond_to_meeting_request(self, meeting_request: MeetingRequest, user_id: UUID, accept: bool) -> MeetingRequest:
        """
        Accept or decline a meeting request
        """
        # Check if meeting request is still pending
        if meeting_request.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Meeting request is already {meeting_request.status}"
            )
        
        # Update status
        meeting_request.status = "accepted" if accept else "declined"
        meeting_request.responded_at = datetime.utcnow()
        meeting_request.responder_id = user_id
        
        self.db.commit()
        self.db.refresh(meeting_request)
        
        # Send notification to requester
        requester = self.db.query(User).filter(User.id == meeting_request.requester_id).first()
        if requester:
            NotificationService().send_meeting_response_notification(requester, meeting_request, accept)
        
        return meeting_request
    
    def get_meeting_feedback(self, meeting_request_id: UUID) -> List[MeetingFeedback]:
        """
        Get feedback for a meeting
        """
        return self.db.query(MeetingFeedback).filter(
            MeetingFeedback.meeting_request_id == meeting_request_id
        ).all()
    
    def create_meeting_feedback(self, feedback_data: MeetingFeedbackCreate, user_id: UUID) -> MeetingFeedback:
        """
        Create feedback for a meeting
        """
        # Check if user has already provided feedback
        existing_feedback = self.db.query(MeetingFeedback).filter(
            MeetingFeedback.meeting_request_id == feedback_data.meeting_request_id,
            MeetingFeedback.user_id == user_id
        ).first()
        
        if existing_feedback:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already provided feedback for this meeting"
            )
        
        # Create feedback
        feedback = MeetingFeedback(
            meeting_request_id=feedback_data.meeting_request_id,
            user_id=user_id,
            rating=feedback_data.rating,
            comments=feedback_data.comments,
            want_to_continue=feedback_data.want_to_continue
        )
        
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        
        return feedback
    
    def both_users_provided_feedback(self, meeting_request_id: UUID) -> bool:
        """
        Check if both users have provided feedback for a meeting
        """
        meeting_request = self.db.query(MeetingRequest).filter(
            MeetingRequest.id == meeting_request_id
        ).first()
        
        if not meeting_request:
            return False
        
        journey = self.db.query(Journey).filter(Journey.id == meeting_request.journey_id).first()
        if not journey:
            return False
        
        match = journey.match
        
        # Count feedback from both users
        feedback_count = self.db.query(MeetingFeedback).filter(
            MeetingFeedback.meeting_request_id == meeting_request_id,
            MeetingFeedback.user_id.in_([match.user1_id, match.user2_id])
        ).count()
        
        return feedback_count == 2
    
    def both_users_want_to_continue(self, meeting_request_id: UUID) -> bool:
        """
        Check if both users want to continue after meeting
        """
        feedbacks = self.db.query(MeetingFeedback).filter(
            MeetingFeedback.meeting_request_id == meeting_request_id
        ).all()
        
        if len(feedbacks) != 2:
            return False
        
        return all(feedback.want_to_continue for feedback in feedbacks)
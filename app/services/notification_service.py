from typing import Any, Dict

from app.models.journey import Journey
from app.models.match import Match
from app.models.meeting import MeetingRequest
from app.models.message import Message
from app.models.user import User


class NotificationService:
    """
    Service for sending notifications to users
    In a real application, this would integrate with push notifications, email, or SMS
    """

    def send_notification(
        self, user: User, title: str, body: str, data: Dict[str, Any] = None
    ) -> bool:
        """
        Send a notification to a user
        """
        # In a real app, this would send to a notification service like Firebase
        print(f"Sending notification to {user.phone_number}: {title} - {body}")
        return True

    def send_new_match_notification(self, user: User, match: Match) -> bool:
        """
        Send notification about a new potential match
        """
        # Get the other user in the match
        other_user_id = match.user1_id if match.user2_id == user.id else match.user2_id

        # In a real app, we would query the database for the other user's name
        other_user_name = "Someone"  # Placeholder

        return self.send_notification(
            user,
            "New Match",
            f"{other_user_name} [{other_user_id}] might be compatible with you!",
            {"match_id": str(match.id), "type": "new_match"},
        )

    def send_match_confirmed_notification(self, user: User, match: Match) -> bool:
        """
        Send notification when both users accept a match
        """
        # Get the other user in the match
        other_user_id = match.user1_id if match.user2_id == user.id else match.user2_id

        # In a real app, we would query the database for the other user's name
        other_user_name = "Someone"  # Placeholder

        return self.send_notification(
            user,
            "Match Confirmed!",
            f"You and {other_user_name} [{other_user_id}] have matched! Start your journey together.",
            {"match_id": str(match.id), "type": "match_confirmed"},
        )

    def send_journey_step_advanced_notification(self, user: User, journey: Journey) -> bool:
        """
        Send notification when a journey advances to a new step
        """
        step_descriptions = {
            1: "Pre-compatibility",
            2: "Voice/Video Call",
            3: "Photos Unlocked",
            4: "Physical Meeting",
            5: "Meeting Feedback",
        }

        step_name = step_descriptions.get(journey.current_step, f"Step {journey.current_step}")

        return self.send_notification(
            user,
            "Journey Advanced",
            f"Your journey has advanced to {step_name}!",
            {
                "journey_id": str(journey.id),
                "type": "journey_advanced",
                "step": journey.current_step,
            },
        )

    def send_journey_completed_notification(self, user: User, journey: Journey) -> bool:
        """
        Send notification when a journey is completed
        """
        return self.send_notification(
            user,
            "Journey Completed",
            "Congratulations! You've completed your journey.",
            {"journey_id": str(journey.id), "type": "journey_completed"},
        )

    def send_journey_ended_notification(self, user: User, journey: Journey, reason: str) -> bool:
        """
        Send notification when a journey ends prematurely
        """
        return self.send_notification(
            user,
            "Journey Ended",
            f"Your journey has ended. {reason}",
            {"journey_id": str(journey.id), "type": "journey_ended", "reason": reason},
        )

    def send_new_message_notification(self, user: User, message: Message, sender_name: str) -> bool:
        """
        Send notification for a new message
        """
        return self.send_notification(
            user,
            "New Message",
            f"{sender_name}: {message.content[:50]}{'...' if len(message.content) > 50 else ''}",
            {
                "journey_id": str(message.journey_id),
                "message_id": str(message.id),
                "type": "new_message",
            },
        )

    def send_meeting_request_notification(
        self, user: User, meeting_request: MeetingRequest, requester_name: str
    ) -> bool:
        """
        Send notification for a new meeting request
        """
        return self.send_notification(
            user,
            "Meeting Request",
            f"{requester_name} has requested to meet on {meeting_request.proposed_date.strftime('%B %d, %Y')}",
            {
                "journey_id": str(meeting_request.journey_id),
                "meeting_id": str(meeting_request.id),
                "type": "meeting_request",
            },
        )

    def send_meeting_response_notification(
        self, user: User, meeting_request: MeetingRequest, accepted: bool
    ) -> bool:
        """
        Send notification for a meeting request response
        """
        status = "accepted" if accepted else "declined"

        return self.send_notification(
            user,
            f"Meeting Request {status.capitalize()}",
            f"Your meeting request for {meeting_request.proposed_date.strftime('%B %d, %Y')} was {status}",
            {
                "journey_id": str(meeting_request.journey_id),
                "meeting_id": str(meeting_request.id),
                "type": "meeting_response",
                "accepted": accepted,
            },
        )

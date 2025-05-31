"""
Meeting models module - contains MeetingRequest and MeetingFeedback classes
This file exists to provide backward compatibility for imports
"""

from app.models.meeting_request import MeetingRequest
from app.models.meeting_feedback import MeetingFeedback

# Re-export MeetingRequest and MeetingFeedback for backward compatibility
# This allows existing code to import from app.models.meeting
__all__ = ["MeetingRequest", "MeetingFeedback"]

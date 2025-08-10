"""
Matching Cron Service for Ryvin Dating App

This service handles automatic matching between users through scheduled jobs.
It calculates compatibility scores and creates matches between users of different genders.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, not_, or_
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.models.match import Match
from app.models.questionnaire import Questionnaire
from app.models.user import User
from app.models.enums import Gender, MatchStatus
from app.services.matching_algorithm_service import MatchingAlgorithmService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class MatchingCronService:
    """
    Service for automated matching between users via cron jobs
    """

    def __init__(self, session: Session = None):
        self.session = session or next(get_session())
        self.matching_algorithm = MatchingAlgorithmService()
        self.notification_service = NotificationService()
        self.min_compatibility_score = 50  # Minimum score to create a match (lowered for testing)
        self.max_matches_per_user = 50  # Maximum matches per user

    async def run_daily_matching(self) -> dict:
        """
        Main cron job function to run daily matching
        
        Returns:
            Dictionary with matching statistics
        """
        logger.info("Starting daily matching process...")
        
        stats = {
            "total_users_processed": 0,
            "new_matches_created": 0,
            "users_with_new_matches": 0,
            "processing_time": None,
            "errors": []
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Get all active users who need matching
            eligible_users = self._get_eligible_users_for_matching()
            stats["total_users_processed"] = len(eligible_users)
            
            logger.info(f"Found {len(eligible_users)} eligible users for matching")
            
            # Process matching for each user
            for user in eligible_users:
                try:
                    user_matches = await self._process_user_matching(user)
                    if user_matches > 0:
                        stats["new_matches_created"] += user_matches
                        stats["users_with_new_matches"] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing matches for user {user.id}: {str(e)}")
                    stats["errors"].append(f"User {user.id}: {str(e)}")
            
            # Calculate processing time
            end_time = datetime.utcnow()
            stats["processing_time"] = (end_time - start_time).total_seconds()
            
            logger.info(f"Daily matching completed. Created {stats['new_matches_created']} new matches")
            
        except Exception as e:
            logger.error(f"Error in daily matching process: {str(e)}")
            stats["errors"].append(f"General error: {str(e)}")
        
        return stats

    async def process_new_user_matching(self, user_id: UUID) -> dict:
        """
        Process matching for a newly registered user
        
        Args:
            user_id: ID of the new user
            
        Returns:
            Dictionary with matching statistics for the user
        """
        logger.info(f"Processing matching for new user: {user_id}")
        
        stats = {
            "user_id": str(user_id),
            "matches_created": 0,
            "processing_time": None,
            "error": None
        }
        
        start_time = datetime.utcnow()
        
        try:
            user = self.session.get(User, user_id)
            if not user:
                stats["error"] = "User not found"
                return stats
            
            # Check if user is eligible for matching
            if not self._is_user_eligible_for_matching(user):
                stats["error"] = "User not eligible for matching"
                return stats
            
            matches_created = await self._process_user_matching(user)
            stats["matches_created"] = matches_created
            
            end_time = datetime.utcnow()
            stats["processing_time"] = (end_time - start_time).total_seconds()
            
            logger.info(f"Created {matches_created} matches for new user {user_id}")
            
        except Exception as e:
            logger.error(f"Error processing matches for new user {user_id}: {str(e)}")
            stats["error"] = str(e)
        
        return stats

    def _get_eligible_users_for_matching(self) -> List[User]:
        """
        Get all users eligible for matching
        
        Returns:
            List of eligible users
        """
        # Get users who:
        # 1. Are active and verified
        # 2. Have completed questionnaire
        # 3. Have gender specified
        # 4. Don't have too many existing matches
        # 5. Haven't been processed recently (optional optimization)
        
        subquery_match_count = (
            self.session.query(Match.user1_id.label('user_id'))
            .filter(Match.status != MatchStatus.DECLINED)
            .union_all(
                self.session.query(Match.user2_id.label('user_id'))
                .filter(Match.status != MatchStatus.DECLINED)
            )
            .subquery()
        )
        
        users = (
            self.session.query(User)
            .join(Questionnaire, User.id == Questionnaire.user_id)
            .filter(
                User.is_active.is_(True),
                User.is_verified.is_(True),
                User.is_banned.is_(False),
                User.has_completed_questionnaire.is_(True),
                Questionnaire.gender.isnot(None),
                Questionnaire.gender.in_([Gender.HOMME, Gender.FEMME])
            )
            .all()
        )
        
        # Filter users who don't have too many matches
        eligible_users = []
        for user in users:
            match_count = self._get_user_match_count(user.id)
            if match_count < self.max_matches_per_user:
                eligible_users.append(user)
        
        return eligible_users

    def _is_user_eligible_for_matching(self, user: User) -> bool:
        """
        Check if a user is eligible for matching
        
        Args:
            user: User to check
            
        Returns:
            True if eligible, False otherwise
        """
        if not (user.is_active and user.is_verified and not user.is_banned):
            return False
        
        if not user.has_completed_questionnaire:
            return False
        
        # Check if user has questionnaire with gender
        questionnaire = (
            self.session.query(Questionnaire)
            .filter(Questionnaire.user_id == user.id)
            .first()
        )
        
        if not questionnaire or not questionnaire.gender:
            return False
        
        if questionnaire.gender not in [Gender.HOMME, Gender.FEMME]:
            return False
        
        # Check match count
        match_count = self._get_user_match_count(user.id)
        if match_count >= self.max_matches_per_user:
            return False
        
        return True

    async def _process_user_matching(self, user: User) -> int:
        """
        Process matching for a specific user
        
        Args:
            user: User to process matching for
            
        Returns:
            Number of new matches created
        """
        matches_created = 0
        
        # Get user's questionnaire
        user_questionnaire = (
            self.session.query(Questionnaire)
            .filter(Questionnaire.user_id == user.id)
            .first()
        )
        
        if not user_questionnaire:
            return 0
        
        # Get potential matches (opposite gender)
        potential_matches = self._get_potential_matches_for_user(user, user_questionnaire)
        
        logger.info(f"Found {len(potential_matches)} potential matches for user {user.id}")
        
        # Calculate compatibility with each potential match
        for potential_match_user, potential_match_questionnaire in potential_matches:
            try:
                # Calculate compatibility
                compatibility_result = self.matching_algorithm.calculate_compatibility(
                    user_questionnaire, potential_match_questionnaire
                )
                
                # Only create match if compatibility is above threshold
                if (compatibility_result.total_score >= self.min_compatibility_score and 
                    not compatibility_result.deal_breaker_failed):
                    
                    # Create the match
                    match = self._create_match(
                        user.id, 
                        potential_match_user.id, 
                        compatibility_result
                    )
                    
                    if match:
                        matches_created += 1
                        logger.debug(f"Created match between {user.id} and {potential_match_user.id} "
                                   f"with score {compatibility_result.total_score}")
                
            except Exception as e:
                logger.error(f"Error calculating compatibility between {user.id} and "
                           f"{potential_match_user.id}: {str(e)}")
        
        return matches_created

    def _get_potential_matches_for_user(self, user: User, user_questionnaire: Questionnaire) -> List[Tuple[User, Questionnaire]]:
        """
        Get potential matches for a user (opposite gender, not already matched)
        
        Args:
            user: User to find matches for
            user_questionnaire: User's questionnaire
            
        Returns:
            List of tuples (User, Questionnaire) for potential matches
        """
        # Determine opposite gender
        opposite_gender = Gender.FEMME if user_questionnaire.gender == Gender.HOMME else Gender.HOMME
        
        # Get existing match user IDs to exclude
        existing_match_user_ids = (
            self.session.query(Match.user2_id)
            .filter(Match.user1_id == user.id)
            .union_all(
                self.session.query(Match.user1_id)
                .filter(Match.user2_id == user.id)
            )
            .all()
        )
        existing_match_user_ids = [row[0] for row in existing_match_user_ids]
        
        # Query for potential matches
        query = (
            self.session.query(User, Questionnaire)
            .join(Questionnaire, User.id == Questionnaire.user_id)
            .filter(
                User.id != user.id,
                User.is_active.is_(True),
                User.is_verified.is_(True),
                User.is_banned.is_(False),
                User.has_completed_questionnaire.is_(True),
                Questionnaire.gender == opposite_gender
            )
        )
        
        # Exclude existing matches
        if existing_match_user_ids:
            query = query.filter(User.id.notin_(existing_match_user_ids))
        
        # Limit results for performance
        potential_matches = query.limit(100).all()
        
        return potential_matches

    def _create_match(self, user1_id: UUID, user2_id: UUID, compatibility_result) -> Optional[Match]:
        """
        Create a new match between two users
        
        Args:
            user1_id: First user ID
            user2_id: Second user ID
            compatibility_result: Compatibility calculation result
            
        Returns:
            Created Match object or None if failed
        """
        try:
            # Check if match already exists
            existing_match = (
                self.session.query(Match)
                .filter(
                    or_(
                        and_(Match.user1_id == user1_id, Match.user2_id == user2_id),
                        and_(Match.user1_id == user2_id, Match.user2_id == user1_id)
                    )
                )
                .first()
            )
            
            if existing_match:
                return None
            
            # Create new match (only using fields that exist in the Match model)
            match = Match(
                user1_id=user1_id,
                user2_id=user2_id,
                compatibility_score=compatibility_result.total_score,
                status="pending"
            )
            
            self.session.add(match)
            self.session.commit()
            self.session.refresh(match)
            
            # Note: SMS notifications disabled - only storing matches in database
            logger.debug(f"Match created and stored: {user1_id} ↔ {user2_id} (Score: {compatibility_result.total_score})")
            
            return match
            
        except Exception as e:
            logger.error(f"Error creating match between {user1_id} and {user2_id}: {str(e)}")
            self.session.rollback()
            return None
    def _get_user_match_count(self, user_id: UUID) -> int:
        """
        Get the number of existing matches for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of matches
        """
        return (
            self.session.query(Match)
            .filter(
                or_(Match.user1_id == user_id, Match.user2_id == user_id),
                Match.status != "declined"
            )
            .count()
        )

    def get_matching_statistics(self) -> dict:
        """
        Get overall matching statistics
        
        Returns:
            Dictionary with matching statistics
        """
        total_users = self.session.query(User).filter(User.is_active.is_(True)).count()
        
        users_with_questionnaire = (
            self.session.query(User)
            .filter(
                User.is_active.is_(True),
                User.has_completed_questionnaire.is_(True)
            )
            .count()
        )
        
        total_matches = self.session.query(Match).count()
        
        active_matches = (
            self.session.query(Match)
            .filter(Match.status.in_(["pending", "active"]))
            .count()
        )
        
        return {
            "total_users": total_users,
            "users_with_questionnaire": users_with_questionnaire,
            "total_matches": total_matches,
            "active_matches": active_matches,
            "matching_rate": (users_with_questionnaire / total_users * 100) if total_users > 0 else 0
        }

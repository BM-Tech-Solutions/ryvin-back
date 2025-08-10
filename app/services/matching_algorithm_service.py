"""
Advanced Matching Algorithm Service for Ryvin Dating App

This service implements a sophisticated compatibility scoring system
based on questionnaire responses across multiple categories.
"""

from typing import Dict, Any, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass
from enum import Enum

from app.models.questionnaire import Questionnaire
from app.models.enums import Gender


class MatchingStrategy(Enum):
    """Different strategies for matching different types of fields"""
    EXACT_MATCH = "exact_match"
    PREFERENCE_MATCH = "preference_match"
    RANGE_MATCH = "range_match"
    COMPLEMENTARY_MATCH = "complementary_match"
    TOLERANCE_MATCH = "tolerance_match"


@dataclass
class CategoryWeight:
    """Weights for different compatibility categories"""
    relationship_goals_values: float = 0.25
    religious_spiritual: float = 0.20
    lifestyle_compatibility: float = 0.15
    family_children: float = 0.15
    personality_communication: float = 0.10
    physical_intimacy: float = 0.08
    socio_economic: float = 0.05
    political_social: float = 0.02


@dataclass
class CompatibilityResult:
    """Result of compatibility calculation"""
    total_score: int
    category_scores: Dict[str, int]
    deal_breaker_failed: bool
    deal_breaker_reasons: list[str]
    confidence_level: float


class MatchingAlgorithmService:
    """
    Advanced matching algorithm service that calculates compatibility
    between two users based on their questionnaire responses.
    """

    def __init__(self):
        self.category_weights = CategoryWeight()
        self.deal_breaker_fields = self._get_deal_breaker_fields()
        self.compatibility_matrices = self._initialize_compatibility_matrices()

    def calculate_compatibility(
        self, 
        questionnaire_1: Questionnaire, 
        questionnaire_2: Questionnaire
    ) -> CompatibilityResult:
        """
        Main method to calculate compatibility between two questionnaires
        
        Args:
            questionnaire_1: First user's questionnaire
            questionnaire_2: Second user's questionnaire
            
        Returns:
            CompatibilityResult with detailed scoring breakdown
        """
        # Step 1: Validate questionnaires are complete
        if not questionnaire_1.is_complete() or not questionnaire_2.is_complete():
            return CompatibilityResult(
                total_score=0,
                category_scores={},
                deal_breaker_failed=True,
                deal_breaker_reasons=["Incomplete questionnaire"],
                confidence_level=0.0
            )
        
        # Step 1.5: Validate gender compatibility (only male-female matching)
        gender_validation = self._validate_gender_compatibility(questionnaire_1, questionnaire_2)
        if not gender_validation[0]:
            return CompatibilityResult(
                total_score=0,
                category_scores={},
                deal_breaker_failed=True,
                deal_breaker_reasons=gender_validation[1],
                confidence_level=1.0
            )

        # Step 2: Check deal breakers
        deal_breaker_result = self._check_deal_breakers(questionnaire_1, questionnaire_2)
        if deal_breaker_result[0]:  # Deal breaker failed
            return CompatibilityResult(
                total_score=0,
                category_scores={},
                deal_breaker_failed=True,
                deal_breaker_reasons=deal_breaker_result[1],
                confidence_level=1.0
            )

        # Step 3: Calculate category scores
        category_scores = self._calculate_category_scores(questionnaire_1, questionnaire_2)

        # Step 4: Calculate weighted total score
        total_score = self._calculate_weighted_total(category_scores)

        # Step 5: Calculate confidence level
        confidence = self._calculate_confidence_level(questionnaire_1, questionnaire_2)

        return CompatibilityResult(
            total_score=min(100, max(0, int(total_score))),
            category_scores=category_scores,
            deal_breaker_failed=False,
            deal_breaker_reasons=[],
            confidence_level=confidence
        )

    def _check_deal_breakers(
        self, 
        q1: Questionnaire, 
        q2: Questionnaire
    ) -> Tuple[bool, list[str]]:
        """
        Check for deal breakers that would eliminate compatibility
        
        Returns:
            Tuple of (has_deal_breaker, list_of_reasons)
        """
        deal_breaker_reasons = []

        # Religious deal breakers
        if q1.partner_must_share_religion == "oui" and q1.religion_spirituality != q2.religion_spirituality:
            deal_breaker_reasons.append("Religious requirement not met")

        if q2.partner_must_share_religion == "oui" and q2.religion_spirituality != q1.religion_spirituality:
            deal_breaker_reasons.append("Partner's religious requirement not met")

        # Non-believer acceptance
        if q1.accept_non_believer == "non" and q2.religion_spirituality in ["athée", "agnostique", "non_croyant"]:
            deal_breaker_reasons.append("Non-believer not accepted")

        if q2.accept_non_believer == "non" and q1.religion_spirituality in ["athée", "agnostique", "non_croyant"]:
            deal_breaker_reasons.append("Partner doesn't accept non-believers")

        # Children deal breakers
        if q1.wants_children == "oui" and q1.partner_must_want_children == "oui" and q2.wants_children == "non":
            deal_breaker_reasons.append("Children requirement not met")

        if q2.wants_children == "oui" and q2.partner_must_want_children == "oui" and q1.wants_children == "non":
            deal_breaker_reasons.append("Partner's children requirement not met")

        # Smoking deal breakers
        if q1.accept_smoker_partner == "non" and q2.smoker == "oui":
            deal_breaker_reasons.append("Smoking not accepted")

        if q2.accept_smoker_partner == "non" and q1.smoker == "oui":
            deal_breaker_reasons.append("Partner doesn't accept smoking")

        # Alcohol deal breakers
        if q1.accept_alcohol_consumer_partner == "non" and q2.drinks_alcohol == "oui":
            deal_breaker_reasons.append("Alcohol consumption not accepted")

        if q2.accept_alcohol_consumer_partner == "non" and q1.drinks_alcohol == "oui":
            deal_breaker_reasons.append("Partner doesn't accept alcohol consumption")

        return len(deal_breaker_reasons) > 0, deal_breaker_reasons

    def _calculate_category_scores(
        self, 
        q1: Questionnaire, 
        q2: Questionnaire
    ) -> Dict[str, int]:
        """Calculate scores for each compatibility category"""
        
        category_scores = {}

        # 1. Relationship Goals & Values (25%)
        category_scores["relationship_goals_values"] = self._score_relationship_goals(q1, q2)

        # 2. Religious & Spiritual Beliefs (20%)
        category_scores["religious_spiritual"] = self._score_religious_compatibility(q1, q2)

        # 3. Lifestyle Compatibility (15%)
        category_scores["lifestyle_compatibility"] = self._score_lifestyle_compatibility(q1, q2)

        # 4. Family & Children Planning (15%)
        category_scores["family_children"] = self._score_family_compatibility(q1, q2)

        # 5. Personality & Communication (10%)
        category_scores["personality_communication"] = self._score_personality_compatibility(q1, q2)

        # 6. Physical & Intimacy Preferences (8%)
        category_scores["physical_intimacy"] = self._score_physical_compatibility(q1, q2)

        # 7. Socio-Economic Compatibility (5%)
        category_scores["socio_economic"] = self._score_socio_economic_compatibility(q1, q2)

        # 8. Political & Social Values (2%)
        category_scores["political_social"] = self._score_political_compatibility(q1, q2)

        return category_scores

    def _score_relationship_goals(self, q1: Questionnaire, q2: Questionnaire) -> int:
        """Score relationship goals and core values compatibility"""
        score = 0
        max_score = 100

        # Relationship goal alignment (40 points)
        if q1.relationship_goal == q2.relationship_goal:
            score += 40

        # Age compatibility (20 points)
        score += self._score_age_compatibility(q1, q2, max_points=20)

        # Lessons from past relationships (20 points)
        if q1.lessons_from_past_relationships and q2.lessons_from_past_relationships:
            # Similar learning experiences indicate maturity
            score += 20

        # Previously married compatibility (20 points)
        if q1.previously_married == q2.previously_married:
            score += 20
        elif q1.previously_married in ["non", None] and q2.previously_married in ["non", None]:
            score += 15  # Both haven't been married

        return min(score, max_score)

    def _score_religious_compatibility(self, q1: Questionnaire, q2: Questionnaire) -> int:
        """Score religious and spiritual compatibility"""
        score = 0
        max_score = 100

        # Same religion/spirituality (30 points)
        if q1.religion_spirituality == q2.religion_spirituality:
            score += 30

        # Religious practice level (25 points)
        if q1.religious_practice == q2.religious_practice:
            score += 25
        elif self._are_compatible_practice_levels(q1.religious_practice, q2.religious_practice):
            score += 15

        # Faith transmission to children (25 points)
        if q1.faith_transmission_to_children == q2.faith_transmission_to_children:
            score += 25

        # Partner same religious education vision (20 points)
        if q1.partner_same_religious_education_vision == q2.partner_same_religious_education_vision:
            score += 20

        return min(score, max_score)

    def _score_lifestyle_compatibility(self, q1: Questionnaire, q2: Questionnaire) -> int:
        """Score lifestyle compatibility"""
        score = 0
        max_score = 100

        # Sport frequency compatibility (20 points)
        score += self._score_lifestyle_preference_match(
            q1.sport_frequency, q2.sport_frequency,
            q1.partner_sport_frequency, q2.partner_sport_frequency, 20
        )

        # Dietary habits (20 points)
        if q1.specific_dietary_habits == q2.specific_dietary_habits:
            score += 20
        elif q1.partner_same_dietary_habits == "non" and q2.partner_same_dietary_habits == "non":
            score += 15  # Both are flexible

        # Cleanliness and hygiene (20 points)
        score += self._score_lifestyle_preference_match(
            q1.hygiene_tidiness_approach, q2.hygiene_tidiness_approach,
            q1.partner_cleanliness_importance, q2.partner_cleanliness_importance, 20
        )

        # Social vs homebody balance (20 points)
        if q1.tolerance_social_vs_homebody and q2.tolerance_social_vs_homebody:
            # High tolerance from both is good
            score += 20

        # Pet compatibility (20 points)
        score += self._score_pet_compatibility(q1, q2, 20)

        return min(score, max_score)

    def _score_family_compatibility(self, q1: Questionnaire, q2: Questionnaire) -> int:
        """Score family and children planning compatibility"""
        score = 0
        max_score = 100

        # Wants children alignment (40 points)
        if q1.wants_children == q2.wants_children:
            score += 40
        elif q1.wants_children == "peut_etre" or q2.wants_children == "peut_etre":
            score += 20  # One is flexible

        # Number of desired children (20 points)
        if q1.partner_desired_number_of_children and q2.partner_desired_number_of_children:
            if q1.partner_desired_number_of_children == q2.partner_desired_number_of_children:
                score += 20

        # Educational approach (20 points)
        if q1.educational_approach == q2.educational_approach:
            score += 20

        # Accept partner with children (20 points)
        if q1.has_children == "oui" and q2.accept_partner_with_children == "oui":
            score += 10
        if q2.has_children == "oui" and q1.accept_partner_with_children == "oui":
            score += 10

        return min(score, max_score)

    def _score_personality_compatibility(self, q1: Questionnaire, q2: Questionnaire) -> int:
        """Score personality and communication compatibility"""
        score = 0
        max_score = 100

        # Love language compatibility (30 points)
        if q1.primary_love_language == q2.primary_love_language:
            score += 30
        elif q1.partner_same_love_language == "non" and q2.partner_same_love_language == "non":
            score += 15  # Both are flexible with different love languages

        # Personality type compatibility (25 points)
        score += self._score_personality_type_compatibility(q1, q2, 25)

        # Conflict management (25 points)
        if q1.conflict_management == q2.conflict_management:
            score += 25
        elif self._are_complementary_conflict_styles(q1.conflict_management, q2.conflict_management):
            score += 15

        # Greatest quality alignment (20 points)
        if q1.greatest_quality_in_relationship == q2.greatest_quality_in_relationship:
            score += 20

        return min(score, max_score)

    def _score_physical_compatibility(self, q1: Questionnaire, q2: Questionnaire) -> int:
        """Score physical and intimacy compatibility"""
        score = 0
        max_score = 100

        # Importance of sexuality alignment (30 points)
        if q1.importance_of_sexuality == q2.importance_of_sexuality:
            score += 30

        # Intimate frequency compatibility (25 points)
        if q1.ideal_intimate_frequency == q2.ideal_intimate_frequency:
            score += 25

        # Comfort talking about sexuality (20 points)
        if q1.comfort_level_talking_sexuality == q2.comfort_level_talking_sexuality:
            score += 20

        # Public affection comfort (15 points)
        if q1.comfortable_public_affection == q2.comfortable_public_affection:
            score += 15

        # Appearance importance (10 points)
        if q1.appearance_importance == q2.appearance_importance:
            score += 10

        return min(score, max_score)

    def _score_socio_economic_compatibility(self, q1: Questionnaire, q2: Questionnaire) -> int:
        """Score socio-economic compatibility"""
        score = 0
        max_score = 100

        # Education level compatibility (40 points)
        if q1.education_level == q2.education_level:
            score += 40
        elif self._are_compatible_education_levels(q1.education_level, q2.education_level):
            score += 25

        # Professional situation compatibility (30 points)
        if q1.professional_situation == q2.professional_situation:
            score += 30

        # Money approach in couple (30 points)
        if q1.money_approach_in_couple == q2.money_approach_in_couple:
            score += 30

        return min(score, max_score)

    def _score_political_compatibility(self, q1: Questionnaire, q2: Questionnaire) -> int:
        """Score political and social values compatibility"""
        score = 0
        max_score = 100

        # Political orientation (60 points)
        if q1.political_orientation == q2.political_orientation:
            score += 60
        elif q1.partner_share_convictions_importance == "peu_important" and q2.partner_share_convictions_importance == "peu_important":
            score += 30  # Both don't care much about political alignment

        # Importance of sharing convictions (40 points)
        if q1.partner_share_convictions_importance == q2.partner_share_convictions_importance:
            score += 40

        return min(score, max_score)

    # Helper methods for specific compatibility calculations

    def _score_age_compatibility(self, q1: Questionnaire, q2: Questionnaire, max_points: int) -> int:
        """Score age compatibility based on preferences and actual ages"""
        # This would need actual age calculation from age field
        # For now, return partial score if both have age preferences
        if q1.partner_age_range and q2.partner_age_range:
            return max_points // 2
        return 0

    def _score_lifestyle_preference_match(
        self, 
        trait1: str, trait2: str, 
        preference1: str, preference2: str, 
        max_points: int
    ) -> int:
        """Score mutual lifestyle preference matching"""
        score = 0
        
        # If traits match exactly
        if trait1 == trait2:
            score += max_points // 2
            
        # If preferences are met mutually
        if preference1 == trait2:
            score += max_points // 4
        if preference2 == trait1:
            score += max_points // 4
            
        return min(score, max_points)

    def _score_pet_compatibility(self, q1: Questionnaire, q2: Questionnaire, max_points: int) -> int:
        """Score pet-related compatibility"""
        score = 0
        
        # If both have pets or both don't have pets
        if q1.has_pet == q2.has_pet:
            score += max_points // 2
            
        # Check readiness to live with pets
        if q1.has_pet == "oui" and q2.ready_to_live_with_pet == "oui":
            score += max_points // 4
        if q2.has_pet == "oui" and q1.ready_to_live_with_pet == "oui":
            score += max_points // 4
            
        # Check allergies
        if q1.allergic_to_animals == "oui" and q2.has_pet == "oui":
            score -= max_points // 2
        if q2.allergic_to_animals == "oui" and q1.has_pet == "oui":
            score -= max_points // 2
            
        return max(0, min(score, max_points))

    def _score_personality_type_compatibility(self, q1: Questionnaire, q2: Questionnaire, max_points: int) -> int:
        """Score personality type compatibility"""
        if not q1.personality_type or not q2.personality_type:
            return 0
            
        # Check if personality types are complementary or similar based on preferences
        if q1.partner_personality_preference == q2.personality_type:
            return max_points
        elif q2.partner_personality_preference == q1.personality_type:
            return max_points
        elif q1.personality_type == q2.personality_type:
            return max_points // 2  # Similar can be good too
        else:
            return 0

    def _are_compatible_practice_levels(self, practice1: str, practice2: str) -> bool:
        """Check if religious practice levels are compatible"""
        if not practice1 or not practice2:
            return False
            
        # Define compatibility matrix for practice levels
        compatible_practices = {
            "tres_pratiquant": ["pratiquant", "moderement_pratiquant"],
            "pratiquant": ["tres_pratiquant", "moderement_pratiquant"],
            "moderement_pratiquant": ["pratiquant", "peu_pratiquant"],
            "peu_pratiquant": ["moderement_pratiquant", "non_pratiquant"],
            "non_pratiquant": ["peu_pratiquant"]
        }
        
        return practice2 in compatible_practices.get(practice1, [])

    def _are_complementary_conflict_styles(self, style1: str, style2: str) -> bool:
        """Check if conflict management styles are complementary"""
        if not style1 or not style2:
            return False
            
        # Some conflict styles work well together
        complementary_pairs = [
            ("direct", "diplomatique"),
            ("calme", "expressif"),
            ("analytique", "emotionnel")
        ]
        
        return (style1, style2) in complementary_pairs or (style2, style1) in complementary_pairs

    def _are_compatible_education_levels(self, edu1: str, edu2: str) -> bool:
        """Check if education levels are compatible"""
        if not edu1 or not edu2:
            return False
            
        # Define education level hierarchy
        education_hierarchy = {
            "doctorat": 5,
            "master": 4,
            "licence": 3,
            "bac": 2,
            "college": 1
        }
        
        level1 = education_hierarchy.get(edu1, 0)
        level2 = education_hierarchy.get(edu2, 0)
        
        # Compatible if within 1-2 levels
        return abs(level1 - level2) <= 2

    def _calculate_weighted_total(self, category_scores: Dict[str, int]) -> float:
        """Calculate weighted total score from category scores"""
        total = 0.0
        
        total += category_scores.get("relationship_goals_values", 0) * self.category_weights.relationship_goals_values
        total += category_scores.get("religious_spiritual", 0) * self.category_weights.religious_spiritual
        total += category_scores.get("lifestyle_compatibility", 0) * self.category_weights.lifestyle_compatibility
        total += category_scores.get("family_children", 0) * self.category_weights.family_children
        total += category_scores.get("personality_communication", 0) * self.category_weights.personality_communication
        total += category_scores.get("physical_intimacy", 0) * self.category_weights.physical_intimacy
        total += category_scores.get("socio_economic", 0) * self.category_weights.socio_economic
        total += category_scores.get("political_social", 0) * self.category_weights.political_social
        
        return total

    def _calculate_confidence_level(self, q1: Questionnaire, q2: Questionnaire) -> float:
        """Calculate confidence level based on questionnaire completeness"""
        # Count non-null fields for both questionnaires
        total_fields = 50  # Approximate number of important fields
        
        q1_filled = sum(1 for field in vars(q1).values() if field is not None and field != "")
        q2_filled = sum(1 for field in vars(q2).values() if field is not None and field != "")
        
        avg_completeness = (q1_filled + q2_filled) / (2 * total_fields)
        return min(1.0, avg_completeness)

    def _get_deal_breaker_fields(self) -> list[str]:
        """Get list of fields that can be deal breakers"""
        return [
            "partner_must_share_religion",
            "accept_non_believer", 
            "partner_must_want_children",
            "accept_smoker_partner",
            "accept_alcohol_consumer_partner",
            "allergic_to_animals"
        ]

    def _validate_gender_compatibility(self, q1: Questionnaire, q2: Questionnaire) -> Tuple[bool, list[str]]:
        """
        Validate that users have different genders (male-female matching only)
        
        Args:
            q1: First user's questionnaire
            q2: Second user's questionnaire
            
        Returns:
            Tuple of (is_compatible, list_of_reasons)
        """
        reasons = []
        
        # Check if both users have gender specified
        if not q1.gender or not q2.gender:
            reasons.append("Gender not specified for one or both users")
            return False, reasons
        
        # Check if both genders are valid (homme or femme)
        valid_genders = [Gender.HOMME, Gender.FEMME]
        if q1.gender not in valid_genders or q2.gender not in valid_genders:
            reasons.append("Invalid gender specification")
            return False, reasons
        
        # Check if genders are different (no same-sex matching)
        if q1.gender == q2.gender:
            reasons.append("Same-sex matching not supported")
            return False, reasons
        
        # Valid male-female pairing
        return True, []

    def _initialize_compatibility_matrices(self) -> Dict[str, Any]:
        """Initialize compatibility matrices for complex matching"""
        return {
            "personality_types": {},
            "conflict_styles": {},
            "education_levels": {}
        }

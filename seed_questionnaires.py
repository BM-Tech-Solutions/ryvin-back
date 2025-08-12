#!/usr/bin/env python3
"""
Seed script to complete questionnaires for 60+ users with realistic and diverse French data
"""

import json
import os
import random
import sys

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.core.database import get_session
from app.core.security import utc_now
from app.models.questionnaire import Questionnaire
from app.models.user import User


def get_realistic_questionnaire_data(gender: str, user_name: str):
    """Generate realistic questionnaire data based on gender and personality with enhanced diversity"""

    # More diverse age range
    age = str(random.randint(20, 50))

    # fmt: off
    # Extended French cities including smaller towns
    cities = [
        "Paris", "Lyon", "Marseille", "Toulouse", "Nice",
        "Nantes", "Strasbourg", "Montpellier", "Bordeaux", "Lille",
        "Rennes", "Reims", "Saint-Étienne", "Toulon", "Le Havre",
        "Grenoble", "Dijon", "Angers", "Villeurbanne", "Nîmes",
        "Clermont-Ferrand", "Aix-en-Provence", "Brest", "Limoges", "Tours"
    ]
    # fmt: on

    # French names
    first_name = user_name.split()[0]

    # Create personality-based preferences
    personality_type = random.choice(["introverti", "extraverti", "ambivert"])
    is_religious = random.random() < 0.4  # 40% religious
    is_health_conscious = random.random() < 0.6  # 60% health conscious
    is_career_focused = random.random() < 0.7  # 70% career focused

    # Personality-based preferences
    languages = ["français"]
    if random.random() > 0.3:  # 70% speak English
        languages.append("anglais")
    if random.random() > 0.8:  # 20% speak a third language
        languages.append(random.choice(["espagnol", "italien", "allemand", "arabe"]))

    # Career and education correlation
    if is_career_focused:
        education_level = random.choice(
            ["bac_plus_4_5", "bac_plus_2_3", "bac_plus_4_5"]
        )  # Higher education bias
        professional_situation = random.choice(
            ["salarie", "independant", "salarie"]
        )  # Less likely student
    else:
        education_level = random.choice(["bac_ou_equivalent", "bac_plus_2_3", "bac_plus_4_5"])
        professional_situation = random.choice(["salarie", "independant", "etudiant"])

    # Religious consistency
    if is_religious:
        religion = random.choice(["christianisme", "islam", "judaisme"])
        religious_practice = random.choice(
            ["oui", "occasionnellement", "oui"]
        )  # More likely to practice
        partner_must_share_religion = random.choice(
            ["oui_absolument", "serait_un_plus", "serait_un_plus"]
        )
        accept_non_believer = random.choice(["non", "oui", "non"])  # Less likely to accept
    else:
        religion = random.choice(
            ["athee", "agnostique", "christianisme"]
        )  # Some cultural Christians
        religious_practice = random.choice(["non", "occasionnellement", "non"])
        partner_must_share_religion = random.choice(
            ["pas_necessaire", "serait_un_plus", "pas_necessaire"]
        )
        accept_non_believer = "oui"

    data = {
        # Basic Info
        "first_name": first_name,
        "age": age,
        "gender": gender,
        "city_of_residence": random.choice(cities),
        "nationality_cultural_origin": "française",
        "languages_spoken": languages,
        # Relationship Goals (age-based)
        "relationship_goal": "mariage"
        if int(age) > 28 or random.random() > 0.6
        else "relation_serieuse",
        # Professional (personality-based)
        "professional_situation": professional_situation,
        "education_level": education_level,
        "previously_married": "oui" if int(age) > 35 and random.random() > 0.7 else "non",
        # Religious & Spiritual (consistent logic)
        "religion_spirituality": religion,
        "religious_practice": religious_practice,
        "partner_must_share_religion": partner_must_share_religion,
        "accept_non_believer": accept_non_believer,
        "faith_transmission_to_children": "oui"
        if is_religious
        else random.choice(["non", "je_ne_sais_pas_encore"]),
        "partner_same_religious_education_vision": "oui" if is_religious else "peu_importe",
        # Political
        "political_orientation": random.choice(["gauche", "centre", "droite", "apolitique"]),
        "partner_share_convictions_importance": random.choice(
            ["tres_important", "important", "peu_important"]
        ),
        # Lifestyle (health-conscious logic)
        "sport_frequency": (
            random.choice(["3_5_par_semaine", "tous_les_jours", "1_2_par_semaine"])
            if is_health_conscious
            else random.choice(["jamais", "1_2_par_semaine", "3_5_par_semaine"])
        ),
        "specific_dietary_habits": (
            random.choice(["vegetarien", "vegan", "aucune"])
            if is_health_conscious and random.random() > 0.7
            else ("halal" if religion == "islam" else "aucune")
        ),
        "hygiene_tidiness_approach": random.choice(["tres_important", "important", "flexible"]),
        "smoker": "non"
        if is_health_conscious
        else random.choice(["oui", "non", "occasionnellement"]),
        "drinks_alcohol": (
            "non"
            if religion == "islam" or (is_health_conscious and random.random() > 0.6)
            else random.choice(["oui", "occasionnellement", "non"])
        ),
        # Partner Lifestyle Preferences (consistent with own preferences)
        "partner_sport_frequency": (
            random.choice(["1_2_par_semaine", "3_5_par_semaine", "peu_importe"])
            if is_health_conscious
            else "peu_importe"
        ),
        "partner_same_dietary_habits": "oui" if religion == "islam" else "peu_importe",
        "partner_cleanliness_importance": random.choice(
            ["tres_important", "important", "flexible"]
        ),
        "accept_smoker_partner": "non"
        if is_health_conscious
        else random.choice(["oui", "non", "occasionnellement_seulement"]),
        "accept_alcohol_consumer_partner": (
            "non"
            if religion == "islam"
            else ("occasionnellement_seulement" if is_health_conscious else "oui")
        ),
        # Pets
        "has_pet": random.choice(["oui", "non"]),
        "ready_to_live_with_pet": random.choice(["oui", "non", "ca_depend"]),
        # Personality (consistent with personality_type)
        "personality_type": personality_type,
        "primary_love_language": random.choice(
            ["mots_affirmation", "temps_qualite", "contact_physique", "cadeaux", "services"]
        ),
        "friends_visit_frequency": (
            "souvent"
            if personality_type == "extraverti"
            else ("rarement" if personality_type == "introverti" else "parfois")
        ),
        "tolerance_social_vs_homebody": (
            "tres_social"
            if personality_type == "extraverti"
            else ("casanier" if personality_type == "introverti" else "equilibre")
        ),
        # Physical & Intimacy
        "importance_of_sexuality": random.choice(["tres_important", "important", "peu_important"]),
        "ideal_intimate_frequency": random.choice(
            ["quotidienne", "plusieurs_fois_semaine", "hebdomadaire"]
        ),
        "comfort_level_talking_sexuality": random.choice(
            ["tres_confortable", "confortable", "inconfortable"]
        ),
        "comfortable_public_affection": random.choice(["oui", "non", "modere"]),
        # Compatibility
        "partner_similarity_preference": random.choice(
            ["tres_similaire", "quelques_differences", "complementaire"]
        ),
        "partner_age_range": f"{max(18, int(age) - 5)}-{min(60, int(age) + 8)}",
        # Socio-economic
        "importance_financial_situation_partner": random.choice(
            ["tres_important", "important", "peu_important"]
        ),
        "ideal_partner_education_profession": random.choice(
            ["similaire", "superieur", "peu_importe"]
        ),
        # Children & Family
        "has_children": random.choice(["oui", "non"]),
        "wants_children": random.choice(["oui", "non", "peut_etre"]),
        "partner_must_want_children": random.choice(["oui", "non", "peu_importe"]),
        "accept_partner_with_children": random.choice(["oui", "non", "ca_depend"]),
        # Description fields
        "lessons_from_past_relationships": "J'ai appris l'importance de la communication.",
        "greatest_quality_in_relationship": "L'honnêteté et la bienveillance.",
        "what_attracts_you": "L'intelligence et l'humour.",
        "intolerable_flaw": "Le manque de respect.",
        "ideal_partner_description": "Une personne authentique et bienveillante.",
        "ideal_couple_life_description": "Une vie équilibrée entre complicité et indépendance.",
        "imagine_yourself_in10_years": "Dans une relation stable avec peut-être des enfants.",
        "reason_for_registration": "Trouver une relation sérieuse et durable.",
    }

    return data


def create_questionnaire_for_user(user_id: int, gender: str, user_name: str):
    """Create a realistic questionnaire for a specific user"""

    session = next(get_session())

    try:
        # Check if questionnaire already exists
        existing = session.query(Questionnaire).filter(Questionnaire.user_id == user_id).first()

        if existing:
            print(f"  ⚠️  Questionnaire already exists for {user_name}")
            return existing

        # Generate realistic data
        data = get_realistic_questionnaire_data(gender, user_name)

        # Create questionnaire
        questionnaire = Questionnaire(
            user_id=user_id,
            first_name=data["first_name"],
            age=data["age"],
            gender=data["gender"],
            city_of_residence=data["city_of_residence"],
            nationality_cultural_origin=data["nationality_cultural_origin"],
            languages_spoken=data["languages_spoken"],
            relationship_goal=data["relationship_goal"],
            professional_situation=data["professional_situation"],
            education_level=data["education_level"],
            previously_married=data["previously_married"],
            # Religious & Spiritual
            religion_spirituality=data["religion_spirituality"],
            religious_practice=data["religious_practice"],
            partner_must_share_religion=data["partner_must_share_religion"],
            accept_non_believer=data["accept_non_believer"],
            faith_transmission_to_children=data["faith_transmission_to_children"],
            partner_same_religious_education_vision=data["partner_same_religious_education_vision"],
            # Political
            political_orientation=data["political_orientation"],
            partner_share_convictions_importance=data["partner_share_convictions_importance"],
            # Lifestyle
            sport_frequency=data["sport_frequency"],
            specific_dietary_habits=data["specific_dietary_habits"],
            hygiene_tidiness_approach=data["hygiene_tidiness_approach"],
            smoker=data["smoker"],
            drinks_alcohol=data["drinks_alcohol"],
            # Partner Lifestyle
            partner_sport_frequency=data["partner_sport_frequency"],
            partner_same_dietary_habits=data["partner_same_dietary_habits"],
            partner_cleanliness_importance=data["partner_cleanliness_importance"],
            accept_smoker_partner=data["accept_smoker_partner"],
            accept_alcohol_consumer_partner=data["accept_alcohol_consumer_partner"],
            # Pets
            has_pet=data["has_pet"],
            ready_to_live_with_pet=data["ready_to_live_with_pet"],
            # Personality
            personality_type=data["personality_type"],
            primary_love_language=data["primary_love_language"],
            friends_visit_frequency=data["friends_visit_frequency"],
            tolerance_social_vs_homebody=data["tolerance_social_vs_homebody"],
            # Physical & Intimacy
            importance_of_sexuality=data["importance_of_sexuality"],
            ideal_intimate_frequency=data["ideal_intimate_frequency"],
            comfort_level_talking_sexuality=data["comfort_level_talking_sexuality"],
            comfortable_public_affection=data["comfortable_public_affection"],
            # Compatibility
            partner_similarity_preference=data["partner_similarity_preference"],
            partner_age_range=data["partner_age_range"],
            # Socio-economic
            importance_financial_situation_partner=data["importance_financial_situation_partner"],
            ideal_partner_education_profession=data["ideal_partner_education_profession"],
            # Children & Family
            has_children=data["has_children"],
            wants_children=data["wants_children"],
            partner_must_want_children=data["partner_must_want_children"],
            accept_partner_with_children=data["accept_partner_with_children"],
            # Descriptions
            lessons_from_past_relationships=data["lessons_from_past_relationships"],
            greatest_quality_in_relationship=data["greatest_quality_in_relationship"],
            what_attracts_you=data["what_attracts_you"],
            intolerable_flaw=data["intolerable_flaw"],
            ideal_partner_description=data["ideal_partner_description"],
            ideal_couple_life_description=data["ideal_couple_life_description"],
            imagine_yourself_in10_years=data["imagine_yourself_in10_years"],
            reason_for_registration=data["reason_for_registration"],
            completed_at=utc_now(),
        )

        session.add(questionnaire)
        session.commit()

        # Update user completion status
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.has_completed_questionnaire = True
            session.commit()

        print(f"  ✅ Created questionnaire for {user_name}")
        print(f"     Age: {data['age']}, Goal: {data['relationship_goal']}")
        print(
            f"     Location: {data['city_of_residence']}, Profession: {data['professional_situation']}"
        )

        return questionnaire

    except Exception as e:
        print(f"  ❌ Error creating questionnaire for {user_name}: {str(e)}")
        session.rollback()
        return None
    finally:
        session.close()


def seed_questionnaires_from_file():
    """Seed questionnaires for users from created_users.json"""

    print("📋 Loading users from created_users.json...")

    try:
        with open("created_users.json", "r", encoding="utf-8") as f:
            users_data = json.load(f)
    except FileNotFoundError:
        print("❌ created_users.json not found. Run seed_users.py first!")
        return False
    except Exception as e:
        print(f"❌ Error reading user data: {str(e)}")
        return False

    print(f"📝 Creating questionnaires for {len(users_data)} users...")

    created_count = 0

    for user_data in users_data:
        user_id = user_data["id"]
        user_name = user_data["name"]
        gender = user_data["gender"]

        questionnaire = create_questionnaire_for_user(user_id, gender, user_name)
        if questionnaire:
            created_count += 1

    print(f"\n🎉 Successfully created {created_count} questionnaires!")
    return True


def seed_questionnaires_from_db():
    """Seed questionnaires for all active users in database"""

    print("📋 Loading users from database...")

    session = next(get_session())

    try:
        users = (
            session.query(User).filter(User.is_active.is_(True), User.is_verified.is_(True)).all()
        )

        if not users:
            print("❌ No active users found in database")
            return False

        print(f"📝 Creating questionnaires for {len(users)} users...")

        created_count = 0

        for user in users:
            # Determine gender from email pattern or random
            gender = "homme" if created_count % 2 == 0 else "femme"
            user_name = user.email.split("@")[0].replace(".", " ").title()

            questionnaire = create_questionnaire_for_user(user.id, gender, user_name)
            if questionnaire:
                created_count += 1

        print(f"\n🎉 Successfully created {created_count} questionnaires!")
        return True

    except Exception as e:
        print(f"❌ Error loading users: {str(e)}")
        return False
    finally:
        session.close()


def main():
    """Main function to run questionnaire seeding"""

    print("📝 RYVIN DATING APP - QUESTIONNAIRE SEEDING SCRIPT")
    print("=" * 55)

    # Try to load from file first, then from database
    success = seed_questionnaires_from_file()

    if not success:
        print("\n🔄 Trying to load users from database...")
        success = seed_questionnaires_from_db()

    if success:
        print("\n🎯 Next Steps:")
        print("1. Wait 2 minutes for automatic matching to trigger")
        print("2. Check logs for matching activity:")
        print("   🎯 AUTOMATIC MATCHING JOB STARTED...")
        print("3. View matches: GET /api/v1/matches/admin/stats/detailed")
        print("4. Test user matches: GET /api/v1/matches")
        print("\n🚀 Your dating app is ready for testing!")
    else:
        print("❌ Questionnaire seeding failed")


if __name__ == "__main__":
    main()

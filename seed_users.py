#!/usr/bin/env python3
"""
Seed script to create 60 test users (30 male, 30 female) for the Ryvin dating app
"""

import sys
import os
import random
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_session
from app.models.user import User
from app.models.enums import SubscriptionType


def create_test_users():
    """Create 60 test users with realistic French names and data"""
    
    print("🚀 Starting user seeding process...")
    
    session = next(get_session())
    
    # Extended French male names
    male_names = [
        "Alexandre", "Antoine", "Baptiste", "Benjamin", "Clément", 
        "David", "Étienne", "Fabien", "Guillaume", "Hugo",
        "Julien", "Lucas", "Maxime", "Nicolas", "Pierre",
        "Raphaël", "Sébastien", "Thomas", "Vincent", "Xavier",
        "Adrien", "Arthur", "Aurélien", "Bastien", "Cédric",
        "Damien", "Florian", "Jérémie", "Loïc", "Mathieu"
    ]
    
    # Extended French female names
    female_names = [
        "Amélie", "Camille", "Charlotte", "Élise", "Emma",
        "Julie", "Léa", "Marie", "Océane", "Sophie",
        "Anaïs", "Audrey", "Céline", "Clara", "Élodie",
        "Fanny", "Gabrielle", "Hélène", "Inès", "Justine",
        "Laure", "Manon", "Nathalie", "Pauline", "Romane",
        "Sarah", "Tiffany", "Valérie", "Yasmine", "Zoé"
    ]
    
    # Extended French surnames
    surnames = [
        "Martin", "Bernard", "Dubois", "Thomas", "Robert",
        "Petit", "Durand", "Leroy", "Moreau", "Simon",
        "Laurent", "Lefebvre", "Michel", "Garcia", "David",
        "Bertrand", "Roux", "Vincent", "Fournier", "Morel",
        "Girard", "Andre", "Lefebvre", "Mercier", "Dupont",
        "Lambert", "Bonnet", "Francois", "Martinez", "Legrand",
        "Garnier", "Faure", "Rousseau", "Blanc", "Guerin",
        "Muller", "Henry", "Roussel", "Nicolas", "Perrin",
        "Morin", "Mathieu", "Clement", "Gauthier", "Dumont",
        "Lopez", "Fontaine", "Chevalier", "Robin", "Masson"
    ]
    
    created_users = []
    
    try:
        # Create 30 male users
        print("👨 Creating 30 male users...")
        for i in range(30):
            first_name = male_names[i]
            last_name = random.choice(surnames)
            
            user = User(
                phone_number=f"+336{random.randint(10000000, 99999999)}",
                email=f"{first_name.lower()}.{last_name.lower()}@example.fr",
                is_active=True,
                is_verified=True,
                has_completed_questionnaire=False,  # Will be set to True when questionnaire is completed
                subscription_type=random.choice([SubscriptionType.FREE, SubscriptionType.PREMIUM]),
                last_login=datetime.utcnow() - timedelta(days=random.randint(0, 7)),
                verified_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            
            session.add(user)
            session.flush()  # Get the ID
            created_users.append({
                'id': user.id,
                'name': f"{first_name} {last_name}",
                'email': user.email,
                'phone': user.phone_number,
                'gender': 'homme'
            })
            
            print(f"  ✅ Created male user: {first_name} {last_name} ({user.email})")
        
        # Create 30 female users
        print("👩 Creating 30 female users...")
        for i in range(30):
            first_name = female_names[i]
            last_name = random.choice(surnames)
            
            user = User(
                phone_number=f"+336{random.randint(10000000, 99999999)}",
                email=f"{first_name.lower()}.{last_name.lower()}@example.fr",
                is_active=True,
                is_verified=True,
                has_completed_questionnaire=False,  # Will be set to True when questionnaire is completed
                subscription_type=random.choice([SubscriptionType.FREE, SubscriptionType.PREMIUM]),
                last_login=datetime.utcnow() - timedelta(days=random.randint(0, 7)),
                verified_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            
            session.add(user)
            session.flush()  # Get the ID
            created_users.append({
                'id': user.id,
                'name': f"{first_name} {last_name}",
                'email': user.email,
                'phone': user.phone_number,
                'gender': 'femme'
            })
            
            print(f"  ✅ Created female user: {first_name} {last_name} ({user.email})")
        
        # Commit all users
        session.commit()
        
        print(f"\n🎉 Successfully created {len(created_users)} users!")
        print("\n📋 User Summary:")
        print(f"   👨 Male users: 30")
        print(f"   👩 Female users: 30")
        print(f"   📧 All users verified and active")
        
    
        
        return created_users
        
    except Exception as e:
        print(f"❌ Error creating users: {str(e)}")
        session.rollback()
        return []
    finally:
        session.close()


def list_existing_users():
    """List existing users in the database"""
    
    print("📋 Checking existing users...")
    
    session = next(get_session())
    
    try:
        users = session.query(User).filter(User.is_active == True).all()
        
        if not users:
            print("   No users found in database")
            return []
        
        print(f"   Found {len(users)} existing users:")
        for user in users:
            print(f"   - {user.email} ({user.phone_number})")
        
        return users
        
    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")
        return []
    finally:
        session.close()


def main():
    """Main function to run the user seeding"""
    
    print("🌱 RYVIN DATING APP - USER SEEDING SCRIPT")
    print("=" * 50)
    
    # Check existing users
    existing_users = list_existing_users()
    
    if existing_users:
        response = input(f"\n⚠️  Found {len(existing_users)} existing users. Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("❌ Seeding cancelled")
            return
    
    # Create new users
    created_users = create_test_users()
    
    if created_users:
        print("\n🎯 Next Steps:")
        print("1. Run 'python seed_questionnaires.py' to complete questionnaires")
        print("2. Wait 2 minutes for automatic matching")
        print("3. Check matches via API: GET /api/v1/matches/admin/stats/detailed")
        print("\n🚀 Happy testing!")
    else:
        print("❌ User seeding failed")


if __name__ == "__main__":
    main()

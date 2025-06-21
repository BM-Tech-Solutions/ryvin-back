"""
Firebase User Creation Script
----------------------------
This script creates a user in Firebase with a phone number and returns a Firebase ID token.
"""
import firebase_admin
from firebase_admin import credentials, auth
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Phone number to test (the one you created in Firebase Console)
PHONE_NUMBER = "+213778788714"  # E.164 format without spaces

# Firebase Web API Key (from Firebase Console > Project Settings > General)
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY")

def setup_firebase_admin():
    """Initialize Firebase Admin SDK with service account credentials"""
    try:
        # Path to your service account file - adjust if needed
        service_account_path = os.environ.get(
            "FIREBASE_SERVICE_ACCOUNT_PATH", 
            "path/to/serviceAccountKey.json"
        )
        
        # Check if Firebase Admin is already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")
        return False

def get_or_create_user_by_phone(phone_number):
    """Get existing user by phone number or create if not exists"""
    try:
        # Try to get user by phone number
        user = auth.get_user_by_phone_number(phone_number)
        print(f"Found existing user with phone: {phone_number}, UID: {user.uid}")
        return user
    except auth.UserNotFoundError:
        # User not found, create a new one
        print(f"User with phone {phone_number} not found. Creating new user...")
        user = auth.create_user(phone_number=phone_number)
        print(f"Created new user with phone: {phone_number}, UID: {user.uid}")
        return user
    except Exception as e:
        print(f"Error getting or creating user: {e}")
        return None

def create_custom_token(uid):
    """Create a custom token for the user"""
    try:
        custom_token = auth.create_custom_token(uid).decode('utf-8')
        print("Custom token created successfully")
        return custom_token
    except Exception as e:
        print(f"Error creating custom token: {e}")
        return None

def exchange_custom_token_for_id_token(custom_token):
    """Exchange a custom token for an ID token using Firebase Auth REST API"""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={FIREBASE_API_KEY}"
    payload = {
        "token": custom_token,
        "returnSecureToken": True
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            id_token = data.get("idToken")
            print("Successfully obtained Firebase ID token")
            return id_token
        else:
            print(f"Error exchanging custom token: {response.text}")
            return None
    except Exception as e:
        print(f"Error exchanging custom token: {e}")
        return None

def display_user_info(user):
    """Display user information in a formatted way"""
    if not user:
        return
    
    print("\nUser Information:")
    print("----------------")
    print(f"UID: {user.uid}")
    print(f"Phone Number: {user.phone_number}")
    print(f"Email: {user.email or 'Not set'}")
    print(f"Display Name: {user.display_name or 'Not set'}")
    print(f"Photo URL: {user.photo_url or 'Not set'}")
    print(f"Email Verified: {user.email_verified}")
    print(f"Disabled: {user.disabled}")
    print(f"Creation Time: {user.user_metadata.creation_timestamp}")
    print(f"Last Sign In Time: {user.user_metadata.last_sign_in_timestamp}")
    
    # Print custom claims if any
    if user.custom_claims:
        print("\nCustom Claims:")
        print(json.dumps(user.custom_claims, indent=2))

# Main execution
if __name__ == "__main__":
    print("Firebase User Creation")
    print("=====================\n")
    
    # Initialize Firebase Admin SDK
    if not setup_firebase_admin():
        print("Failed to initialize Firebase Admin SDK. Exiting.")
        exit(1)
    
    # Get or create user by phone number
    user = get_or_create_user_by_phone(PHONE_NUMBER)
    if not user:
        print(f"Failed to get or create user with phone {PHONE_NUMBER}.")
        exit(1)
    
    # Display user information
    display_user_info(user)
    
    # Create custom token
    custom_token = create_custom_token(user.uid)
    if not custom_token:
        print("Failed to create custom token. Exiting.")
        exit(1)
    
    # Exchange for ID token
    id_token = exchange_custom_token_for_id_token(custom_token)
    if not id_token:
        print("Failed to exchange custom token for ID token. Exiting.")
        exit(1)
    
    # Save the ID token to a file for use in other scripts
    with open('firebase_id_token.txt', 'w') as f:
        f.write(id_token)
    print("\nFirebase ID token saved to firebase_id_token.txt")
    
    print("\nUser creation/verification completed successfully.")

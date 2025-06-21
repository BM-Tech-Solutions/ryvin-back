"""
Firebase Phone Verification Script
--------------------------------
This script tests the verify-phone endpoint using a Firebase ID token.
"""
import firebase_admin
from firebase_admin import credentials, auth
import json
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Phone number to test (the one you created in Firebase Console)
PHONE_NUMBER = "+213778788714"  # E.164 format without spaces

# Your API token from .env file
API_TOKEN = os.environ.get("API_TOKEN")

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

def get_user_by_phone(phone_number):
    """Get existing user by phone number"""
    try:
        # Try to get user by phone number
        user = auth.get_user_by_phone_number(phone_number)
        print(f"Found existing user with phone: {phone_number}, UID: {user.uid}")
        return user
    except auth.UserNotFoundError:
        print(f"User with phone {phone_number} not found.")
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
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

def test_verify_phone_endpoint(id_token):
    """Test the verify-phone endpoint with the ID token"""
    url = "http://localhost:8001/api/v1/auth/verify-phone"
    headers = {
        "Content-Type": "application/json",
        "API-Token": API_TOKEN
    }
    payload = {
        "firebase_token": id_token,
        "device_info": {
            "device_id": "test-device-123",
            "platform": "python-test"
        }
    }
    
    try:
        print(f"\nSending request to {url}")
        print(f"Headers: {headers}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, headers=headers, json=payload)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response body: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"Error response: {response.text}")
            return None
    except Exception as e:
        print(f"Error testing endpoint: {e}")
        return None

def load_firebase_id_token():
    """Load the Firebase ID token from the file saved by firebase_create_user.py"""
    try:
        with open('firebase_id_token.txt', 'r') as f:
            token = f.read().strip()
            if token:
                print("Firebase ID token loaded successfully")
                return token
            else:
                print("Firebase ID token file is empty")
                return None
    except FileNotFoundError:
        print("Firebase ID token file not found. Please run firebase_create_user.py first.")
        return None
    except Exception as e:
        print(f"Error loading Firebase ID token: {e}")
        return None

# Main execution
if __name__ == "__main__":
    print("Firebase Phone Verification Test")
    print("==============================\n")
    
    # Option 1: Load Firebase ID token from file
    print("Option 1: Using saved Firebase ID token from file")
    id_token = load_firebase_id_token()
    
    # Option 2: Generate a new Firebase ID token
    if not id_token:
        print("\nOption 2: Generating a new Firebase ID token")
        
        # Initialize Firebase Admin SDK
        if not setup_firebase_admin():
            print("Failed to initialize Firebase Admin SDK. Exiting.")
            exit(1)
        
        # Get user by phone number
        user = get_user_by_phone(PHONE_NUMBER)
        if not user:
            print(f"User with phone {PHONE_NUMBER} not found. Please run firebase_create_user.py first.")
            exit(1)
        
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
    
    # Test verify-phone endpoint
    verify_response = test_verify_phone_endpoint(id_token)
    
    if verify_response:
        print("\nVerify phone test completed successfully.")
        
        # Save the access token to a file for use in the next script
        if 'access_token' in verify_response:
            with open('access_token.txt', 'w') as f:
                f.write(verify_response['access_token'])
            print("Access token saved to access_token.txt for use in firebase_complete_profile.py")
            
            # Also save the entire response for reference
            with open('verify_phone_response.json', 'w') as f:
                json.dump(verify_response, f, indent=2)
            print("Full response saved to verify_phone_response.json")
    else:
        print("\nVerify phone test failed.")

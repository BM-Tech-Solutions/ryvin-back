import firebase_admin
from firebase_admin import credentials, auth
import json
import requests
import os
from app.core.config import settings


# Phone number to test (the one you created in Firebase Console)
PHONE_NUMBER = "+213778788714"  # E.164 format without spaces

# Your API token from .env file
API_TOKEN = settings.API_TOKEN

# Firebase Web API Key (from Firebase Console > Project Settings > General)
FIREBASE_API_KEY = settings.FIREBASE_API_KEY

def setup_firebase_admin():
    """Initialize Firebase Admin SDK with service account credentials"""
    # Path to your service account file - adjust if needed
    service_account_path = "firebase-credentials.json"
    
    # Check if file exists
    if not os.path.exists(service_account_path):
        # Try alternative path
        service_account_path = "app/firebase-credentials.json"
        if not os.path.exists(service_account_path):
            print(f"Error: Firebase credentials file not found at {service_account_path}")
            return False
    
    try:
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
    except Exception as e:
        print(f"User not found: {e}")
        print(f"Creating new user with phone: {phone_number}")
        
        try:
            # Create new user with phone number
            user = auth.create_user(phone_number=phone_number)
            print(f"Created new user with phone: {phone_number}, UID: {user.uid}")
            return user
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

def create_custom_token(uid):
    """Create a custom token for the user"""
    try:
        custom_token = auth.create_custom_token(uid).decode('utf-8')
        print(f"Custom token created successfully")
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
        data = response.json()
        
        if 'idToken' in data:
            print("Successfully obtained Firebase ID token")
            return data['idToken']
        else:
            print(f"Error getting ID token: {data}")
            return None
    except Exception as e:
        print(f"Error in API request: {e}")
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

def test_register_with_token(temp_token):
    """Test the register-with-token endpoint with the temporary token"""
    url = "http://localhost:8001/api/v1/auth/register-with-token"
    headers = {
        "Content-Type": "application/json",
        "API-Token": API_TOKEN
    }
    payload = {
        "temp_token": temp_token,
        "name": "Fahed Kaddou",
        "email": "fahed.kaddou@ryvin.com",
        "profile_image": "https://media.licdn.com/dms/image/v2/D4E03AQHdzfQt5c3gJQ/profile-displayphoto-shrink_400_400/B4EZVg7lTGHcAg-/0/1741087988112?e=1755734400&v=beta&t=rOCY4RpGG2_JNzSO18tRi2iqfpgkTyK7wA328yAP7og"
    }
    
    try:
        print(f"\nSending request to {url}")
        response = requests.post(url, headers=headers, json=payload)
        print(f"Response status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"Response body: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"Error response: {response.text}")
            return None
    except Exception as e:
        print(f"Error testing endpoint: {e}")
        return None

# Main execution
if __name__ == "__main__":
    print("Firebase Phone Authentication Test")
    print("=================================\n")
    
    # Initialize Firebase Admin SDK
    if not setup_firebase_admin():
        print("Failed to initialize Firebase Admin SDK. Exiting.")
        exit(1)
    
    # Get or create user by phone number
    user = get_or_create_user_by_phone(PHONE_NUMBER)
    if not user:
        print(f"Failed to get or create user with phone {PHONE_NUMBER}.")
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
    
    # If we got a successful response with a temporary token, test register-with-token endpoint
    if verify_response and 'access_token' in verify_response:
        print("\nTesting register-with-token endpoint with the received access token...")
        register_response = test_register_with_token(verify_response['access_token'])
        if register_response:
            print("\nRegistration successful!")
    
    print("\nTest completed.")

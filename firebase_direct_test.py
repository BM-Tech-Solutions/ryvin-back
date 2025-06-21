import requests
import json
import time

# Firebase project configuration
FIREBASE_API_KEY = "YOUR_FIREBASE_WEB_API_KEY"  # Replace with your Firebase Web API Key
API_TOKEN = "YOUR_API_TOKEN"  # Replace with your backend API token

# Test phone number and verification code
PHONE_NUMBER = "+213557641451"
VERIFICATION_CODE = "123456"

def verify_phone_number():
    """
    Test Firebase phone authentication using the REST API
    This simulates what the Firebase SDK does on the client side
    """
    # Step 1: Send verification code
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendVerificationCode?key={FIREBASE_API_KEY}"
    payload = {
        "phoneNumber": PHONE_NUMBER,
        "recaptchaToken": "test-token"  # In a real scenario, this would be a valid reCAPTCHA token
    }
    
    print(f"Sending verification code to {PHONE_NUMBER}...")
    response = requests.post(url, json=payload)
    data = response.json()
    
    if 'error' in data:
        print(f"Error sending verification code: {data['error']['message']}")
        print("Note: This direct REST API approach may not work without a valid reCAPTCHA token.")
        print("Consider using the Firebase Admin SDK approach instead.")
        return None
    
    session_info = data.get('sessionInfo')
    print(f"Verification code sent. Session info: {session_info}")
    
    # Step 2: Verify the code
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPhoneNumber?key={FIREBASE_API_KEY}"
    payload = {
        "sessionInfo": session_info,
        "code": VERIFICATION_CODE
    }
    
    print(f"Verifying code {VERIFICATION_CODE}...")
    response = requests.post(url, json=payload)
    data = response.json()
    
    if 'error' in data:
        print(f"Error verifying code: {data['error']['message']}")
        return None
    
    id_token = data.get('idToken')
    refresh_token = data.get('refreshToken')
    
    print(f"Phone verified successfully!")
    print(f"ID Token: {id_token}")
    print(f"Refresh Token: {refresh_token}")
    
    return id_token

def test_backend_verify_phone(id_token):
    """Test the backend /verify-phone endpoint with the Firebase ID token"""
    url = "http://localhost:8000/api/v1/auth/verify-phone"
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
    
    print("\nTesting backend /verify-phone endpoint...")
    response = requests.post(url, headers=headers, json=payload)
    
    try:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except:
        print(f"Error parsing response: {response.text}")
        return None

# Alternative approach using Firebase Admin SDK
def test_with_admin_sdk():
    """
    Note: This function is provided as a reference but requires additional setup.
    You'll need to install firebase-admin package and have service account credentials.
    """
    print("\nThis function requires additional setup and is provided as a reference.")
    print("To use it, uncomment the code and install the firebase-admin package.")
    """
    import firebase_admin
    from firebase_admin import credentials, auth
    
    # Initialize Firebase Admin SDK
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred)
    
    # Create or get user with phone number
    try:
        user = auth.get_user_by_phone_number(PHONE_NUMBER)
        print(f"Found existing user with phone: {PHONE_NUMBER}")
    except:
        user = auth.create_user(phone_number=PHONE_NUMBER)
        print(f"Created new user with phone: {PHONE_NUMBER}")
    
    # Create custom token
    custom_token = auth.create_custom_token(user.uid).decode('utf-8')
    
    # Exchange for ID token
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={FIREBASE_API_KEY}"
    response = requests.post(url, json={"token": custom_token, "returnSecureToken": True})
    data = response.json()
    
    id_token = data.get('idToken')
    print(f"ID Token: {id_token}")
    
    # Test backend endpoint
    return test_backend_verify_phone(id_token)
    """

if __name__ == "__main__":
    print("Firebase Phone Authentication Test")
    print("=================================")
    
    # Try direct REST API approach first
    id_token = verify_phone_number()
    
    if id_token:
        # Test backend endpoint
        test_backend_verify_phone(id_token)
    else:
        print("\nDirect REST API approach failed.")
        print("This is expected as Firebase requires a valid reCAPTCHA token for phone auth.")
        print("\nAlternative options:")
        print("1. Use the Firebase Admin SDK approach (see test_with_admin_sdk function)")
        print("2. Use the Firebase Console to manually create a user with this phone number")
        
        # Uncomment to try the Admin SDK approach
        # test_with_admin_sdk()

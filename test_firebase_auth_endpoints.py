"""
Test Firebase Authentication Endpoints
------------------------------------
This script tests the Firebase authentication endpoints integrated in the auth router.
"""
import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Your API token from .env file
API_TOKEN = os.environ.get("API_TOKEN")

# Base URL for the API
BASE_URL = "http://localhost:8001/api/v1"

# Headers with API token
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_TOKEN}"
}

def test_create_user():
    """Test the register endpoint"""
    print("\n1. Testing Register Endpoint")
    print("-------------------------------")
    
    # Phone number to test
    phone_number = "+213778788714"  # E.164 format without spaces
    
    # Request payload
    payload = {
        "phone_number": phone_number,
        "display_name": "Test User",
        "photo_url": "https://example.com/photo.jpg"
    }
    
    # Make the request
    url = f"{BASE_URL}/auth/register"
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=HEADERS)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response:")
            print(json.dumps(data, indent=2))
            
            # Save the Firebase ID token to a file
            with open('firebase_id_token.txt', 'w') as f:
                f.write(data['firebase_id_token'])
            print("Firebase ID token saved to firebase_id_token.txt")
            
            return data
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def test_verify_user():
    """Test the verify-user endpoint"""
    print("\n2. Testing Verify User Endpoint")
    print("-------------------------------")
    
    # Phone number to test
    phone_number = "+213778788714"  # E.164 format without spaces
    
    # Request payload
    payload = {
        "phone_number": phone_number
    }
    
    # Make the request
    url = f"{BASE_URL}/auth/verify-user"
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=HEADERS)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response:")
            print(json.dumps(data, indent=2))
            return data
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def test_verify_phone(firebase_id_token=None):
    """Test the verify-phone endpoint"""
    print("\n3. Testing Verify Phone Endpoint")
    print("-------------------------------")
    
    # Load Firebase ID token if not provided
    if not firebase_id_token:
        try:
            with open('firebase_id_token.txt', 'r') as f:
                firebase_id_token = f.read().strip()
                print("Firebase ID token loaded from file")
        except FileNotFoundError:
            print("Firebase ID token file not found. Please run test_create_user first.")
            return None
    
    # Request payload
    payload = {
        "firebase_token": firebase_id_token,
        "device_info": {
            "device_id": "test-device-id",
            "platform": "android"
        }
    }
    
    # Make the request
    url = f"{BASE_URL}/auth/verify-phone"
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=HEADERS)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response:")
            print(json.dumps(data, indent=2))
            
            # Save the access token to a file
            with open('access_token.txt', 'w') as f:
                f.write(data['access_token'])
            print("Access token saved to access_token.txt")
            
            # Save the entire response for reference
            with open('verify_phone_response.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("Full response saved to verify_phone_response.json")
            
            return data
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def test_complete_profile(access_token=None):
    """Test the complete-profile endpoint"""
    print("\n4. Testing Complete Profile Endpoint")
    print("----------------------------------")
    
    # Load access token if not provided
    if not access_token:
        try:
            with open('access_token.txt', 'r') as f:
                access_token = f.read().strip()
                print("Access token loaded from file")
        except FileNotFoundError:
            print("Access token file not found. Please run test_verify_phone first.")
            return None
    
    # Request payload
    payload = {
        "access_token": access_token,
        "name": "Test User Updated",
        "email": "test.user.updated@example.com",
        "profile_image": "https://example.com/updated-photo.jpg"
    }
    
    # Make the request
    url = f"{BASE_URL}/auth/complete-profile"
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=HEADERS)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response:")
            print(json.dumps(data, indent=2))
            
            # Save the entire response for reference
            with open('complete_profile_response.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("Full response saved to complete_profile_response.json")
            
            return data
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


# Main execution
if __name__ == "__main__":
    print("Firebase Authentication Endpoints Test")
    print("======================================")
    
    # Test verify user endpoint
    test_verify_user()
    
    # Test register endpoint
    firebase_user = test_create_user()
    
    if firebase_user:
        # Test verify phone endpoint
        verify_result = test_verify_phone(firebase_user.get("firebase_id_token"))
        
        if verify_result:
            # Test complete profile endpoint
            test_complete_profile(verify_result.get("access_token"))
    
    print("\nTest completed!")

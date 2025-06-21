"""
Firebase Complete Profile Script
------------------------------
This script tests the register-with-token endpoint to complete user profile.
"""
import json
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Your API token from .env file
API_TOKEN = os.environ.get("API_TOKEN")

def load_access_token():
    """Load the access token from the file saved by firebase_verify_phone.py"""
    try:
        with open('access_token.txt', 'r') as f:
            token = f.read().strip()
            if token:
                print("Access token loaded successfully")
                return token
            else:
                print("Access token file is empty")
                return None
    except FileNotFoundError:
        print("Access token file not found. Please run firebase_verify_phone.py first.")
        return None
    except Exception as e:
        print(f"Error loading access token: {e}")
        return None

def test_register_with_token(access_token):
    """Test the register-with-token endpoint with the access token"""
    url = "http://localhost:8001/api/v1/auth/register-with-token"
    headers = {
        "Content-Type": "application/json",
        "API-Token": API_TOKEN
    }
    payload = {
        "temp_token": access_token,
        "name": "Fahed Kaddou",
        "email": "fahed2.kaddou@ryvin.com",
        "profile_image": "https://media.licdn.com/dms/image/v2/D4E03AQHdzfQt5c3gJQ/profile-displayphoto-shrink_400_400/B4EZVg7lTGHcAg-/0/1741087988112?e=1755734400&v=beta&t=rOCY4RpGG2_JNzSO18tRi2iqfpgkTyK7wA328yAP7og"
    }
    
    try:
        print(f"\nSending request to {url}")
        print(f"Headers: {headers}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
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
    print("Firebase Complete Profile Test")
    print("============================\n")
    
    # Load access token
    access_token = load_access_token()
    if not access_token:
        print("Failed to load access token. Exiting.")
        exit(1)
    
    # Test register-with-token endpoint
    register_response = test_register_with_token(access_token)
    
    if register_response:
        print("\nProfile completion test completed successfully.")
    else:
        print("\nProfile completion test failed.")

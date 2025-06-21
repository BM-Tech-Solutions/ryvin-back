# Simplified Firebase Authentication Flow

This document explains the simplified Firebase authentication flow implemented in the Ryvin backend.

## Overview

The authentication flow has been simplified to follow these steps:

1. **Frontend**: Send OTP to user's phone using Firebase
2. **Backend**: Verify if user exists
3. **Backend**: Verify phone and create/update user
4. **Backend**: Complete user profile (for new users)

## API Endpoints

### 1. Verify User Exists

```
POST /api/v1/auth/verify-user
```

**Request:**
```json
{
  "phone_number": "+213778788714"
}
```

**Response:**
```json
{
  "exists": true/false,
  "phone_number": "+213778788714",
  "user_id": "uuid-if-exists" // Only included if user exists
}
```

### 2. Verify Phone

```
POST /api/v1/auth/verify-phone
```

**Request:**
```json
{
  "firebase_token": "firebase-id-token-from-frontend",
  "device_info": {
    "device_id": "optional-device-id",
    "platform": "optional-platform-info"
  }
}
```

**Response:**
```json
{
  "user_exists": true/false,
  "profile_complete": true/false,
  "user_id": "user-uuid",
  "access_token": "jwt-access-token",
  "refresh_token": "refresh-token",
  "token_type": "bearer",
  "user": { // Only included if profile_complete is true
    "id": "user-uuid",
    "phone": "+213778788714",
    "name": "User Name",
    "email": "user@example.com",
    "is_verified": true,
    "created_at": "2023-01-01T00:00:00",
    "last_login": "2023-01-01T00:00:00"
  }
}
```

### 3. Complete Profile

```
POST /api/v1/auth/complete-profile
```

**Request:**
```json
{
  "access_token": "jwt-access-token-from-verify-phone",
  "name": "User Name",
  "email": "user@example.com",
  "profile_image": "optional-profile-image-url"
}
```

**Response:**
```json
{
  "user_id": "user-uuid",
  "name": "User Name",
  "email": "user@example.com",
  "profile_image": "profile-image-url-if-provided",
  "access_token": "new-jwt-access-token",
  "refresh_token": "new-refresh-token",
  "token_type": "bearer"
}
```

### 4. Refresh Token

```
POST /api/v1/auth/refresh-token
```

**Request:**
```json
{
  "refresh_token": "refresh-token"
}
```

**Response:**
```json
{
  "access_token": "new-jwt-access-token",
  "refresh_token": "new-refresh-token",
  "token_type": "bearer"
}
```

### 5. Logout

```
POST /api/v1/auth/logout
```

**Request:**
```json
{
  "refresh_token": "refresh-token"
}
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

## Implementation Steps

To implement this new authentication flow:

1. Replace the existing auth service with the new one:
   ```bash
   mv app/services/new_auth_service.py app/services/auth_service.py
   ```

2. Replace the existing auth endpoints with the new ones:
   ```bash
   mv app/api/api_v1/endpoints/new_auth.py app/api/api_v1/endpoints/auth.py
   ```

3. Update the API router:
   ```bash
   mv app/api/api_v1/api_new.py app/api/api_v1/api.py
   ```

4. Restart your application

## Frontend Implementation

In your frontend application:

1. Use Firebase Authentication to send OTP to the user's phone
2. After successful verification, get the Firebase ID token
3. Call the backend API endpoints in sequence:
   - First `/auth/verify-user` to check if the user exists
   - Then `/auth/verify-phone` with the Firebase token
   - If needed, `/auth/complete-profile` to complete the user profile
4. Store the access and refresh tokens for authenticated requests
5. Use `/auth/refresh-token` when the access token expires
6. Use `/auth/logout` when the user logs out

## Notes

- The Firebase user and database user are synchronized during the `/auth/verify-phone` step
- The access token is valid for 30 minutes
- The refresh token is valid for 30 days
- All endpoints except `/auth/refresh-token` and `/auth/logout` require the API key

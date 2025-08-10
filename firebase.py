from functools import lru_cache
import os
import json
import logging

import firebase_admin
from firebase_admin import credentials

from app.core.config import settings


@lru_cache()
def init_firebase():
    # If already initialized, return existing app to avoid ValueError
    try:
        app = firebase_admin.get_app()
        # If app already exists, verify it has a projectId either via options or env
        existing_project = None
        try:
            existing_project = getattr(app, "options", {}).get("projectId")  # type: ignore[attr-defined]
        except Exception:
            existing_project = None

        if os.getenv("GOOGLE_CLOUD_PROJECT") or existing_project:
            # All good, ensure env var mirrors the option if present
            if existing_project and not os.getenv("GOOGLE_CLOUD_PROJECT"):
                os.environ.setdefault("GOOGLE_CLOUD_PROJECT", existing_project)
            return app

        # Otherwise, reinitialize with a resolved project_id
        logging.warning("Existing Firebase app has no projectId; reinitializing with resolved project_id")
        firebase_admin.delete_app(app)
    except ValueError:
        pass  # Not initialized yet

    # Build credentials from file or environment variables
    if settings.FIREBASE_SERVICE_ACCOUNT_PATH:
        cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        # Try in order: explicit env settings -> GOOGLE_CLOUD_PROJECT -> project_id from JSON file
        project_id = (
            settings.FIREBASE_PROJECT_ID
            or settings.FIREBASE_PROJECT_ID_ENV
            or os.getenv("GOOGLE_CLOUD_PROJECT")
        )
        if not project_id:
            try:
                with open(settings.FIREBASE_SERVICE_ACCOUNT_PATH, "r", encoding="utf-8") as f:
                    sa_data = json.load(f)
                    project_id = sa_data.get("project_id")
            except Exception:
                # Fall back silently; Firebase may still infer in some environments
                project_id = None
    else:
        service_account_info = {
            "type": settings.FIREBASE_TYPE,
            # Prefer explicit FIREBASE_PROJECT_ID, then FIREBASE_PROJECT_ID_ENV, then env var
            "project_id": settings.FIREBASE_PROJECT_ID or settings.FIREBASE_PROJECT_ID_ENV or os.getenv("GOOGLE_CLOUD_PROJECT"),
            "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
            "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n') if settings.FIREBASE_PRIVATE_KEY else None,
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
            "client_id": settings.FIREBASE_CLIENT_ID,
            "auth_uri": settings.FIREBASE_AUTH_URI,
            "token_uri": settings.FIREBASE_TOKEN_URI,
            "auth_provider_x509_cert_url": settings.FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
            "client_x509_cert_url": settings.FIREBASE_CLIENT_X509_CERT_URL,
        }
        cred = credentials.Certificate(service_account_info)
        project_id = service_account_info.get("project_id")

    # Ensure we have a project_id; if not, provide clear guidance
    if not project_id:
        logging.error(
            "Firebase init failed: project_id not found. Set one of FIREBASE_PROJECT_ID, FIREBASE_PROJECT_ID_ENV, GOOGLE_CLOUD_PROJECT, or provide a service account JSON with project_id."
        )
        raise RuntimeError(
            "Firebase project_id is required. Set FIREBASE_PROJECT_ID or GOOGLE_CLOUD_PROJECT, or ensure your service account JSON includes project_id."
        )

    # Propagate project_id to env for Firebase internals that rely on GOOGLE_CLOUD_PROJECT
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)

    # Provide projectId explicitly to avoid auth service errors when project ID isn't inferred
    options = {"projectId": project_id} if project_id else None
    return firebase_admin.initialize_app(cred, options or {})

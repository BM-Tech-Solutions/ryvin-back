from functools import lru_cache

import firebase_admin
from firebase_admin import credentials

from app.core.config import settings


@lru_cache()
def init_firebase():
    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)

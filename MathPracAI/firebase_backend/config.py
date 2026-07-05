import json
import os


_firebase_admin = None
_credentials = None
_firestore = None

try:
    import firebase_admin as _firebase_admin
    from firebase_admin import credentials as _credentials
    from firebase_admin import firestore as _firestore
except ImportError:
    _firebase_admin = None


class FirebaseUnavailable(RuntimeError):
    pass


def firebase_available():
    return _firebase_admin is not None


def initialize_firebase():
    if _firebase_admin is None:
        raise FirebaseUnavailable("firebase-admin is not installed. Install requirements.txt first.")

    if _firebase_admin._apps:
        return _firebase_admin.get_app()

    service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    service_account_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    if service_account_json:
        cred = _credentials.Certificate(json.loads(service_account_json))
    elif service_account_path:
        cred = _credentials.Certificate(service_account_path)
    else:
        cred = _credentials.ApplicationDefault()

    return _firebase_admin.initialize_app(cred)


def firestore_client():
    initialize_firebase()
    return _firestore.client()


def server_timestamp():
    if _firestore is None:
        return None
    return _firestore.SERVER_TIMESTAMP

import json
import os
import threading
from pathlib import Path

from config.env import load_environment


load_environment()


_firebase_admin = None
_credentials = None
_firestore = None
_firebase_init_lock = threading.Lock()

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

    with _firebase_init_lock:
        if _firebase_admin._apps:
            return _firebase_admin.get_app()

        service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        service_account_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

        if service_account_json:
            try:
                service_account_data = json.loads(service_account_json)
            except json.JSONDecodeError as exc:
                raise FirebaseUnavailable(
                    "FIREBASE_SERVICE_ACCOUNT_JSON must contain valid service-account JSON."
                ) from exc

            if not isinstance(service_account_data, dict):
                raise FirebaseUnavailable(
                    "FIREBASE_SERVICE_ACCOUNT_JSON must contain a JSON object."
                )

            private_key = service_account_data.get("private_key")
            if isinstance(private_key, str):
                service_account_data["private_key"] = private_key.replace("\\n", "\n")

            try:
                cred = _credentials.Certificate(service_account_data)
            except (OSError, ValueError) as exc:
                raise FirebaseUnavailable(
                    "FIREBASE_SERVICE_ACCOUNT_JSON must contain a valid Firebase service-account JSON object."
                ) from exc
        elif service_account_path:
            service_account_path = Path(service_account_path)
            if not service_account_path.is_absolute():
                service_account_path = Path(__file__).resolve().parent / service_account_path
            if not service_account_path.is_file():
                raise FirebaseUnavailable(
                    "Firebase credentials are not configured: "
                    "FIREBASE_SERVICE_ACCOUNT_JSON is not set and the service-account file "
                    f"does not exist at {service_account_path}."
                )
            try:
                cred = _credentials.Certificate(str(service_account_path))
            except (OSError, ValueError) as exc:
                raise FirebaseUnavailable(
                    f"Firebase service-account file is invalid: {service_account_path}. "
                    "Set FIREBASE_SERVICE_ACCOUNT_JSON or provide a valid credential file."
                ) from exc
        else:
            raise FirebaseUnavailable(
                "Firebase credentials are not configured. Set FIREBASE_SERVICE_ACCOUNT_JSON "
                "or provide a valid FIREBASE_SERVICE_ACCOUNT_PATH."
            )

        return _firebase_admin.initialize_app(cred)


def firestore_client():
    initialize_firebase()
    return _firestore.client()


def server_timestamp():
    if _firestore is None:
        return None
    return _firestore.SERVER_TIMESTAMP

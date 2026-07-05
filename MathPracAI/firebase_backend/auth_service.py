from functools import wraps
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import redirect, session, url_for

from firebase_backend.config import FirebaseUnavailable, initialize_firebase
from firebase_backend.firestore_service import get_user_profile, touch_last_active


try:
    from firebase_admin import auth as firebase_auth
except ImportError:
    firebase_auth = None


class AuthError(RuntimeError):
    pass


def create_auth_user(email, password, first_name, last_name):
    if firebase_auth is None:
        raise AuthError("firebase-admin is not installed. Install requirements.txt first.")
    initialize_firebase()
    display_name = " ".join(part for part in (first_name, last_name) if part).strip()
    user = firebase_auth.create_user(
        email=email.strip().lower(),
        password=password,
        display_name=display_name or None,
    )
    return user.uid


def sign_in_with_email_password(email, password):
    api_key = os.environ.get("FIREBASE_WEB_API_KEY")
    if not api_key:
        raise AuthError("FIREBASE_WEB_API_KEY is required for email/password login.")

    payload = json.dumps(
        {
            "email": email.strip().lower(),
            "password": password,
            "returnSecureToken": True,
        }
    ).encode("utf-8")
    request = Request(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8")
        raise AuthError(_firebase_rest_error(detail)) from error
    except URLError as error:
        raise AuthError("Unable to reach Firebase Auth.") from error

    uid = data.get("localId")
    id_token = data.get("idToken")
    if not uid or not id_token:
        raise AuthError("Firebase Auth did not return a valid login response.")

    verify_id_token(id_token)
    return uid


def verify_id_token(id_token):
    if firebase_auth is None:
        raise AuthError("firebase-admin is not installed. Install requirements.txt first.")
    try:
        initialize_firebase()
        return firebase_auth.verify_id_token(id_token)
    except FirebaseUnavailable as error:
        raise AuthError(str(error)) from error


def login_user(uid):
    session.clear()
    session["uid"] = uid
    touch_last_active(uid)


def logout_user():
    session.clear()


def current_user_profile():
    uid = session.get("uid")
    if not uid:
        return None
    profile = get_user_profile(uid)
    if not profile:
        session.clear()
        return None
    return profile


def role_redirect(profile):
    if profile.get("role") == "student":
        return redirect(url_for("practice.index"))
    return redirect(url_for("dashboard.dashboard"))


def require_login(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user_profile():
            return redirect(url_for("auth.auth_home"))
        return view(*args, **kwargs)

    return wrapped


def require_role(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user_profile()
            if not user:
                return redirect(url_for("auth.auth_home"))
            if user.get("role") not in roles:
                return role_redirect(user)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def _firebase_rest_error(detail):
    try:
        data = json.loads(detail)
        message = data.get("error", {}).get("message", "")
    except (TypeError, ValueError):
        message = ""
    return {
        "EMAIL_NOT_FOUND": "No account exists for that email.",
        "INVALID_PASSWORD": "Incorrect password.",
        "USER_DISABLED": "This account has been disabled.",
        "INVALID_LOGIN_CREDENTIALS": "Invalid email or password.",
    }.get(message, "Unable to sign in with those credentials.")

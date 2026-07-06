from flask import Blueprint, jsonify, redirect, request, url_for

from firebase_backend.auth_service import (
    AuthError,
    create_auth_user,
    current_user_profile,
    firebase_web_config,
    google_user_from_id_token,
    login_user,
    logout_user,
    role_redirect,
    sign_in_with_email_password,
)
from views.auth_views import (
    render_login,
    render_role_select,
    render_student_code_step,
    render_student_signup,
    render_tutor_code_step,
    render_tutor_signup,
)
from firebase_backend.code_service import class_code_profile, tutor_invite_profile
from firebase_backend.firestore_service import create_user_profile, mark_tutor_invite_code_used


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.get("")
def auth_home():
    user = current_user_profile()
    if user:
        return role_redirect(user)
    return render_role_select()


@auth_bp.get("/<role>")
def login_form(role):
    if role not in ("student", "tutor", "admin"):
        return redirect(url_for("auth.auth_home"))
    return render_login(role)


@auth_bp.post("/login")
def login():
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    selected_role = request.form.get("selected_role", "student")
    if not email or not password:
        return render_login(selected_role, "Email and password are required.")
    try:
        uid = sign_in_with_email_password(email, password)
        login_user(uid)
        profile = current_user_profile()
    except AuthError as error:
        return render_login(selected_role, str(error))

    if not profile:
        logout_user()
        return render_login(selected_role, "This account does not have a MathPracAI profile yet.")
    return role_redirect(profile)


@auth_bp.get("/student/signup")
def student_signup_form():
    return render_student_code_step()


@auth_bp.post("/student/signup")
def student_signup():
    step = request.form.get("step", "code")
    if step == "code":
        values = _form_values("class_code")
        if not values["class_code"]:
            return render_student_code_step("Class code is required.", values)
        try:
            class_code = class_code_profile(values["class_code"])
        except Exception as error:
            return render_student_code_step(str(error), values)
        if not class_code:
            return render_student_code_step("Invalid class code.", values)
        return render_student_signup(values=values)

    values = _form_values("first_name", "last_name", "email", "class_code")
    password = request.form.get("password", "")
    error = _required_error(values, password)
    if error:
        return render_student_signup(error, values)

    try:
        class_code = class_code_profile(values["class_code"])
        if not class_code:
            return render_student_signup("Invalid class code.", values)
        uid = create_auth_user(values["email"], password, values["first_name"], values["last_name"])
        profile = create_user_profile(
            uid=uid,
            first_name=values["first_name"],
            last_name=values["last_name"],
            email=values["email"],
            role="student",
            tutor_id=class_code.get("tutorId"),
            auth_provider="email",
        )
        login_user(profile["uid"])
    except Exception as error:
        return render_student_signup(str(error), values)

    return redirect(url_for("practice.index"))


@auth_bp.get("/tutor/signup")
def tutor_signup_form():
    return render_tutor_code_step()


@auth_bp.post("/tutor/signup")
def tutor_signup():
    step = request.form.get("step", "code")
    if step == "code":
        values = _form_values("invite_code")
        if not values["invite_code"]:
            return render_tutor_code_step("Tutor invite code is required.", values)
        try:
            invite = tutor_invite_profile(values["invite_code"])
        except Exception as error:
            return render_tutor_code_step(str(error), values)
        if not invite:
            return render_tutor_code_step("Invalid or used tutor invite code.", values)
        return render_tutor_signup(values=values)

    values = _form_values("first_name", "last_name", "email", "invite_code")
    password = request.form.get("password", "")
    error = _required_error(values, password)
    if error:
        return render_tutor_signup(error, values)

    try:
        invite = tutor_invite_profile(values["invite_code"])
        if not invite:
            return render_tutor_signup("Invalid or used tutor invite code.", values)
        uid = create_auth_user(values["email"], password, values["first_name"], values["last_name"])
        profile = create_user_profile(
            uid=uid,
            first_name=values["first_name"],
            last_name=values["last_name"],
            email=values["email"],
            role="tutor",
            tutor_id=None,
            auth_provider="email",
        )
        mark_tutor_invite_code_used(invite["id"], uid)
        login_user(profile["uid"])
    except Exception as error:
        return render_tutor_signup(str(error), values)

    return redirect(url_for("dashboard.dashboard"))


@auth_bp.get("/firebase-web-config")
def firebase_config():
    try:
        return jsonify({"ok": True, "config": firebase_web_config()})
    except AuthError as error:
        return jsonify({"ok": False, "error": str(error)}), 400


@auth_bp.post("/google-login")
def google_login():
    try:
        google_user = google_user_from_id_token(_json_value("idToken"))
        profile = create_or_login_existing_google_profile(google_user)
    except AuthError as error:
        return jsonify({"ok": False, "error": str(error)}), 400

    login_user(profile["uid"])
    return jsonify({"ok": True, "redirect": redirect_url_for_profile(profile)})


@auth_bp.post("/student/google-signup")
def student_google_signup():
    try:
        google_user = google_user_from_id_token(_json_value("idToken"))
        existing_profile = create_or_login_existing_google_profile(google_user, allow_missing=False)
        if existing_profile:
            login_user(existing_profile["uid"])
            return jsonify({"ok": True, "redirect": redirect_url_for_profile(existing_profile)})

        class_code = class_code_profile(_json_value("classCode"))
        if not class_code:
            raise AuthError("Invalid class code.")

        names = resolved_google_names(google_user)
        if names is None:
            return jsonify({"ok": False, "needsName": True})

        profile = create_user_profile(
            uid=google_user["uid"],
            first_name=names["first_name"],
            last_name=names["last_name"],
            email=google_user["email"],
            role="student",
            tutor_id=class_code.get("tutorId"),
            auth_provider="google",
        )
        login_user(profile["uid"])
        return jsonify({"ok": True, "redirect": url_for("practice.index")})
    except AuthError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 400


@auth_bp.post("/tutor/google-signup")
def tutor_google_signup():
    try:
        google_user = google_user_from_id_token(_json_value("idToken"))
        existing_profile = create_or_login_existing_google_profile(google_user, allow_missing=False)
        if existing_profile:
            login_user(existing_profile["uid"])
            return jsonify({"ok": True, "redirect": redirect_url_for_profile(existing_profile)})

        invite = tutor_invite_profile(_json_value("inviteCode"))
        if not invite:
            raise AuthError("Invalid or used tutor invite code.")

        names = resolved_google_names(google_user)
        if names is None:
            return jsonify({"ok": False, "needsName": True})

        profile = create_user_profile(
            uid=google_user["uid"],
            first_name=names["first_name"],
            last_name=names["last_name"],
            email=google_user["email"],
            role="tutor",
            tutor_id=None,
            auth_provider="google",
        )
        mark_tutor_invite_code_used(invite["id"], google_user["uid"])
        login_user(profile["uid"])
        return jsonify({"ok": True, "redirect": url_for("dashboard.dashboard")})
    except AuthError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 400


@auth_bp.post("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.auth_home"))


def create_or_login_existing_google_profile(google_user, allow_missing=True):
    profile = current_profile_for_uid(google_user["uid"])
    if profile:
        return profile
    if allow_missing:
        raise AuthError("This Google account does not have a MathPracAI profile yet.")
    return None


def current_profile_for_uid(uid):
    from firebase_backend.firestore_service import get_user_profile

    return get_user_profile(uid)


def resolved_google_names(google_user):
    first_name = _json_value("firstName") or google_user.get("first_name", "")
    last_name = _json_value("lastName") or google_user.get("last_name", "")
    if (not first_name or not last_name) and google_user.get("display_name"):
        parts = google_user["display_name"].strip().split()
        if not first_name and parts:
            first_name = parts[0]
        if not last_name and len(parts) > 1:
            last_name = " ".join(parts[1:])
    first_name = first_name.strip()
    last_name = last_name.strip()
    if not first_name or not last_name:
        return None
    return {"first_name": first_name, "last_name": last_name}


def redirect_url_for_profile(profile):
    if profile.get("role") == "student":
        return url_for("practice.index")
    return url_for("dashboard.dashboard")


def _json_value(key):
    data = request.get_json(silent=True) or {}
    return str(data.get(key) or "").strip()


def _form_values(*keys):
    return {key: request.form.get(key, "").strip() for key in keys}


def _required_error(values, password):
    if any(not value for value in values.values()) or not password:
        return "All fields are required."
    return ""

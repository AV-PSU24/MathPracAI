from flask import Blueprint, redirect, request, url_for

from firebase_backend.auth_service import (
    AuthError,
    create_auth_user,
    current_user_profile,
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
        )
        mark_tutor_invite_code_used(invite["id"], uid)
        login_user(profile["uid"])
    except Exception as error:
        return render_tutor_signup(str(error), values)

    return redirect(url_for("dashboard.dashboard"))


@auth_bp.post("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.auth_home"))


def _form_values(*keys):
    return {key: request.form.get(key, "").strip() for key in keys}


def _required_error(values, password):
    if any(not value for value in values.values()) or not password:
        return "All fields are required."
    return ""

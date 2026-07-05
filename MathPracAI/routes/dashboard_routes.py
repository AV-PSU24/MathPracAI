from flask import Blueprint, jsonify, redirect, request, url_for

from firebase_backend.auth_service import current_user_profile, require_role
from firebase_backend.code_service import CodeGenerationError, create_class_code, create_tutor_invite_code
from views.dashboard_views import render_dashboard_page
from firebase_backend.config import FirebaseUnavailable
from firebase_backend.firestore_service import (
    activate_workspace_item,
    close_workspace_item,
    get_student,
    get_tutor,
    get_workspace,
    list_all_students,
    list_students_for_tutor,
    list_tutors,
    open_workspace_item,
)


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.get("")
@require_role("tutor", "admin")
def dashboard():
    return redirect(url_for("dashboard.students"))


@dashboard_bp.get("/students")
@require_role("tutor", "admin")
def students():
    return render_dashboard("students")


@dashboard_bp.get("/tutors")
@require_role("admin")
def tutors():
    return render_dashboard("tutors")


@dashboard_bp.post("/workspace/open/<item_type>/<item_id>")
@require_role("tutor", "admin")
def open_workspace(item_type, item_id):
    user = current_user_profile()
    if item_type not in ("student", "tutor"):
        return redirect(url_for("dashboard.students"))
    if item_type == "tutor" and user.get("role") != "admin":
        return redirect(url_for("dashboard.students"))
    open_workspace_item(user["uid"], item_type, item_id)
    endpoint = "dashboard.tutors" if item_type == "tutor" else "dashboard.students"
    return redirect(url_for(endpoint))


@dashboard_bp.get("/workspace/activate/<item_type>/<item_id>")
@require_role("tutor", "admin")
def activate_workspace(item_type, item_id):
    user = current_user_profile()
    if item_type == "tutor" and user.get("role") != "admin":
        return redirect(url_for("dashboard.students"))
    activate_workspace_item(user["uid"], item_type, item_id)
    endpoint = "dashboard.tutors" if item_type == "tutor" else "dashboard.students"
    return redirect(url_for(endpoint))


@dashboard_bp.post("/workspace/close/<item_type>/<item_id>")
@require_role("tutor", "admin")
def close_workspace(item_type, item_id):
    user = current_user_profile()
    close_workspace_item(user["uid"], item_type, item_id)
    return redirect(request.referrer or url_for("dashboard.students"))


@dashboard_bp.post("/codes/class")
@require_role("tutor", "admin")
def generate_class_code():
    user = current_user_profile()
    label = request.form.get("label", "")
    try:
        code = create_class_code(user["uid"], label)
    except (CodeGenerationError, FirebaseUnavailable, RuntimeError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    return jsonify({"ok": True, "code": code["code"], "id": code["id"]})


@dashboard_bp.post("/codes/tutor")
@require_role("admin")
def generate_tutor_code():
    user = current_user_profile()
    try:
        code = create_tutor_invite_code(user["uid"])
    except (CodeGenerationError, FirebaseUnavailable, RuntimeError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    return jsonify({"ok": True, "code": code["code"], "id": code["id"]})


def render_dashboard(section):
    user = current_user_profile()
    query = request.args.get("q", "").strip()

    try:
        if user.get("role") == "admin":
            students = list_all_students()
            tutors = list_tutors()
        else:
            students = list_students_for_tutor(user["uid"])
            tutors = []
        workspace = get_workspace(user["uid"])
        workspace_students = [student for student in (get_student(uid) for uid in workspace["openStudentIds"]) if student]
        workspace_tutors = [tutor for tutor in (get_tutor(uid) for uid in workspace["openTutorIds"]) if tutor]
        active_student = get_student(workspace.get("activeStudentId"))
        active_tutor = get_tutor(workspace.get("activeTutorId")) if user.get("role") == "admin" else None
    except Exception:
        students = []
        tutors = []
        workspace_students = []
        workspace_tutors = []
        active_student = None
        active_tutor = None

    students = filter_by_name(students, query)
    tutors = filter_by_name(tutors, query)
    return render_dashboard_page(
        user=user,
        section=section,
        students=students,
        tutors=tutors,
        workspace_students=workspace_students,
        workspace_tutors=workspace_tutors,
        active_student=active_student,
        active_tutor=active_tutor,
        query=query,
    )


def filter_by_name(items, query):
    if not query:
        return items
    lowered = query.lower()
    return [item for item in items if lowered in item.get("name", "").lower()]

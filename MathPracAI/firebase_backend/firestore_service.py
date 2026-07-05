from firebase_backend.config import FirebaseUnavailable, firestore_client, server_timestamp


def _db():
    return firestore_client()


def _doc_to_dict(doc):
    data = doc.to_dict() or {}
    data["id"] = doc.id
    return data


def _first(query):
    docs = list(query.limit(1).stream())
    return docs[0] if docs else None


def get_user_profile(uid):
    if not uid:
        return None
    try:
        doc = _db().collection("users").document(uid).get()
    except Exception:
        return None
    if not doc.exists:
        return None
    data = doc.to_dict() or {}
    data["uid"] = uid
    return data


def create_user_profile(uid, first_name, last_name, email, role, tutor_id=None):
    data = {
        "firstName": first_name.strip(),
        "lastName": last_name.strip(),
        "email": email.strip().lower(),
        "role": role,
        "tutorId": tutor_id,
        "createdAt": server_timestamp(),
        "lastActiveAt": server_timestamp(),
    }
    _db().collection("users").document(uid).set(data)
    data["uid"] = uid
    return data


def touch_last_active(uid):
    if not uid:
        return
    try:
        _db().collection("users").document(uid).set({"lastActiveAt": server_timestamp()}, merge=True)
    except Exception:
        return


def validate_class_code(code):
    normalized = normalize_code(code)
    if not normalized:
        return None
    query = (
        _db()
        .collection("classCodes")
        .where("code", "==", normalized)
        .where("active", "==", True)
    )
    doc = _first(query)
    return _doc_to_dict(doc) if doc else None


def validate_tutor_invite_code(code):
    normalized = normalize_code(code)
    if not normalized:
        return None
    query = (
        _db()
        .collection("tutorInviteCodes")
        .where("code", "==", normalized)
        .where("active", "==", True)
        .where("used", "==", False)
    )
    doc = _first(query)
    return _doc_to_dict(doc) if doc else None


def mark_tutor_invite_code_used(code_id, uid):
    _db().collection("tutorInviteCodes").document(code_id).set(
        {
            "used": True,
            "usedBy": uid,
            "usedAt": server_timestamp(),
        },
        merge=True,
    )


def normalize_code(code):
    return "".join(str(code or "").upper().split())


def code_exists(code):
    normalized = normalize_code(code)
    if not normalized:
        return False
    for collection in ("classCodes", "tutorInviteCodes"):
        doc = _first(_db().collection(collection).where("code", "==", normalized))
        if doc:
            return True
    return False


def save_class_code(code, tutor_id, label):
    data = {
        "code": normalize_code(code),
        "tutorId": tutor_id,
        "label": label.strip(),
        "active": True,
        "createdAt": server_timestamp(),
    }
    ref = _db().collection("classCodes").document()
    ref.set(data)
    data["id"] = ref.id
    return data


def save_tutor_invite_code(code, admin_id):
    data = {
        "code": normalize_code(code),
        "active": True,
        "used": False,
        "usedBy": None,
        "createdByAdminId": admin_id,
        "createdAt": server_timestamp(),
        "usedAt": None,
    }
    ref = _db().collection("tutorInviteCodes").document()
    ref.set(data)
    data["id"] = ref.id
    return data


def list_students_for_tutor(tutor_id):
    if not tutor_id:
        return []
    query = (
        _db()
        .collection("users")
        .where("role", "==", "student")
        .where("tutorId", "==", tutor_id)
    )
    return [_student_card_data(doc) for doc in query.stream()]


def list_all_students():
    query = _db().collection("users").where("role", "==", "student")
    return [_student_card_data(doc) for doc in query.stream()]


def list_tutors():
    query = _db().collection("users").where("role", "in", ["tutor", "admin"])
    return [_tutor_card_data(doc) for doc in query.stream()]


def get_student(student_id):
    profile = get_user_profile(student_id)
    if not profile or profile.get("role") != "student":
        return None
    return _student_profile_data(profile)


def get_tutor(tutor_id):
    profile = get_user_profile(tutor_id)
    if not profile or profile.get("role") not in ("tutor", "admin"):
        return None
    return _tutor_profile_data(profile)


def class_code_count_for_tutor(tutor_id):
    query = (
        _db()
        .collection("classCodes")
        .where("tutorId", "==", tutor_id)
        .where("active", "==", True)
    )
    return sum(1 for _doc in query.stream())


def student_count_for_tutor(tutor_id):
    query = _db().collection("users").where("role", "==", "student").where("tutorId", "==", tutor_id)
    return sum(1 for _doc in query.stream())


def get_workspace(user_id):
    default = {
        "openStudentIds": [],
        "openTutorIds": [],
        "activeStudentId": None,
        "activeTutorId": None,
    }
    if not user_id:
        return default
    doc = _db().collection("tutorWorkspaces").document(user_id).get()
    if not doc.exists:
        return default
    data = doc.to_dict() or {}
    default.update(
        {
            "openStudentIds": list(data.get("openStudentIds") or []),
            "openTutorIds": list(data.get("openTutorIds") or []),
            "activeStudentId": data.get("activeStudentId"),
            "activeTutorId": data.get("activeTutorId"),
        }
    )
    return default


def save_workspace(user_id, workspace):
    data = {
        "openStudentIds": list(dict.fromkeys(workspace.get("openStudentIds") or [])),
        "openTutorIds": list(dict.fromkeys(workspace.get("openTutorIds") or [])),
        "activeStudentId": workspace.get("activeStudentId"),
        "activeTutorId": workspace.get("activeTutorId"),
        "updatedAt": server_timestamp(),
    }
    _db().collection("tutorWorkspaces").document(user_id).set(data, merge=True)
    return data


def open_workspace_item(user_id, item_type, item_id):
    workspace = get_workspace(user_id)
    if item_type == "student":
        workspace["openStudentIds"] = _add_unique(workspace["openStudentIds"], item_id)
        workspace["activeStudentId"] = item_id
        workspace["activeTutorId"] = None
    elif item_type == "tutor":
        workspace["openTutorIds"] = _add_unique(workspace["openTutorIds"], item_id)
        workspace["activeTutorId"] = item_id
        workspace["activeStudentId"] = None
    return save_workspace(user_id, workspace)


def activate_workspace_item(user_id, item_type, item_id):
    workspace = get_workspace(user_id)
    if item_type == "student":
        workspace["activeStudentId"] = item_id
        workspace["activeTutorId"] = None
    elif item_type == "tutor":
        workspace["activeTutorId"] = item_id
        workspace["activeStudentId"] = None
    return save_workspace(user_id, workspace)


def close_workspace_item(user_id, item_type, item_id):
    workspace = get_workspace(user_id)
    if item_type == "student":
        workspace["openStudentIds"] = [value for value in workspace["openStudentIds"] if value != item_id]
        if workspace.get("activeStudentId") == item_id:
            workspace["activeStudentId"] = None
    elif item_type == "tutor":
        workspace["openTutorIds"] = [value for value in workspace["openTutorIds"] if value != item_id]
        if workspace.get("activeTutorId") == item_id:
            workspace["activeTutorId"] = None
    return save_workspace(user_id, workspace)


def record_completed_test_result(student_id, tutor_id, score, total_questions, correct_count, topic, result_json):
    data = {
        "studentId": student_id,
        "tutorId": tutor_id,
        "score": score,
        "totalQuestions": total_questions,
        "correctCount": correct_count,
        "topic": topic,
        "completedAt": server_timestamp(),
        "resultJson": result_json,
    }
    ref = _db().collection("testResults").document()
    ref.set(data)
    data["id"] = ref.id
    return data


def latest_test_for_student(student_id):
    query = (
        _db()
        .collection("testResults")
        .where("studentId", "==", student_id)
        .order_by("completedAt", direction="DESCENDING")
    )
    doc = _first(query)
    return _doc_to_dict(doc) if doc else None


def _add_unique(values, value):
    return list(dict.fromkeys([*values, value]))


def _full_name(data):
    return " ".join(part for part in (data.get("firstName"), data.get("lastName")) if part).strip() or data.get("email", "Unknown")


def _student_card_data(doc):
    data = doc.to_dict() or {}
    uid = doc.id
    latest = latest_test_for_student(uid)
    score = latest.get("score") if latest else None
    return {
        "id": uid,
        "name": _full_name(data),
        "email": data.get("email", ""),
        "lastTestScore": score,
        "lastActive": _display_last_active(data.get("lastActiveAt")),
        "needsHelp": _needs_help(latest),
        "daysInactive": None,
    }


def _student_profile_data(profile):
    latest = latest_test_for_student(profile["uid"])
    return {
        "id": profile["uid"],
        "name": _full_name(profile),
        "email": profile.get("email", ""),
        "lastTestScore": latest.get("score") if latest else None,
        "lastActive": _display_last_active(profile.get("lastActiveAt")),
        "needsHelp": _needs_help(latest),
        "recentTests": [latest] if latest else [],
    }


def _tutor_card_data(doc):
    data = doc.to_dict() or {}
    uid = doc.id
    return {
        "id": uid,
        "name": _full_name(data),
        "email": data.get("email", ""),
        "studentCount": student_count_for_tutor(uid),
        "activeClassCodes": class_code_count_for_tutor(uid),
        "lastActive": _display_last_active(data.get("lastActiveAt")),
    }


def _tutor_profile_data(profile):
    uid = profile["uid"]
    return {
        "id": uid,
        "name": _full_name(profile),
        "email": profile.get("email", ""),
        "studentCount": student_count_for_tutor(uid),
        "activeClassCodes": class_code_count_for_tutor(uid),
        "lastActive": _display_last_active(profile.get("lastActiveAt")),
    }


def _display_last_active(value):
    if not value:
        return "No activity yet"
    return "Recently"


def _needs_help(latest_result):
    if not latest_result:
        return None
    score = latest_result.get("score")
    if isinstance(score, (int, float)) and score < 80:
        return latest_result.get("topic") or "Recent test"
    return None

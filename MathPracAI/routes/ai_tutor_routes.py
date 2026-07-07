from flask import Blueprint, jsonify, request

from services.ai_tutor.service import AITutorError, create_tutor_reply


ai_tutor_bp = Blueprint("ai_tutor", __name__, url_prefix="/ai-tutor")


@ai_tutor_bp.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    student_message = str(data.get("studentMessage") or "").strip()
    if not student_message:
        return jsonify({"ok": False, "error": "studentMessage is required."}), 400

    try:
        return jsonify(create_tutor_reply(student_message, data))
    except AITutorError as error:
        return jsonify({"ok": False, "error": str(error)}), 502

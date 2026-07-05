import secrets

from firebase_backend.firestore_service import (
    code_exists,
    normalize_code,
    save_class_code,
    save_tutor_invite_code,
    validate_class_code,
    validate_tutor_invite_code,
)


CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 6
MAX_GENERATION_ATTEMPTS = 100


class CodeGenerationError(RuntimeError):
    pass


def generate_random_code():
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def generate_unique_code():
    for _attempt in range(MAX_GENERATION_ATTEMPTS):
        code = generate_random_code()
        if not code_exists(code):
            return code
    raise CodeGenerationError("Unable to generate a unique code. Try again.")


def create_class_code(tutor_id, label):
    if not label or not label.strip():
        raise CodeGenerationError("Class name is required.")
    code = generate_unique_code()
    return save_class_code(code, tutor_id, label)


def create_tutor_invite_code(admin_id):
    code = generate_unique_code()
    return save_tutor_invite_code(code, admin_id)


def class_code_profile(code):
    return validate_class_code(normalize_code(code))


def tutor_invite_profile(code):
    return validate_tutor_invite_code(normalize_code(code))

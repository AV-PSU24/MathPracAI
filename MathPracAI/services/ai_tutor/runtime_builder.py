from enum import Enum
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
PROMPT_ROOT = ROOT / "prompts" / "ai_tutor"


class RuntimeState(Enum):
    GUIDED_LEARNING = "guided_learning"
    ANSWER_VERIFICATION = "answer_verification"
    SOLUTION_LOCKED = "solution_locked"
    SOLUTION_EXPLANATION = "solution_explanation"
    HOMEWORK_REVIEW = "homework_review"
    EXAM_MODE = "exam_mode"
    TUTOR_REVIEW = "tutor_review"
    PARENT_REVIEW = "parent_review"


RUNTIME_PROMPT_FILES = {
    RuntimeState.GUIDED_LEARNING: PROMPT_ROOT / "runtime" / "guided_learning.txt",
    RuntimeState.ANSWER_VERIFICATION: PROMPT_ROOT / "runtime" / "answer_verification.txt",
    RuntimeState.SOLUTION_LOCKED: PROMPT_ROOT / "runtime" / "solution_locked.txt",
    RuntimeState.SOLUTION_EXPLANATION: PROMPT_ROOT / "runtime" / "solution_explanation.txt",
    RuntimeState.HOMEWORK_REVIEW: PROMPT_ROOT / "runtime" / "homework_review.txt",
    RuntimeState.EXAM_MODE: PROMPT_ROOT / "runtime" / "exam_mode.txt",
    RuntimeState.TUTOR_REVIEW: PROMPT_ROOT / "runtime" / "tutor_review.txt",
    RuntimeState.PARENT_REVIEW: PROMPT_ROOT / "runtime" / "parent_review.txt",
}


def determine_runtime_state(session):
    message = session.student_message.lower()
    if asks_for_answer_verification(message):
        return RuntimeState.ANSWER_VERIFICATION
    if asks_for_solution(message):
        if session.attempt_count >= 3 or session.solution_unlocked:
            return RuntimeState.SOLUTION_EXPLANATION
        return RuntimeState.SOLUTION_LOCKED
    return RuntimeState.GUIDED_LEARNING


def asks_for_solution(message):
    patterns = (
        r"\bgive me (the )?(answer|solution)\b",
        r"\bjust (give|tell|show) me\b",
        r"\bshow me (the )?(solution|answer)\b",
        r"\btell me (the )?(answer|solution)\b",
        r"\btell me exactly what to type\b",
        r"\bwhat should i type\b",
        r"\bi give up\b",
        r"\bfinal answer\b",
        r"\breveal (the )?(solution|answer)\b",
    )
    return any(re.search(pattern, message) for pattern in patterns)


def asks_for_answer_verification(message):
    patterns = (
        r"\bis (this|that|my answer|the answer) correct\b",
        r"\bam i right\b",
        r"\bdid i get (it|this|that) right\b",
        r"\bwould the answer be\b",
        r"\bcould the answer be\b",
        r"\bdoes .* look correct\b",
        r"\bcheck my answer\b",
        r"\bverify my answer\b",
    )
    return any(re.search(pattern, message) for pattern in patterns)


def build_runtime_prompt(session):
    runtime_state = session.runtime_state
    prompt_path = RUNTIME_PROMPT_FILES[runtime_state]
    return runtime_state, prompt_path.read_text(encoding="utf-8").strip()

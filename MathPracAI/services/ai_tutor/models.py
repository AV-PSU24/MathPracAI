from dataclasses import dataclass, field, replace
from typing import Any, Optional

from llm.llm_client import LLMResponse
from services.ai_tutor.runtime_builder import RuntimeState


@dataclass(frozen=True)
class MiloSession:
    student_message: str
    unit: str = ""
    topic: str = ""
    problem: dict[str, Any] = field(default_factory=dict)
    attempts: list[dict[str, Any]] = field(default_factory=list)
    chat_history: list[dict[str, Any]] = field(default_factory=list)
    attempt_count: int = 0
    solution_unlocked: bool = False
    help_status: str = "none"
    runtime_state: RuntimeState = RuntimeState.GUIDED_LEARNING
    tutor_metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_request(cls, student_message, context=None):
        context = context or {}
        return cls(
            student_message=(student_message or "").strip(),
            unit=str(context.get("unit") or "").strip(),
            topic=str(context.get("topic") or "").strip(),
            problem=_dict_value(context.get("problem")),
            attempts=_list_of_dicts(context.get("attempts")),
            chat_history=_list_of_dicts(context.get("chatHistory")),
            attempt_count=_int_value(context.get("attemptCount")),
            solution_unlocked=_bool_value(context.get("solutionUnlocked")),
            help_status=str(context.get("helpStatus") or "none").strip() or "none",
            tutor_metadata=_dict_value(context.get("tutorMetadata")),
        )

    def with_runtime_state(self, runtime_state):
        return replace(self, runtime_state=runtime_state)


@dataclass(frozen=True)
class PromptComponent:
    name: str
    content: str


@dataclass(frozen=True)
class AITutorResponse:
    reply: str
    help_status: str
    diagnosis: Any = None
    suggested_actions: list[Any] = field(default_factory=list)
    raw_model_response: Optional[LLMResponse] = None
    assembled_prompt: str = ""

    def to_public_dict(self):
        return {
            "ok": True,
            "reply": self.reply,
            "helpStatus": self.help_status,
            "diagnosis": self.diagnosis,
            "suggestedActions": self.suggested_actions,
        }


def _dict_value(value):
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value):
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _int_value(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _bool_value(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)

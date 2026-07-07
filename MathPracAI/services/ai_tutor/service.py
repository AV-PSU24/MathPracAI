from llm.llm_client import LLMConfigurationError, LLMProviderError, generate_text
from services.ai_tutor.models import AITutorResponse, MiloSession
from services.ai_tutor.prompt_builder import build_prompt
from services.ai_tutor.runtime_builder import determine_runtime_state


DEFAULT_HELP_STATUS = "hint"


class AITutorError(RuntimeError):
    pass


def create_tutor_response(student_message, context=None):
    session = MiloSession.from_request(student_message, context)
    if not session.student_message:
        raise ValueError("studentMessage is required.")
    session = session.with_runtime_state(determine_runtime_state(session))

    prompt, runtime_state = build_prompt(session)
    try:
        model_response = generate_text(prompt)
    except (LLMConfigurationError, LLMProviderError) as error:
        raise AITutorError(str(error)) from error

    return AITutorResponse(
        reply=model_response.text,
        help_status=_response_help_status(session, runtime_state),
        diagnosis=None,
        suggested_actions=[],
        raw_model_response=model_response,
        assembled_prompt=prompt,
    )


def create_tutor_reply(student_message, context=None):
    return create_tutor_response(student_message, context).to_public_dict()


def _response_help_status(session, runtime_state):
    if session.help_status == "solution":
        return "solution"
    if runtime_state.value == "solution_explanation":
        return "solution"
    return DEFAULT_HELP_STATUS

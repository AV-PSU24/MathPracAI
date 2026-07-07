from llm.llm_client import LLMConfigurationError, LLMProviderError, generate_text
from services.ai_tutor.models import AITutorResponse, MiloSession
from services.ai_tutor.prompt_builder import build_prompt


DEFAULT_HELP_STATUS = "hint"


class AITutorError(RuntimeError):
    pass


def create_tutor_response(student_message, context=None):
    session = MiloSession.from_request(student_message, context)
    if not session.student_message:
        raise ValueError("studentMessage is required.")

    prompt, runtime_state = build_prompt(session)
    try:
        model_response = generate_text(prompt)
    except (LLMConfigurationError, LLMProviderError) as error:
        raise AITutorError(str(error)) from error

    return AITutorResponse(
        reply=model_response.text,
        help_status=_response_help_status(runtime_state),
        diagnosis=None,
        suggested_actions=[],
        raw_model_response=model_response,
        assembled_prompt=prompt,
    )


def create_tutor_reply(student_message, context=None):
    return create_tutor_response(student_message, context).to_public_dict()


def _response_help_status(runtime_state):
    return DEFAULT_HELP_STATUS

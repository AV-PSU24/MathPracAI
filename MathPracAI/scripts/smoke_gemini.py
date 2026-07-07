git simport sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm.llm_client import (
    LLMConfigurationError,
    LLMProviderError,
    create_llm_client,
    llm_environment_status,
)


SMOKE_PROMPT = "Hello, say hi in one short sentence."


def main():
    status = llm_environment_status()
    print("GEMINI_API_KEY detected:", status["api_key_detected"])
    print("GEMINI_MODEL:", status["model"])

    if not status["api_key_detected"]:
        print("Gemini smoke test skipped: GEMINI_API_KEY is missing.")
        return 1

    try:
        response = create_llm_client().generate_text(SMOKE_PROMPT)
    except (LLMConfigurationError, LLMProviderError, ValueError) as error:
        print("Gemini responded successfully: False")
        print("Gemini smoke test error:", error)
        return 1

    print("Gemini responded successfully:", bool(response.text))
    print("Response:", response.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import os
from dataclasses import dataclass

from config.env import load_environment


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
PROVIDER_GEMINI = "gemini"


class LLMConfigurationError(RuntimeError):
    pass


class LLMProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    provider: str
    raw_response: object = None


class GeminiLLMClient:
    def __init__(self, api_key=None, model=None):
        load_environment()
        self.api_key = (api_key or os.environ.get("GEMINI_API_KEY") or "").strip()
        self.model = (model or os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL).strip()
        self.provider = PROVIDER_GEMINI
        self._client = None

        if not self.api_key:
            raise LLMConfigurationError("GEMINI_API_KEY is required.")
        if not self.model:
            self.model = DEFAULT_GEMINI_MODEL

    def generate_text(self, prompt):
        prompt = (prompt or "").strip()
        if not prompt:
            raise ValueError("Prompt is required.")

        try:
            response = self._gemini_client().models.generate_content(
                model=self.model,
                contents=prompt,
            )
        except Exception as error:
            raise LLMProviderError(f"Gemini request failed: {error}") from error

        text = (getattr(response, "text", "") or "").strip()
        if not text:
            raise LLMProviderError("Gemini returned an empty response.")
        return LLMResponse(text=text, model=self.model, provider=self.provider, raw_response=response)

    def _gemini_client(self):
        if self._client is None:
            try:
                from google import genai
            except ImportError as error:
                raise LLMConfigurationError(
                    "google-genai is required. Install requirements.txt first."
                ) from error
            self._client = genai.Client(api_key=self.api_key)
        return self._client


def llm_environment_status():
    load_environment()
    return {
        "provider": PROVIDER_GEMINI,
        "api_key_detected": bool((os.environ.get("GEMINI_API_KEY") or "").strip()),
        "model": (os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL).strip(),
    }


def create_llm_client():
    return GeminiLLMClient()


def generate_text(prompt):
    return create_llm_client().generate_text(prompt)

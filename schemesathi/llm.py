"""Which AI model the agent uses: Groq's free API, with backups tried in order."""
import os

from crewai import LLM

from . import config

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def model_chain() -> list[str]:
    return [m for m in config.MODELS if not m.startswith("groq/") or os.getenv("GROQ_API_KEY")]


def make_llm(model: str) -> LLM:
    kwargs = {"temperature": 0.1, "max_tokens": 3000}
    if "gpt-oss" in model:
        kwargs["reasoning_effort"] = "low"          # shorter hidden thinking, faster answers
    if "qwen" in model:
        kwargs["max_tokens"] = 900                  # Groq's free plan caps Qwen output per minute
    if model.startswith("groq/"):
        # Groq speaks the OpenAI API; CrewAI's native client avoids a field Groq rejects.
        return LLM(model=model.removeprefix("groq/"), provider="openai", base_url=GROQ_BASE_URL,
                   api_key=os.getenv("GROQ_API_KEY"), **kwargs)
    return LLM(model=model, **kwargs)

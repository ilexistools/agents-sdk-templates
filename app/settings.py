"""Model provider settings stored in the project's .env file.

Secrets are write-only: they are saved to .env and to the running process
environment, but only a masked hint is ever returned.
"""

import os
import re
from pathlib import Path

from dotenv import dotenv_values, find_dotenv, set_key, unset_key

from app.orchestration.config import DEFAULT_DECISION_MODEL, DEFAULT_MODEL, DEFAULT_SANDBOX_MODEL

FIELDS = [
    {"key": "OPENAI_API_KEY", "group": "OpenAI", "label": "API key", "secret": True,
     "help": "Required by agents that use OpenAI models."},
    {"key": "OPENAI_MODEL_NAME", "group": "OpenAI", "label": "Default model", "default": DEFAULT_MODEL,
     "help": "Used by GPT and GPTAgent unless an agent prompt sets its own model."},
    {"key": "OPENAI_SANDBOX_MODEL_NAME", "group": "OpenAI", "label": "Sandbox model",
     "default": DEFAULT_SANDBOX_MODEL, "help": "Used by GPTSandboxAgent."},
    {"key": "OPENAI_DECISION_MODEL_NAME", "group": "OpenAI", "label": "Decision model",
     "default": DEFAULT_DECISION_MODEL, "help": "Used by GPTDecision."},
    {"key": "LOCAL_BASE_URL", "group": "Local or compatible provider", "label": "Base URL",
     "default": "http://localhost:1234/v1",
     "help": "OpenAI-compatible endpoint, e.g. LM Studio, Ollama (http://localhost:11434/v1) or DeepSeek."},
    {"key": "LOCAL_MODEL_NAME", "group": "Local or compatible provider", "label": "Model",
     "default": "local-model", "help": "Model name served by that endpoint."},
    {"key": "LOCAL_API_KEY", "group": "Local or compatible provider", "label": "API key", "secret": True,
     "help": "Leave empty for local servers that do not check keys."},
    {"key": "LOCAL_DISABLE_TRACING", "group": "Local or compatible provider", "label": "Disable tracing",
     "default": "true", "choices": ["true", "false"],
     "help": "Keep true to avoid sending traces to OpenAI when using another provider."},
]
KEYS = {field["key"]: field for field in FIELDS}


def env_file() -> Path:
    configured = os.environ.get("CATALOG_ENV_FILE")
    if configured:
        return Path(configured)
    found = find_dotenv()  # searches upward from this file, like load_environment
    return Path(found) if found else Path(__file__).resolve().parents[1] / ".env"


def configured_value(key: str) -> str:
    """Value from the process environment or, failing that, from the .env file."""
    if os.environ.get(key):
        return os.environ[key]
    path = env_file()
    return (dotenv_values(path).get(key) or "") if path.exists() else ""


def _hint(value: str) -> str:
    return "••••" + value[-4:] if len(value) > 8 else "••••"


def read_settings() -> list[dict]:
    path = env_file()
    stored = dotenv_values(path) if path.exists() else {}
    result = []
    for field in FIELDS:
        key = field["key"]
        value = stored.get(key) or os.environ.get(key) or ""
        source = "env file" if stored.get(key) else "environment" if os.environ.get(key) else "default"
        entry = {name: field[name] for name in ("key", "group", "label", "help", "secret") if name in field}
        entry.update(default=field.get("default", ""), choices=field.get("choices"), source=source, set=bool(value))
        if field.get("secret"):
            entry["hint"] = _hint(value) if value else ""
        else:
            entry["value"] = value
        result.append(entry)
    return result


def validate(key: str, value: str) -> None:
    field = KEYS.get(key)
    if field is None:
        raise ValueError(f"Unknown setting: {key}.")
    if re.search(r"[\r\n\0]", value) or len(value) > 512:
        raise ValueError(f"{field['label']}: invalid value.")
    if field.get("choices") and value and value not in field["choices"]:
        raise ValueError(f"{field['label']}: choose one of {', '.join(field['choices'])}.")
    if key == "LOCAL_BASE_URL" and value and not re.match(r"^https?://\S+$", value):
        raise ValueError("Base URL must start with http:// or https://.")


def update_settings(changes: dict[str, str | None]) -> list[dict]:
    """Apply changes. A string sets the value; None or "" removes it (falls back to the default)."""
    for key, value in changes.items():
        validate(key, value or "")
    path = env_file()
    path.touch(exist_ok=True)
    for key, value in changes.items():
        if value:
            set_key(path, key, value, quote_mode="always")
            os.environ[key] = value
        else:
            if key in dotenv_values(path):
                unset_key(path, key)
            os.environ.pop(key, None)
    return read_settings()

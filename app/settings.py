"""Model provider settings stored in the project's .env file.

Secrets are write-only: they are saved to .env and to the running process
environment, but only a masked hint is ever returned.
"""

import os
import re
from pathlib import Path

from dotenv import dotenv_values, find_dotenv, set_key, unset_key

from app.orchestration.config import DEFAULT_DECISION_MODEL, DEFAULT_MODEL, DEFAULT_SANDBOX_MODEL
from app.orchestration.providers import PROVIDERS


def _provider_fields() -> list[dict]:
    fields = []
    for provider in PROVIDERS.values():
        group = {"group": provider.label, "provider": provider.id}
        if provider.base_url_env:
            fields.append({**group, "key": provider.base_url_env, "label": "Base URL", "default": provider.base_url,
                           "help": provider.notes or "OpenAI-compatible endpoint."})
        if provider.key_env:
            help_text = ("Leave empty for servers that do not check keys." if provider.key_optional
                         else f"Needed for {provider.label} models ({provider.id}:<model>).")
            fields.append({**group, "key": provider.key_env, "label": "API key", "secret": True, "help": help_text})
    return fields


FIELDS = [
    {"key": "DEFAULT_MODEL", "group": "Default model", "label": "Model for agents",
     "default": f"openai:{DEFAULT_MODEL}",
     "help": "provider:model used by agents that do not choose one, e.g. anthropic:claude-sonnet-5-5 or ollama:llama3.2."},
    *_provider_fields(),
    {"key": "OPENAI_MODEL_NAME", "group": "OpenAI", "provider": "openai", "label": "Default OpenAI model",
     "default": DEFAULT_MODEL, "help": "Used by the GPT wrappers when called directly in code."},
    {"key": "OPENAI_SANDBOX_MODEL_NAME", "group": "OpenAI", "provider": "openai", "label": "Sandbox model",
     "default": DEFAULT_SANDBOX_MODEL, "help": "Used by GPTSandboxAgent."},
    {"key": "OPENAI_DECISION_MODEL_NAME", "group": "OpenAI", "provider": "openai", "label": "Decision model",
     "default": DEFAULT_DECISION_MODEL, "help": "Used by GPTDecision."},
    {"key": "LOCAL_MODEL_NAME", "group": PROVIDERS["local"].label, "provider": "local", "label": "Default model",
     "default": "local-model", "help": "Used by GPTLocal and GPTLocalAgent when called directly in code."},
    {"key": "LOCAL_DISABLE_TRACING", "group": "Advanced", "label": "Disable tracing for other providers",
     "default": "true", "choices": ["true", "false"],
     "help": "Keep true so runs on non-OpenAI providers do not send traces to OpenAI."},
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
        entry = {name: field[name] for name in ("key", "group", "label", "help", "secret", "provider") if name in field}
        entry.update(default=field.get("default", ""), choices=field.get("choices"), source=source, set=bool(value))
        if field.get("secret"):
            entry["hint"] = _hint(value) if value else ""
        else:
            entry["value"] = value
        result.append(entry)
    return result


def validate_model_ref(value: str) -> None:
    prefix, sep, model = value.strip().partition(":")
    if not sep or prefix not in PROVIDERS or not model.strip():
        raise ValueError(f"Use provider:model, where provider is one of: {', '.join(PROVIDERS)}.")


def providers_status() -> list[dict]:
    """Providers with their example models and whether they can be used right now."""
    from app.orchestration.providers import ResolvedModel

    result = []
    for provider in PROVIDERS.values():
        missing = ResolvedModel(provider, "").missing_key
        result.append({
            "id": provider.id,
            "label": provider.label,
            "examples": [f"{provider.id}:{model}" for model in provider.examples],
            "ready": missing is None,
            "local": not provider.key_env or provider.key_optional,
        })
    return result


def validate(key: str, value: str) -> None:
    field = KEYS.get(key)
    if field is None:
        raise ValueError(f"Unknown setting: {key}.")
    if re.search(r"[\r\n\0]", value) or len(value) > 512:
        raise ValueError(f"{field['label']}: invalid value.")
    if field.get("choices") and value and value not in field["choices"]:
        raise ValueError(f"{field['label']}: choose one of {', '.join(field['choices'])}.")
    if key == "DEFAULT_MODEL" and value:
        validate_model_ref(value)
    if key.endswith("_BASE_URL") and value and not re.match(r"^https?://\S+$", value):
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

"""Provider-agnostic model selection.

A *model reference* names a provider and a model in one string::

    openai:gpt-4.1-mini
    anthropic:claude-sonnet-5-5
    ollama:llama3.2:3b          # everything after the first ":" is the model name
    gpt-4.1-mini                # no known prefix -> the default provider

Every provider except OpenAI is reached through its OpenAI-compatible endpoint,
so one code path serves all of them. Use :func:`create_agent` instead of
instantiating ``GPTAgent``/``GPTLocalAgent`` directly.

Resolution order for an agent's model:
1. ``model`` passed to :func:`create_agent` (or the per-item override set by the catalog);
2. ``model:`` in the agent's Markdown front matter;
3. the ``DEFAULT_MODEL`` setting (falls back to ``openai:<OPENAI_MODEL_NAME>``).
"""

import os
from contextvars import ContextVar
from dataclasses import dataclass

from app.orchestration.config import default_model, load_environment


@dataclass(frozen=True)
class Provider:
    id: str
    label: str
    base_url: str
    key_env: str = ""              # API key setting; empty when no key is needed
    key_optional: bool = False     # local servers usually accept any key
    base_url_env: str = ""         # setting that overrides base_url
    examples: tuple[str, ...] = ()
    notes: str = ""


PROVIDERS: dict[str, Provider] = {p.id: p for p in (
    Provider("openai", "OpenAI", "https://api.openai.com/v1", "OPENAI_API_KEY",
             examples=("gpt-4.1-mini", "gpt-4.1", "gpt-5-mini")),
    Provider("anthropic", "Anthropic", "https://api.anthropic.com/v1/", "ANTHROPIC_API_KEY",
             examples=("claude-sonnet-5-5", "claude-haiku-5-5", "claude-opus-5-5")),
    Provider("gemini", "Google Gemini", "https://generativelanguage.googleapis.com/v1beta/openai/",
             "GEMINI_API_KEY", examples=("gemini-2.5-flash", "gemini-2.5-pro")),
    Provider("deepseek", "DeepSeek", "https://api.deepseek.com", "DEEPSEEK_API_KEY",
             examples=("deepseek-chat", "deepseek-reasoner")),
    Provider("mistral", "Mistral", "https://api.mistral.ai/v1", "MISTRAL_API_KEY",
             examples=("mistral-large-latest", "mistral-small-latest")),
    Provider("groq", "Groq", "https://api.groq.com/openai/v1", "GROQ_API_KEY",
             examples=("llama-3.3-70b-versatile",)),
    Provider("openrouter", "OpenRouter", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY",
             examples=("openai/gpt-4.1-mini", "anthropic/claude-sonnet-5-5"),
             notes="One key for models from many vendors."),
    Provider("ollama", "Ollama", "http://localhost:11434/v1", base_url_env="OLLAMA_BASE_URL",
             examples=("llama3.2", "qwen2.5:7b"), notes="Runs models on this computer."),
    Provider("lmstudio", "LM Studio", "http://localhost:1234/v1", base_url_env="LMSTUDIO_BASE_URL",
             examples=("local-model",), notes="Runs models on this computer."),
    Provider("local", "Custom (OpenAI-compatible)", "http://localhost:1234/v1", "LOCAL_API_KEY",
             key_optional=True, base_url_env="LOCAL_BASE_URL",
             examples=("local-model",), notes="Any other server that implements the OpenAI API."),
)}

# Set by the catalog for one execution, so a per-item model choice reaches the handler.
model_override: ContextVar[str | None] = ContextVar("model_override", default=None)


@dataclass(frozen=True)
class ResolvedModel:
    provider: Provider
    model: str

    @property
    def ref(self) -> str:
        return f"{self.provider.id}:{self.model}"

    @property
    def base_url(self) -> str:
        return (self.provider.base_url_env and os.getenv(self.provider.base_url_env)) or self.provider.base_url

    @property
    def api_key(self) -> str:
        # The OpenAI client rejects an empty key, even for servers that ignore it.
        return (self.provider.key_env and os.getenv(self.provider.key_env)) or "not-needed"

    @property
    def missing_key(self) -> str | None:
        p = self.provider
        if p.key_env and not p.key_optional and not os.getenv(p.key_env):
            return p.key_env
        return None


def default_model_ref() -> str:
    load_environment()
    return os.getenv("DEFAULT_MODEL") or f"openai:{default_model()}"


def parse(ref: str | None) -> ResolvedModel:
    """Turn a model reference into a provider and a bare model name."""
    load_environment()
    ref = (ref or "").strip() or default_model_ref()
    prefix, sep, rest = ref.partition(":")
    if sep and prefix in PROVIDERS and rest:
        return ResolvedModel(PROVIDERS[prefix], rest)
    fallback = default_model_ref().partition(":")[0]
    provider = PROVIDERS.get(fallback, PROVIDERS["openai"])
    return ResolvedModel(provider, ref)


def agent_model_ref(agent_id: str | None, model: str | None = None) -> tuple[str, str]:
    """Return (reference, source) for an agent, following the resolution order."""
    for ref, source in ((model, "argument"), (model_override.get(), "item")):
        if ref:
            return parse(ref).ref, source
    if agent_id:
        from app.orchestration.util import load_agent_markdown

        try:
            declared = load_agent_markdown(agent_id)["metadata"].get("model")
        except FileNotFoundError:
            declared = None
        if declared:
            return parse(str(declared)).ref, "prompt"
    return parse(None).ref, "default"


def create_agent(agent_id: str | None = None, *, model: str | None = None, **kwargs):
    """Build an agent for any provider. Accepts the same kwargs as GPTAgent.

    OpenAI uses the Responses API with native structured output. Other providers
    use Chat Completions with the JSON schema in the instructions, which works
    with any OpenAI-compatible server.
    """
    ref, _ = agent_model_ref(agent_id, model)
    resolved = parse(ref)
    if resolved.missing_key:
        raise RuntimeError(f"Missing setting: {resolved.missing_key}.")
    if resolved.provider.id == "openai":
        from app.orchestration.gpt_agent import GPTAgent

        return GPTAgent(agent_id=agent_id, model=resolved.model, **kwargs)
    from app.orchestration.gpt_agent_local import GPTLocalAgent

    return GPTLocalAgent(
        agent_id=agent_id,
        model=resolved.model,
        base_url=resolved.base_url,
        api_key=resolved.api_key,
        **kwargs,
    )


def list_models(provider_id: str) -> list[str]:
    """Ask a provider which models it serves (used by the Settings 'Test' button)."""
    from openai import OpenAI

    resolved = ResolvedModel(PROVIDERS[provider_id], "")
    if resolved.missing_key:
        raise RuntimeError(f"Missing setting: {resolved.missing_key}.")
    client = OpenAI(base_url=resolved.base_url, api_key=resolved.api_key, timeout=10, max_retries=0)
    return sorted(model.id for model in client.models.list())

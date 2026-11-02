import os

from dotenv import find_dotenv, load_dotenv


DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_SANDBOX_MODEL = "gpt-5-mini"
DEFAULT_DECISION_MODEL = "gpt-6-luna"


def load_environment() -> None:
    load_dotenv(find_dotenv())


def default_model() -> str:
    load_environment()
    return os.getenv("OPENAI_MODEL_NAME", DEFAULT_MODEL)


def sandbox_model() -> str:
    load_environment()
    return os.getenv("OPENAI_SANDBOX_MODEL_NAME", DEFAULT_SANDBOX_MODEL)


def decision_model() -> str:
    load_environment()
    return os.getenv("OPENAI_DECISION_MODEL_NAME", DEFAULT_DECISION_MODEL)

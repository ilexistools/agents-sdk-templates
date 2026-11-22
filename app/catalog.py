"""Catalog of agents and tools.

Each item lives in ``app/agents/<id>/`` or ``app/tools/<id>/`` and follows the
standard in ``docs/catalog-standards.md``: ``item.toml`` (manifest),
``handler.py`` (``Input``/``Output`` contract + ``async run``) and ``README.md``.
"""

import importlib
import inspect
import os
import sqlite3
import tomllib
from contextlib import closing
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

ROOT = Path(__file__).resolve().parent
AGENT_PROMPTS = ROOT / "assets" / "agents"
Channel = Literal["mcp", "cli", "api"]


class Example(BaseModel):
    title: str = Field(min_length=1, max_length=60)
    input: dict[str, Any]
    output: dict[str, Any] | None = None


class Item(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    type: Literal["agent", "tool"]
    title: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=1, max_length=120)
    icon: str = Field(min_length=1, max_length=4)
    category: str = Field(min_length=1, max_length=30)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    tags: list[str] = Field(default_factory=list, max_length=6)
    requires: list[str] = Field(default_factory=list)
    channels: set[Channel] = Field(min_length=1)
    examples: list[Example] = Field(min_length=1)

    @property
    def folder(self) -> Path:
        return ROOT / f"{self.type}s" / self.id

    def implementation(self):
        return importlib.import_module(f"app.{self.type}s.{self.id}.handler")

    def model(self) -> dict | None:
        """Model an agent will use: per-item override, prompt front matter or the default."""
        if self.type != "agent":
            return None
        from app.orchestration.providers import agent_model_ref, parse

        ref, source = agent_model_ref(self.id, model_choice(self.id))
        resolved = parse(ref)
        return {
            "ref": ref,
            "source": "item" if source == "argument" else source,
            "provider": resolved.provider.id,
            "provider_label": resolved.provider.label,
            "missing_key": resolved.missing_key,
        }

    def missing_requirements(self) -> list[str]:
        from app.settings import configured_value

        missing = [name for name in self.requires if not configured_value(name)]
        model = self.model()
        if model and model["missing_key"] and model["missing_key"] not in missing:
            missing.append(model["missing_key"])
        return missing


def load_item(path: Path) -> Item:
    return Item.model_validate(tomllib.loads(path.read_text(encoding="utf-8")))


def discover() -> dict[str, Item]:
    items = {}
    for kind in ("agent", "tool"):
        for path in sorted((ROOT / f"{kind}s").glob("*/item.toml")):
            item = load_item(path)
            if item.type != kind or item.id != path.parent.name or item.id in items:
                raise ValueError(f"Invalid or duplicate identity: {path}")
            items[item.id] = item
    return items


def _fields(model: type[BaseModel]) -> list[dict]:
    schema = model.model_json_schema()
    required = set(schema.get("required", []))
    return [
        {
            "name": name,
            "type": prop.get("type") or "object",
            "required": name in required,
            "description": prop.get("description", ""),
        }
        for name, prop in schema.get("properties", {}).items()
    ]


def describe(item: Item) -> dict:
    """Documentation generated from the handler contract (used by the dashboard)."""
    handler = item.implementation()
    return {
        "input": _fields(handler.Input),
        "output": _fields(handler.Output),
        "missing_requirements": item.missing_requirements(),
        "model": item.model(),
    }


def check(item: Item) -> list[str]:
    """Check that the item follows the standard. Returns the problems found."""
    problems = []
    if not (item.folder / "README.md").is_file():
        problems.append("README.md is missing from the item folder.")
    if item.type == "agent" and not (AGENT_PROMPTS / f"{item.id}.md").is_file():
        problems.append(f"Missing prompt: app/assets/agents/{item.id}.md.")
    try:
        handler = item.implementation()
    except Exception as exc:
        return problems + [f"handler.py cannot be imported ({type(exc).__name__}: {exc})."]
    for name in ("Input", "Output"):
        model = getattr(handler, name, None)
        if not (inspect.isclass(model) and issubclass(model, BaseModel)):
            problems.append(f"handler.{name} must be a Pydantic model.")
            continue
        for field, info in model.model_fields.items():
            if not info.description:
                problems.append(f"{name}.{field} has no description (use Field(description=...)).")
    if not inspect.iscoroutinefunction(getattr(handler, "run", None)):
        problems.append("handler.run must be async run(request: Input) -> Output.")
    source = (item.folder / "handler.py").read_text(encoding="utf-8")
    if item.type == "agent" and "create_agent(" not in source:
        problems.append("Agent handlers must build the agent with create_agent() so any provider works.")
    if problems:
        return problems
    for example in item.examples:
        for name, data in (("Input", example.input), ("Output", example.output)):
            if data is None:
                continue
            try:
                getattr(handler, name).model_validate(data)
            except ValidationError:
                problems.append(f"Example '{example.title}': {name.lower()} does not match {name}.")
    return problems


def connect():
    path = Path(os.environ.get("CATALOG_DB", ROOT.parent / ".catalog.sqlite3"))
    db = sqlite3.connect(path)
    try:
        db.execute("CREATE TABLE IF NOT EXISTS activation (id TEXT PRIMARY KEY, active INTEGER NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS item_channels (id TEXT PRIMARY KEY, channels TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS item_models (id TEXT PRIMARY KEY, model TEXT NOT NULL)")
    except Exception:
        db.close()
        raise
    return db


def set_active(item_id: str, active: bool):
    with closing(connect()) as db, db:
        db.execute(
            "INSERT INTO activation VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET active = excluded.active",
            (item_id, active),
        )


def activation():
    with closing(connect()) as db:
        return dict(db.execute("SELECT id, active FROM activation"))


def configured_channels(item: Item) -> set[Channel]:
    with closing(connect()) as db:
        row = db.execute("SELECT channels FROM item_channels WHERE id = ?", (item.id,)).fetchone()
    if row is None:
        return set(item.channels)
    return {channel for channel in row[0].split(",") if channel in item.channels}


def set_channels(item: Item, channels: set[Channel]) -> set[Channel]:
    if not channels <= item.channels:
        raise ValueError("Selected channels must be supported by the item.")
    value = ",".join(sorted(channels))
    with closing(connect()) as db, db:
        db.execute(
            "INSERT INTO item_channels VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET channels = excluded.channels",
            (item.id, value),
        )
    return channels


def model_choice(item_id: str) -> str | None:
    """Model reference chosen for this item in the dashboard, if any."""
    with closing(connect()) as db:
        row = db.execute("SELECT model FROM item_models WHERE id = ?", (item_id,)).fetchone()
    return row[0] if row else None


def set_model_choice(item: Item, model: str | None) -> None:
    if item.type != "agent":
        raise ValueError("Only agents use a model.")
    model = (model or "").strip()
    if len(model) > 200 or any(char in model for char in "\r\n\0"):
        raise ValueError("Invalid model reference.")
    with closing(connect()) as db, db:
        if model:
            db.execute(
                "INSERT INTO item_models VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET model = excluded.model",
                (item.id, model),
            )
        else:
            db.execute("DELETE FROM item_models WHERE id = ?", (item.id,))


def is_available(item: Item, channel: Channel) -> bool:
    return channel in configured_channels(item) and bool(activation().get(item.id, True))


class Unavailable(ValueError):
    pass


async def execute(item: Item, channel: Channel, payload: dict) -> BaseModel:
    if not is_available(item, channel):
        raise Unavailable("Item is not available on this channel.")
    from app.orchestration.providers import model_override

    handler = item.implementation()
    request = handler.Input.model_validate(payload)
    token = model_override.set(model_choice(item.id) if item.type == "agent" else None)
    try:
        return handler.Output.model_validate(await handler.run(request))
    finally:
        model_override.reset(token)

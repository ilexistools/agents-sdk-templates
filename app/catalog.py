"""Catálogo de agentes e ferramentas.

Cada item vive em ``app/agents/<id>/`` ou ``app/tools/<id>/`` e segue o padrão
descrito em ``docs/padroes-catalogo.md``: ``item.toml`` (manifesto),
``handler.py`` (contrato ``Input``/``Output`` + ``async run``) e ``README.md``.
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

    def missing_requirements(self) -> list[str]:
        from app.orchestration.config import load_environment

        load_environment()
        return [name for name in self.requires if not os.environ.get(name)]


def load_item(path: Path) -> Item:
    return Item.model_validate(tomllib.loads(path.read_text(encoding="utf-8")))


def discover() -> dict[str, Item]:
    items = {}
    for kind in ("agent", "tool"):
        for path in sorted((ROOT / f"{kind}s").glob("*/item.toml")):
            item = load_item(path)
            if item.type != kind or item.id != path.parent.name or item.id in items:
                raise ValueError(f"Identidade inválida ou duplicada: {path}")
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
    """Documentação gerada a partir do contrato do handler (usada pela interface)."""
    handler = item.implementation()
    return {
        "input": _fields(handler.Input),
        "output": _fields(handler.Output),
        "missing_requirements": item.missing_requirements(),
    }


def check(item: Item) -> list[str]:
    """Verifica se o item segue o padrão. Retorna a lista de problemas encontrados."""
    problems = []
    if not (item.folder / "README.md").is_file():
        problems.append("README.md ausente na pasta do item.")
    if item.type == "agent" and not (AGENT_PROMPTS / f"{item.id}.md").is_file():
        problems.append(f"Prompt ausente: app/assets/agents/{item.id}.md.")
    try:
        handler = item.implementation()
    except Exception as exc:
        return problems + [f"handler.py não importa ({type(exc).__name__}: {exc})."]
    for name in ("Input", "Output"):
        model = getattr(handler, name, None)
        if not (inspect.isclass(model) and issubclass(model, BaseModel)):
            problems.append(f"handler.{name} deve ser um modelo Pydantic.")
            continue
        for field, info in model.model_fields.items():
            if not info.description:
                problems.append(f"{name}.{field} sem description (use Field(description=...)).")
    if not inspect.iscoroutinefunction(getattr(handler, "run", None)):
        problems.append("handler.run deve ser uma função async run(request: Input) -> Output.")
    if problems:
        return problems
    for example in item.examples:
        for name, data in (("Input", example.input), ("Output", example.output)):
            if data is None:
                continue
            try:
                getattr(handler, name).model_validate(data)
            except ValidationError:
                problems.append(f"Exemplo '{example.title}': {name.lower()} não segue {name}.")
    return problems


def connect():
    path = Path(os.environ.get("CATALOG_DB", ROOT.parent / ".catalog.sqlite3"))
    db = sqlite3.connect(path)
    try:
        db.execute("CREATE TABLE IF NOT EXISTS activation (id TEXT PRIMARY KEY, active INTEGER NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS item_channels (id TEXT PRIMARY KEY, channels TEXT NOT NULL)")
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


def is_available(item: Item, channel: Channel) -> bool:
    return channel in configured_channels(item) and bool(activation().get(item.id, True))


class Unavailable(ValueError):
    pass


async def execute(item: Item, channel: Channel, payload: dict) -> BaseModel:
    if not is_available(item, channel):
        raise Unavailable("Item indisponível neste canal.")
    handler = item.implementation()
    request = handler.Input.model_validate(payload)
    return handler.Output.model_validate(await handler.run(request))

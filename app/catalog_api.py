import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ValidationError

from app.catalog import (
    ItemError,
    Unavailable,
    activation,
    configured_channels,
    describe,
    discover,
    execute,
    set_active,
    set_channels,
    set_model_choice,
)
from app.orchestration.providers import PROVIDERS, ResolvedModel, list_models
from app.security import settings_readonly
from app.settings import providers_status, read_settings, update_settings, validate_model_ref

router = APIRouter()
logger = logging.getLogger(__name__)


class ActivationRequest(BaseModel):
    active: bool


class ChannelsRequest(BaseModel):
    channels: set[str]


class ModelRequest(BaseModel):
    model: str | None = None


def get_item(item_id: str):
    item = discover().get(item_id)
    if item is None:
        raise HTTPException(404, "Unknown item.")
    return item


@router.get("/")
def dashboard():
    return FileResponse(Path(__file__).with_name("catalog.html"))


@router.get("/api/catalog")
def catalog():
    state = activation()
    return [
        dict(
            item.model_dump(mode="json"),
            available_channels=sorted(item.channels),
            channels=sorted(configured_channels(item)),
            active=bool(state.get(item.id, True)),
        )
        for item in discover().values()
    ]


@router.get("/api/catalog/{item_id}")
def catalog_item(item_id: str):
    """Item documentation generated from the handler's Input/Output contract."""
    item = get_item(item_id)
    try:
        details = describe(item)
    except Exception as exc:
        logger.error("Could not load %s (%s)", item.id, type(exc).__name__)
        raise HTTPException(500, "Could not load the item handler.") from exc
    return {"id": item.id, **details}


@router.patch("/api/catalog/{item_id}")
def change_status(item_id: str, request: ActivationRequest):
    item = get_item(item_id)
    set_active(item.id, request.active)
    return {"id": item.id, "active": request.active}


@router.patch("/api/catalog/{item_id}/channels")
def change_channels(item_id: str, request: ChannelsRequest):
    item = get_item(item_id)
    try:
        channels = set_channels(item, request.channels)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"id": item.id, "channels": sorted(channels)}


@router.patch("/api/catalog/{item_id}/model")
def change_model(item_id: str, request: ModelRequest):
    """Choose the model for an agent as provider:model; null restores the default."""
    item = get_item(item_id)
    try:
        if request.model:
            validate_model_ref(request.model)
        set_model_choice(item, request.model)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"id": item.id, "model": item.model()}


@router.post("/api/catalog/{item_id}/run")
async def run_item(item_id: str, payload: dict):
    item = get_item(item_id)
    try:
        return await execute(item, "api", payload)
    except Unavailable as exc:
        raise HTTPException(409, str(exc)) from exc
    except ItemError as exc:
        raise HTTPException(422, str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(422, exc.errors(include_input=False, include_context=False)) from exc
    except Exception as exc:
        logger.error("Could not run %s (%s)", item.id, type(exc).__name__)
        raise HTTPException(502, "Item execution failed.") from exc


@router.get("/api/settings")
def get_settings():
    """Model provider settings. Secret values are never returned, only a masked hint."""
    return {"readonly": settings_readonly(), "fields": read_settings()}


@router.get("/api/providers")
def get_providers():
    """Supported providers, example model references and whether each is configured."""
    return providers_status()


@router.post("/api/providers/{provider_id}/models")
def provider_models(provider_id: str):
    """Connect to the provider and list the models it serves (used to test a setup)."""
    if provider_id not in PROVIDERS:
        raise HTTPException(404, "Unknown provider.")
    try:
        models = list_models(provider_id)
    except Exception as exc:
        logger.info("Provider test failed for %s (%s)", provider_id, type(exc).__name__)
        status = getattr(exc, "status_code", None)
        base_url = ResolvedModel(PROVIDERS[provider_id], "").base_url
        if isinstance(exc, RuntimeError):
            reason = str(exc)
        elif status in (401, 403):
            reason = f"The provider rejected the API key (HTTP {status})."
        elif status:
            reason = f"The provider answered with HTTP {status}."
        else:
            reason = f"Could not connect to {base_url}. Check that the server is running and the address is right."
        raise HTTPException(502, reason) from exc
    return {"provider": provider_id, "models": [f"{provider_id}:{model}" for model in models]}


@router.put("/api/settings")
def put_settings(changes: dict[str, str | None]):
    """Update settings in .env. Send only changed keys; null or "" removes a value."""
    if settings_readonly():
        raise HTTPException(403, "Settings are read-only on this server (CATALOG_SETTINGS_READONLY).")
    try:
        return {"readonly": False, "fields": update_settings(changes)}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ValidationError

from app.catalog import (
    Unavailable,
    activation,
    configured_channels,
    describe,
    discover,
    execute,
    set_active,
    set_channels,
)
from app.settings import read_settings, update_settings

router = APIRouter()
logger = logging.getLogger(__name__)


class ActivationRequest(BaseModel):
    active: bool


class ChannelsRequest(BaseModel):
    channels: set[str]


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


@router.post("/api/catalog/{item_id}/run")
async def run_item(item_id: str, payload: dict):
    item = get_item(item_id)
    missing = item.missing_requirements()
    if missing:
        raise HTTPException(409, f"Missing setting: {', '.join(missing)}. Add it in Settings.")
    try:
        return await execute(item, "api", payload)
    except Unavailable as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(422, exc.errors(include_input=False, include_context=False)) from exc
    except Exception as exc:
        logger.error("Could not run %s (%s)", item.id, type(exc).__name__)
        raise HTTPException(502, "Item execution failed.") from exc


@router.get("/api/settings")
def get_settings():
    """Model provider settings. Secret values are never returned, only a masked hint."""
    return read_settings()


@router.put("/api/settings")
def put_settings(changes: dict[str, str | None]):
    """Update settings in .env. Send only changed keys; null or "" removes a value."""
    try:
        return update_settings(changes)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

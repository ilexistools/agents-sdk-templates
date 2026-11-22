"""Dashboard preferences stored in the catalog's SQLite database.

They are shared by everyone who uses this installation (the dashboard has no
user accounts). The browser keeps a copy of the theme and of the filters panel
state only as a cache, so the page renders in the right state before the API
answers.
"""

import json
from contextlib import closing
from typing import Any

from app.catalog import connect

THEMES = {"light", "dark", "system"}
PANEL_STATES = {"expanded", "collapsed"}
CHANNELS = {"api", "cli", "mcp"}
VIEW_FIELDS = {"q", "type", "category", "channel", "status", "item"}


def _validate(key: str, value: Any) -> Any:
    if key in {"theme", "filters_panel", "bulk_channel"} and not isinstance(value, str):
        raise ValueError(f"{key} must be text.")
    if key == "theme":
        if value not in THEMES:
            raise ValueError(f"theme must be one of: {', '.join(sorted(THEMES))}.")
    elif key == "filters_panel":
        if value not in PANEL_STATES:
            raise ValueError(f"filters_panel must be one of: {', '.join(sorted(PANEL_STATES))}.")
    elif key == "bulk_channel":
        if value not in CHANNELS:
            raise ValueError(f"bulk_channel must be one of: {', '.join(sorted(CHANNELS))}.")
    elif key == "view":
        if not isinstance(value, dict) or not set(value) <= VIEW_FIELDS:
            raise ValueError(f"view must be an object with the fields: {', '.join(sorted(VIEW_FIELDS))}.")
        if any(not isinstance(text, str) or len(text) > 200 for text in value.values()):
            raise ValueError("view fields must be text of up to 200 characters.")
        value = {field: text for field, text in value.items() if text}
    else:
        raise ValueError(f"Unknown preference: {key}.")
    return value


def get_preferences() -> dict[str, Any]:
    with closing(connect()) as db:
        return {key: json.loads(value) for key, value in db.execute("SELECT key, value FROM preferences")}


def update_preferences(changes: dict[str, Any], only_missing: bool = False) -> dict[str, Any]:
    """Merge changes into the stored preferences; a null value removes that preference.

    With only_missing, keys that already exist are left untouched (used to migrate
    values an older dashboard kept in the browser without overwriting the server's).
    """
    cleaned = {key: None if value is None else _validate(key, value) for key, value in changes.items()}
    with closing(connect()) as db, db:
        existing = {key for (key,) in db.execute("SELECT key FROM preferences")}
        for key, value in cleaned.items():
            if only_missing and key in existing:
                continue
            if value is None:
                db.execute("DELETE FROM preferences WHERE key = ?", (key,))
            else:
                db.execute(
                    "INSERT INTO preferences VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, json.dumps(value)),
                )
    return get_preferences()

"""Access protection for the dashboard and API.

Set CATALOG_TOKEN to require it on every request except GET /health.
Clients send it as ``Authorization: Bearer <token>`` or with HTTP Basic auth
(any user name, the token as password); browsers show a login prompt for Basic.

Set CATALOG_SETTINGS_READONLY=true to block changes to settings from the
dashboard and API, for deployments where keys come from the environment.
"""

import base64
import binascii
import hmac
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

PUBLIC_PATHS = {"/health"}


def configured_token() -> str:
    return os.environ.get("CATALOG_TOKEN", "").strip()


def token_configured() -> bool:
    return bool(configured_token())


def settings_readonly() -> bool:
    return os.environ.get("CATALOG_SETTINGS_READONLY", "").strip().lower() in {"1", "true", "yes", "on"}


def _presented_token(request: Request) -> str:
    header = request.headers.get("authorization", "")
    scheme, _, value = header.partition(" ")
    if scheme.lower() == "bearer":
        return value.strip()
    if scheme.lower() == "basic":
        try:
            decoded = base64.b64decode(value.strip(), validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            return ""
        return decoded.partition(":")[2]
    return ""


class TokenMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        expected = configured_token()
        if not expected or request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        presented = _presented_token(request)
        if presented and hmac.compare_digest(presented.encode(), expected.encode()):
            return await call_next(request)
        return JSONResponse(
            {"detail": "Authentication required."},
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="MCP Library", charset="UTF-8"'},
        )

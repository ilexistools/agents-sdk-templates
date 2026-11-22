"""Single entry point to run a project built from this template.

    uv run python -m app serve              # dashboard + API on http://127.0.0.1:8000
    uv run python -m app serve --host 0.0.0.0 --port 9000
    uv run python -m app mcp                # catalog MCP server (stdio)
    uv run python -m app mcp --transport streamable-http --port 8001
    uv run python -m app catalog list       # catalog CLI (list, check, new, run, ...)

Environment variables: HOST, PORT, CATALOG_TOKEN, CATALOG_SETTINGS_READONLY,
CATALOG_DB, CATALOG_ENV_FILE. See "Run and deploy" in the README.
"""

import argparse
import ipaddress
import os
import sys

LOOPBACK_NAMES = {"localhost"}


def is_loopback(host: str) -> bool:
    if host in LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def serve(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="python -m app serve", description="Run the dashboard and API.")
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    parser.add_argument("--reload", action="store_true", help="Restart on code changes (development).")
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Allow a non-local host without CATALOG_TOKEN. Only for trusted, isolated networks.",
    )
    args = parser.parse_args(argv)

    from app.orchestration.config import load_environment
    from app.security import token_configured

    load_environment()  # CATALOG_TOKEN may be defined in .env

    if not is_loopback(args.host) and not token_configured() and not args.insecure:
        parser.exit(
            2,
            f"Refusing to listen on {args.host} without CATALOG_TOKEN: the dashboard can edit API keys.\n"
            "Set CATALOG_TOKEN (see README, 'Run and deploy') or use --host 127.0.0.1.\n",
        )
    import uvicorn

    print(f"Dashboard: http://{'127.0.0.1' if args.host in ('0.0.0.0', '::') else args.host}:{args.port}/")
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload, proxy_headers=True)


def main() -> None:
    commands = {"serve", "mcp", "catalog"}
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print(__doc__.strip())
        sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 2)
    command, rest = sys.argv[1], sys.argv[2:]
    if command == "serve":
        serve(rest)
    elif command == "mcp":
        from app import catalog_mcp

        sys.argv = ["python -m app mcp", *rest]
        catalog_mcp.main()
    else:
        from app import catalog_cli

        sys.argv = ["python -m app catalog", *rest]
        catalog_cli.main()


if __name__ == "__main__":
    main()

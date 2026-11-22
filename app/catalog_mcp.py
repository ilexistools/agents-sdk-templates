import asyncio
import argparse
import json
import os

from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from pydantic import ValidationError

from app.catalog import ItemError, Unavailable, discover, execute, is_available


async def list_tools(ctx, params) -> types.ListToolsResult:
    tools = []
    for item in discover().values():
        if is_available(item, "mcp"):
            handler = item.implementation()
            tools.append(types.Tool(
                name=item.id,
                title=item.title,
                description=item.description,
                inputSchema=handler.Input.model_json_schema(),
                outputSchema=handler.Output.model_json_schema(),
            ))
    return types.ListToolsResult(tools=tools)


async def call_tool(ctx, params) -> types.CallToolResult:
    item = discover().get(params.name)
    try:
        if item is None:
            raise Unavailable("Unknown item.")
        result = await execute(item, "mcp", params.arguments or {})
    except (Unavailable, ItemError, ValidationError) as exc:
        message = "Invalid input." if isinstance(exc, ValidationError) else str(exc)
    except Exception:
        message = "Item execution failed."
    else:
        data = result.model_dump(mode="json")
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False))],
            structuredContent=data,
        )
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=message)], isError=True
    )


server = Server("MCP Library", on_list_tools=list_tools, on_call_tool=call_tool)


def _transport_security(host: str):
    """DNS-rebinding protection when serving only this computer (as the SDK does)."""
    from mcp.server.transport_security import TransportSecuritySettings

    if host in ("127.0.0.1", "localhost", "::1"):
        return TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"],
            allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"],
        )
    return None


def streamable_http_app(host: str = "127.0.0.1"):
    """Streamable HTTP app at /mcp, protected by CATALOG_TOKEN when it is set."""
    from app.security import TokenMiddleware

    app = server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        host=host,
        transport_security=_transport_security(host),
    )
    app.add_middleware(TokenMiddleware)
    return app


def sse_app(host: str = "127.0.0.1"):
    """SSE app at /sse (messages at /messages/), protected by CATALOG_TOKEN when it is set."""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.responses import Response
    from starlette.routing import Mount, Route

    from app.security import TokenMiddleware

    transport = SseServerTransport("/messages/", security_settings=_transport_security(host))

    async def handle_sse(request):
        async with transport.connect_sse(request.scope, request.receive, request._send) as (reader, writer):
            await server.run(reader, writer, server.create_initialization_options())
        return Response()

    app = Starlette(routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages/", app=transport.handle_post_message),
    ])
    app.add_middleware(TokenMiddleware)
    return app


def main():
    parser = argparse.ArgumentParser(description="Catalog MCP server.")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http", "sse"),
        default=os.getenv("MCP_TRANSPORT", "stdio"),
        help="MCP transport. Can also be set with MCP_TRANSPORT.",
    )
    parser.add_argument("--host", default=os.getenv("MCP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MCP_PORT", "8888")))
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Allow a non-local host without CATALOG_TOKEN. Only for trusted, isolated networks.",
    )
    args = parser.parse_args()
    if args.transport == "stdio":
        asyncio.run(run_stdio())
        return

    from app.__main__ import is_loopback
    from app.orchestration.config import load_environment
    from app.security import token_configured

    load_environment()
    if not is_loopback(args.host) and not token_configured() and not args.insecure:
        parser.exit(2, f"Refusing to serve MCP on {args.host} without CATALOG_TOKEN.\n")
    import uvicorn

    app = sse_app(args.host) if args.transport == "sse" else streamable_http_app(args.host)
    path = "/sse" if args.transport == "sse" else "/mcp"
    print(f"MCP ({args.transport}): http://{'127.0.0.1' if args.host in ('0.0.0.0', '::') else args.host}:{args.port}{path}")
    uvicorn.run(app, host=args.host, port=args.port)


async def run_stdio():
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())


if __name__ == "__main__":
    main()

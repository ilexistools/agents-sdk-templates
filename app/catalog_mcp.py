import asyncio
import argparse
import json
import os

from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from pydantic import ValidationError

from app.catalog import Unavailable, discover, execute, is_available


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
    except (Unavailable, ValidationError) as exc:
        message = str(exc) if isinstance(exc, Unavailable) else "Invalid input."
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


def main():
    parser = argparse.ArgumentParser(description="Catalog MCP server.")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http", "sse"),
        default=os.getenv("MCP_TRANSPORT", "stdio"),
        help="MCP transport. Can also be set with MCP_TRANSPORT.",
    )
    parser.add_argument("--host", default=os.getenv("MCP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MCP_PORT", "8001")))
    args = parser.parse_args()
    if args.transport == "stdio":
        asyncio.run(run_stdio())
    elif args.transport == "sse":
        server.run(transport="sse", host=args.host, port=args.port)
    else:
        server.run(
            transport="streamable-http",
            host=args.host,
            port=args.port,
            streamable_http_path="/mcp",
            stateless_http=True,
            json_response=True,
        )


async def run_stdio():
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())


if __name__ == "__main__":
    main()

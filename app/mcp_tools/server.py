import argparse
import os

from mcp.server.fastmcp import FastMCP

from app.mcp_tools.tools import (
    count_words,
    normalize_whitespace,
)

mcp = FastMCP(
    "Template Tools MCP",
    host="0.0.0.0",
    port=8000,
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
def count_text_words(text: str) -> dict:
    """
    Count words and characters in a text.

    Args:
        text: The input text to analyze.

    Returns:
        A dictionary with word_count and character_count.
    """
    return count_words(text)


@mcp.tool()
def clean_text_spacing(text: str) -> str:
    """
    Normalize spacing in a text.

    Args:
        text: Text with irregular whitespace.

    Returns:
        The same text with normalized spacing.
    """
    return normalize_whitespace(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the template MCP server.")
    parser.add_argument(
        "--transport",
        choices=["streamable-http", "sse", "stdio"],
        default=os.getenv("MCP_TRANSPORT", "streamable-http"),
        help="MCP transport to use. Defaults to MCP_TRANSPORT or streamable-http.",
    )
    args = parser.parse_args()

    mcp.run(transport=args.transport, mount_path="/mcp")

if __name__ == "__main__":
    main()

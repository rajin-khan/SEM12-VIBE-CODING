"""Run the GradGate MCP server over stdio (default FastMCP transport)."""

from __future__ import annotations


def main() -> None:
    from gradgate_mcp.server import mcp

    mcp.run()


if __name__ == "__main__":
    main()

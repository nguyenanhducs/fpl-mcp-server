"""FPL MCP Tools - Topic-based modules."""
# ruff: noqa: E402

from mcp.server.fastmcp import FastMCP

# Create shared MCP instance following Python naming convention: {service}_mcp
mcp = FastMCP("fpl_mcp")

from .. import (
    prompts,  # noqa: F401
    resources,  # noqa: F401
)
from . import (
    fixtures,  # noqa: F401
    gameweeks,  # noqa: F401
    leagues,  # noqa: F401
    players,  # noqa: F401
    teams,  # noqa: F401
    transfers,  # noqa: F401
)

# Re-export mcp instance
__all__ = ["mcp"]

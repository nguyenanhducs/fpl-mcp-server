"""FPL MCP Resources - Topic-based modules."""
# ruff: noqa: E402

# Import shared MCP instance from tools
from ..tools import mcp

# Import all resource modules (this registers resources with mcp)  # noqa: E402
from . import (
    bootstrap,  # noqa: F401
)

# Re-export mcp instance
__all__ = ["mcp"]

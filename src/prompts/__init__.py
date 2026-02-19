"""FPL MCP Prompts - Topic-based modules."""
# ruff: noqa: E402

# Import shared MCP instance from tools
from ..tools import mcp

# Import all prompt modules (this registers prompts with mcp)  # noqa: E402
from . import (
    captain_recommendation,  # noqa: F401
    chips,  # noqa: F401
    gameweek_analysis,  # noqa: F401
    league_analysis,  # noqa: F401
    player_analysis,  # noqa: F401
    squad_analysis,  # noqa: F401
    team_analysis,  # noqa: F401
    team_selection,  # noqa: F401
    transfers,  # noqa: F401
)

# Re-export mcp instance
__all__ = ["mcp"]

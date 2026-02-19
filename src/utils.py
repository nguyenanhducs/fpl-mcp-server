"""Shared utility functions for FPL MCP Server tools."""

from enum import Enum
import json
from typing import Any

import httpx


class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"


def handle_api_error(e: Exception) -> str:
    """
    Consistent error formatting across all tools with actionable guidance.

    Args:
        e: The exception that was raised

    Returns:
        User-friendly error message with guidance on next steps
    """
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 404:
            return (
                "Error: Resource not found. The ID or name you provided doesn't match any existing resources.\n"
                "Next steps:\n"
                "• For players: Use fpl_search_players or fpl_find_player to find the correct name\n"
                "• For teams: Use fpl_list_all_teams to see all available team names\n"
                "• For leagues: Verify the league ID from the FPL website URL (e.g., /leagues/12345/standings/)\n"
                "• For managers: Check the exact name in league standings using fpl_get_league_standings"
            )
        elif e.response.status_code == 403:
            return (
                "Error: Access denied. You don't have permission to access this resource.\n"
                "This may be because:\n"
                "• The resource is private (some leagues are private)\n"
                "• The manager has restricted access to their team\n"
                "Try accessing public leagues or teams instead."
            )
        elif e.response.status_code == 429:
            return (
                "Error: Rate limit exceeded. The FPL API has temporarily blocked too many requests.\n"
                "Next steps:\n"
                "• Wait 60 seconds before making more requests\n"
                "• Reduce the number of consecutive API calls\n"
                "• Use fpl:// resources instead of tools when possible (they're cached)"
            )
        elif e.response.status_code == 500:
            return (
                "Error: FPL API server error. The Fantasy Premier League servers are experiencing issues.\n"
                "Next steps:\n"
                "• Try again in a few minutes\n"
                "• Check if the FPL website is working: https://fantasy.premierleague.com\n"
                "• This is usually temporary during high traffic periods"
            )
        return (
            f"Error: API request failed with status {e.response.status_code}.\n"
            "Try the following:\n"
            "• Verify your input parameters are correct\n"
            "• Check the FPL API status\n"
            "• Try again in a few moments"
        )
    elif isinstance(e, httpx.TimeoutException):
        return (
            "Error: Request timed out. The FPL API is taking too long to respond.\n"
            "Next steps:\n"
            "• Try again - the API may be under heavy load\n"
            "• Use more specific filters to reduce response size\n"
            "• Check your internet connection"
        )
    elif isinstance(e, httpx.ConnectError):
        return (
            "Error: Cannot connect to FPL API. Network connection failed.\n"
            "Next steps:\n"
            "• Check your internet connection\n"
            "• Verify you can access https://fantasy.premierleague.com\n"
            "• Try again in a moment"
        )
    return f"Error: {type(e).__name__}: {str(e)}"


def check_and_truncate(
    content: str, character_limit: int, additional_message: str | None = None
) -> tuple[str, bool]:
    """
    Check if content exceeds character limit and truncate if needed.

    Args:
        content: The content to check
        character_limit: Maximum allowed characters
        additional_message: Optional message to append if truncated

    Returns:
        Tuple of (possibly truncated content, was_truncated boolean)
    """
    if len(content) <= character_limit:
        return content, False

    # Truncate to ~80% of limit to leave room for truncation message
    truncate_to = int(character_limit * 0.8)
    truncated = content[:truncate_to]

    # Add truncation notice
    truncation_msg = f"\n\n[Response truncated - exceeded {character_limit:,} character limit. "
    if additional_message:
        truncation_msg += additional_message + "]"
    else:
        truncation_msg += "Use more specific filters to reduce results.]"

    return truncated + truncation_msg, True


def create_pagination_metadata(total: int, count: int, limit: int, offset: int) -> dict[str, Any]:
    """
    Create standardized pagination metadata.

    Args:
        total: Total number of items available
        count: Number of items in current response
        limit: Maximum items requested
        offset: Current offset

    Returns:
        Dictionary with pagination metadata
    """
    has_more = total > offset + count
    next_offset = offset + count if has_more else None

    return {
        "total": total,
        "count": count,
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
        "next_offset": next_offset,
    }


def format_player_price(price_in_tenths: int) -> str:
    """Format player price from tenths to pounds."""
    return f"£{price_in_tenths / 10:.1f}m"


def format_status_indicator(status: str, news: str | None = None) -> str:
    """
    Format player status with indicators.

    Args:
        status: Player status code ('a', 'i', 'd', 'u', 's', 'n')
        news: Optional news text

    Returns:
        Formatted status string with indicators
    """
    indicator = ""
    if status != "a":
        status_map = {
            "i": "Injured",
            "d": "Doubtful",
            "u": "Unavailable",
            "s": "Suspended",
            "n": "Not in squad",
        }
        indicator = f" [{status_map.get(status, status)}]"

    if news:
        indicator += " ⚠️"

    return indicator


def format_player_status(status: str) -> str:
    """
    Format player status code to full readable name.

    Args:
        status: Player status code ('a', 'i', 'd', 'u', 's', 'n')

    Returns:
        Full status name
    """
    status_map = {
        "a": "Available",
        "i": "Injured",
        "d": "Doubtful",
        "u": "Unavailable",
        "s": "Suspended",
        "n": "Not in squad",
    }
    return status_map.get(status, status)


def format_json_response(data: Any, indent: int = 2) -> str:
    """
    Format data as JSON string with consistent formatting.

    Args:
        data: Data to format as JSON
        indent: Number of spaces for indentation

    Returns:
        JSON-formatted string
    """
    return json.dumps(data, indent=indent, ensure_ascii=False)


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    """
    Pluralize a word based on count.

    Args:
        count: Number of items
        singular: Singular form of word
        plural: Optional plural form (defaults to singular + 's')

    Returns:
        Formatted string with count and properly pluralized word
    """
    if count == 1:
        return f"{count} {singular}"
    return f"{count} {plural or singular + 's'}"

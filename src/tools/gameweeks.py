"""FPL Gameweek Tools - MCP tools for gameweek information and statistics."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from ..client import FPLClient
from ..constants import CHARACTER_LIMIT
from ..state import store
from ..utils import (
    ResponseFormat,
    check_and_truncate,
    format_json_response,
    handle_api_error,
)
from . import mcp


class GetCurrentGameweekInput(BaseModel):
    """Input model for getting current gameweek."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


async def _create_client():
    """Create an unauthenticated FPL client for public API access and ensure data is loaded."""
    client = FPLClient(store=store)
    await store.ensure_bootstrap_data(client)
    await store.ensure_fixtures_data(client)
    return client


@mcp.tool(
    name="fpl_get_current_gameweek",
    annotations={
        "title": "Get Current FPL Gameweek",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_current_gameweek(params: GetCurrentGameweekInput) -> str:
    """
    Get the current or upcoming Fantasy Premier League gameweek information.

    Returns the gameweek that is currently active (before deadline) or the next gameweek
    (after deadline). Essential for determining which gameweek to plan transfers for and
    understanding the current state of the season.

    Args:
        params (GetCurrentGameweekInput): Validated input parameters containing:
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: Current/upcoming gameweek details with deadline and status

    Examples:
        - Check current GW: response_format="markdown"
        - Get as JSON: response_format="json"

    Error Handling:
        - Returns error if gameweek data unavailable
        - Returns error if no active gameweek found
        - Returns formatted error message if API fails
    """
    try:
        await _create_client()
        if not store.bootstrap_data or not store.bootstrap_data.events:
            return "Error: Gameweek data not available. Please try again later."

        now = datetime.now(UTC)

        # First check for current gameweek (in progress or upcoming)
        for event in store.bootstrap_data.events:
            if event.is_current:
                deadline = datetime.fromisoformat(event.deadline_time.replace("Z", "+00:00"))

                if params.response_format == ResponseFormat.JSON:
                    result = {
                        "id": event.id,
                        "name": event.name,
                        "deadline_time": event.deadline_time,
                        "deadline_passed": now >= deadline,
                        "is_current": event.is_current,
                        "is_next": event.is_next,
                        "is_previous": event.is_previous,
                        "finished": event.finished,
                        "average_entry_score": event.average_entry_score,
                        "highest_score": event.highest_score,
                    }
                    return format_json_response(result)
                else:
                    if now < deadline:
                        # Deadline hasn't passed - gameweek upcoming
                        output = [
                            f"**Current Gameweek: {event.name}**",
                            f"Deadline: {event.deadline_time}",
                            "Status: Active - deadline not yet passed",
                            f"Finished: {event.finished}",
                        ]
                        if event.average_entry_score:
                            output.append(f"Average Score: {event.average_entry_score}")
                        if event.highest_score:
                            output.append(f"Highest Score: {event.highest_score}")
                    else:
                        # Deadline passed - check if finished or in progress
                        if event.finished:
                            status = "Status: Finished"
                        else:
                            status = "Status: In progress - deadline has passed"

                        output = [
                            f"**Current Gameweek: {event.name}**",
                            f"Deadline: {event.deadline_time} (passed)",
                            status,
                        ]
                        if event.average_entry_score:
                            output.append(f"Average Score: {event.average_entry_score}")
                        if event.highest_score:
                            output.append(f"Highest Score: {event.highest_score}")

                    result = "\n".join(output)
                    truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
                    return truncated

        # If no current, check for next gameweek
        for event in store.bootstrap_data.events:
            if event.is_next:
                if params.response_format == ResponseFormat.JSON:
                    result = {
                        "id": event.id,
                        "name": event.name,
                        "deadline_time": event.deadline_time,
                        "is_current": event.is_current,
                        "is_next": event.is_next,
                        "is_previous": event.is_previous,
                        "finished": event.finished,
                        "released": event.released if hasattr(event, "released") else None,
                        "can_enter": event.can_enter if hasattr(event, "can_enter") else None,
                    }
                    return format_json_response(result)
                else:
                    output = [
                        f"**Upcoming Gameweek: {event.name}**",
                        f"Deadline: {event.deadline_time}",
                        "Status: Next gameweek",
                    ]
                    if hasattr(event, "released"):
                        output.append(f"Released: {event.released}")
                    if hasattr(event, "can_enter"):
                        output.append(f"Can Enter: {event.can_enter}")

                    result = "\n".join(output)
                    truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
                    return truncated

        # Fallback: find first unfinished gameweek
        for event in store.bootstrap_data.events:
            if not event.finished:
                if params.response_format == ResponseFormat.JSON:
                    result = {
                        "id": event.id,
                        "name": event.name,
                        "deadline_time": event.deadline_time,
                        "is_current": event.is_current,
                        "is_next": event.is_next,
                        "is_previous": event.is_previous,
                        "finished": event.finished,
                        "released": event.released if hasattr(event, "released") else None,
                    }
                    return format_json_response(result)
                else:
                    output = [
                        f"**Upcoming Gameweek: {event.name}**",
                        f"Deadline: {event.deadline_time}",
                        "Status: Upcoming",
                    ]
                    if hasattr(event, "released"):
                        output.append(f"Released: {event.released}")

                    result = "\n".join(output)
                    truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
                    return truncated

        return "Error: No active or upcoming gameweek found. Season may have ended."

    except Exception as e:
        return handle_api_error(e)

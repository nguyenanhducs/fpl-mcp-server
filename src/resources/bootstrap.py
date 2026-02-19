"""
FPL MCP Resources - Bootstrap Data (Static).

Bootstrap resources expose static FPL data that rarely changes during a season.
"""

from datetime import UTC, datetime

from ..client import FPLClient
from ..constants import PlayerPosition
from ..state import store
from ..tools import mcp


def _create_client():
    """Create an unauthenticated FPL client for public API access."""
    return FPLClient(store=store)


@mcp.resource("fpl://bootstrap/players")
async def get_all_players_resource() -> str:
    """Get all FPL players with basic stats and prices."""
    client = _create_client()
    await store.ensure_bootstrap_data(client)

    if not store.bootstrap_data or not store.bootstrap_data.elements:
        return "Error: Player data not available."

    try:
        players = store.bootstrap_data.elements

        output = [f"**All FPL Players ({len(players)} total)**\n"]

        # Group by position
        positions = {
            PlayerPosition.GOALKEEPER.value: [],
            PlayerPosition.DEFENDER.value: [],
            PlayerPosition.MIDFIELDER.value: [],
            PlayerPosition.FORWARD.value: [],
        }
        for p in players:
            if p.position in positions:
                positions[p.position].append(p)

        for pos, players_list in positions.items():
            output.append(f"\n**{pos} ({len(players_list)} players):**")
            # Sort by price descending, show top 10
            sorted_players = sorted(players_list, key=lambda x: x.now_cost, reverse=True)[:10]
            for p in sorted_players:
                price = p.now_cost / 10
                news_indicator = " ⚠️" if p.news else ""
                output.append(
                    f"├─ {p.web_name:15s} ({p.team_name:15s}) | £{price:4.1f}m | "
                    f"Form: {p.form:4s} | PPG: {p.points_per_game:4s}{news_indicator}"
                )
            if len(players_list) > 10:
                output.append(f"└─ ... and {len(players_list) - 10} more")

        return "\n".join(output)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.resource("fpl://bootstrap/teams")
async def get_all_teams_resource() -> str:
    """Get all Premier League teams with strength ratings."""
    client = _create_client()
    await store.ensure_bootstrap_data(client)

    teams = store.get_all_teams()
    if not teams:
        return "Error: Team data not available."

    output = ["**Premier League Teams:**\n"]

    teams_sorted = sorted(teams, key=lambda t: t["name"])

    for team in teams_sorted:
        strength_info = ""
        if team.get("strength_overall_home") and team.get("strength_overall_away"):
            avg_strength = (team["strength_overall_home"] + team["strength_overall_away"]) / 2
            strength_info = f" | Strength: {avg_strength:.0f}"

        output.append(f"{team['name']:20s} ({team['short_name']}){strength_info}")

    return "\n".join(output)


@mcp.resource("fpl://bootstrap/gameweeks")
async def get_all_gameweeks_resource() -> str:
    """Get all gameweeks with their status for the season."""
    client = _create_client()
    await store.ensure_bootstrap_data(client)

    if not store.bootstrap_data or not store.bootstrap_data.events:
        return "Error: Gameweek data not available."

    try:
        output = ["**All Gameweeks:**\n"]

        for event in store.bootstrap_data.events:
            status = []
            if event.is_current:
                status.append("CURRENT")
            if event.is_previous:
                status.append("PREVIOUS")
            if event.is_next:
                status.append("NEXT")
            if event.finished:
                status.append("FINISHED")

            status_str = f" [{', '.join(status)}]" if status else ""
            avg_score = f" | Avg: {event.average_entry_score}" if event.average_entry_score else ""

            output.append(
                f"GW{event.id}: {event.name}{status_str} | "
                f"Deadline: {event.deadline_time[:10]}{avg_score}"
            )

        return "\n".join(output)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.resource("fpl://current-gameweek")
async def get_current_gameweek_resource() -> str:
    """Get the current or upcoming gameweek information."""
    client = _create_client()
    await store.ensure_bootstrap_data(client)

    if not store.bootstrap_data or not store.bootstrap_data.events:
        return "Error: Gameweek data not available."

    try:
        now = datetime.now(UTC)

        # First check for current gameweek (in progress or upcoming)
        for event in store.bootstrap_data.events:
            if event.is_current:
                deadline = datetime.fromisoformat(event.deadline_time.replace("Z", "+00:00"))
                if now < deadline:
                    # Deadline hasn't passed - gameweek upcoming
                    return (
                        f"**Current Gameweek: {event.name}**\n"
                        f"Deadline: {event.deadline_time}\n"
                        f"Status: Active - deadline not yet passed\n"
                        f"Finished: {event.finished}\n"
                        f"Average Score: {event.average_entry_score or 'N/A'}\n"
                        f"Highest Score: {event.highest_score or 'N/A'}"
                    )
                else:
                    # Deadline passed - check if finished or in progress
                    if event.finished:
                        status = "Status: Finished"
                    else:
                        status = "Status: In progress - deadline has passed"

                    return (
                        f"**Current Gameweek: {event.name}**\n"
                        f"Deadline: {event.deadline_time} (passed)\n"
                        f"{status}\n"
                        f"Average Score: {event.average_entry_score or 'N/A'}\n"
                        f"Highest Score: {event.highest_score or 'N/A'}"
                    )

        # If no current, check for next gameweek
        for event in store.bootstrap_data.events:
            if event.is_next:
                return (
                    f"**Upcoming Gameweek: {event.name}**\n"
                    f"Deadline: {event.deadline_time}\n"
                    f"Status: Next gameweek\n"
                    f"Released: {event.released}\n"
                    f"Can Enter: {event.can_enter}"
                )

        # Fallback: find first unfinished gameweek
        for event in store.bootstrap_data.events:
            if not event.finished:
                return (
                    f"**Upcoming Gameweek: {event.name}**\n"
                    f"Deadline: {event.deadline_time}\n"
                    f"Status: Upcoming\n"
                    f"Released: {event.released}"
                )

        return "Error: No active or upcoming gameweek found."
    except Exception as e:
        return f"Error: {str(e)}"

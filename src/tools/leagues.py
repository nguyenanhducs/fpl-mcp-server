"""FPL League Tools - MCP tools for league standings and manager analysis."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..client import FPLClient
from ..constants import CHARACTER_LIMIT
from ..formatting import format_manager_squad
from ..state import store
from ..utils import (
    ResponseFormat,
    check_and_truncate,
    format_json_response,
    handle_api_error,
)
from . import mcp


class GetLeagueStandingsInput(BaseModel):
    """Input model for getting league standings."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    league_id: int = Field(
        ...,
        description="League ID from FPL URL (e.g., for /leagues/12345/standings/ use 12345)",
        ge=1,
    )
    page: int = Field(default=1, description="Page number for pagination (default: 1)", ge=1)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class GetManagerGameweekTeamInput(BaseModel):
    """Input model for getting manager's team for a gameweek."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    manager_name: str = Field(
        ...,
        description="Manager's name or team name (e.g., 'John Smith', 'FC Warriors')",
        min_length=2,
        max_length=100,
    )
    league_id: int = Field(..., description="League ID where the manager is found", ge=1)
    gameweek: int = Field(..., description="Gameweek number (1-38)", ge=1, le=38)


class CompareManagersInput(BaseModel):
    """Input model for comparing managers."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    manager_names: list[str] = Field(
        ...,
        description="List of 2-4 manager names to compare (e.g., ['John', 'Sarah', 'Mike'])",
        min_length=2,
        max_length=4,
    )
    league_id: int = Field(..., description="League ID where managers are found", ge=1)
    gameweek: int = Field(..., description="Gameweek number to compare (1-38)", ge=1, le=38)

    @field_validator("manager_names")
    @classmethod
    def validate_manager_names(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            raise ValueError("Must provide at least 2 managers to compare")
        if len(v) > 4:
            raise ValueError("Cannot compare more than 4 managers at once")
        return v


class GetManagerSquadInput(BaseModel):
    """Input model for getting manager's squad by team ID."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    team_id: int = Field(
        ...,
        description="Manager's team ID (entry ID)",
        ge=1,
    )
    gameweek: int | None = Field(
        default=None,
        description="Gameweek number (1-38). If not provided, uses current gameweek",
        ge=1,
        le=38,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class GetManagerByTeamIdInput(BaseModel):
    """Input model for getting manager profile by team ID."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    team_id: int = Field(
        ...,
        description="Manager's team ID (entry ID)",
        ge=1,
    )
    gameweek: int | None = Field(
        default=None,
        description="Gameweek number (1-38). If not provided, uses current gameweek",
        ge=1,
        le=38,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class AnalyzeRivalInput(BaseModel):
    """Input model for analyzing a rival manager."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    my_team_id: int = Field(..., description="Your team ID", ge=1)
    rival_team_id: int = Field(..., description="Rival's team ID", ge=1)
    gameweek: int | None = Field(
        default=None,
        description="Gameweek to analyze (defaults to current)",
        ge=1,
        le=38,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


async def _create_client():
    """Create an unauthenticated FPL client for public API access and ensure data is loaded."""
    client = FPLClient(store=store)
    await store.ensure_bootstrap_data(client)
    await store.ensure_fixtures_data(client)
    return client


@mcp.tool(
    name="fpl_get_league_standings",
    annotations={
        "title": "Get FPL League Standings",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_league_standings(params: GetLeagueStandingsInput) -> str:
    """
    Get standings for a specific Fantasy Premier League league.

    Returns manager rankings, points, team names, and rank changes within the league.
    Supports pagination for large leagues. Find league ID in the FPL website URL
    (e.g., for /leagues/12345/standings/ use league_id=12345).

    Args:
        params (GetLeagueStandingsInput): Validated input parameters containing:
            - league_id (int): League ID from FPL URL
            - page (int): Page number for pagination (default: 1)
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: League standings with rankings and pagination info

    Examples:
        - View league: league_id=12345
        - Next page: league_id=12345, page=2
        - Get as JSON: league_id=12345, response_format="json"

    Error Handling:
        - Returns error if league not found
        - Returns error if page number invalid
        - Returns formatted error message if API fails
    """
    try:
        client = await _create_client()
        standings_data = await client.get_league_standings(
            league_id=params.league_id, page_standings=params.page
        )

        league_data = standings_data.get("league", {})
        standings = standings_data.get("standings", {})
        results = standings.get("results", [])

        if not results:
            return f"No standings found for league ID {params.league_id}. The league may not exist or you may not have access."

        if params.response_format == ResponseFormat.JSON:
            result = {
                "league": {
                    "id": params.league_id,
                    "name": league_data.get("name", f"League {params.league_id}"),
                },
                "pagination": {
                    "page": params.page,
                    "has_next": standings.get("has_next", False),
                },
                "standings": [
                    {
                        "rank": entry["rank"],
                        "last_rank": entry["last_rank"],
                        "rank_change": entry["rank"] - entry["last_rank"],
                        "team_id": entry["entry"],
                        "entry_name": entry["entry_name"],
                        "player_name": entry["player_name"],
                        "gameweek_points": entry["event_total"],
                        "total_points": entry["total"],
                    }
                    for entry in results
                ],
            }
            return format_json_response(result)
        else:
            output = [
                f"**{league_data.get('name', f'League {params.league_id}')}**",
                f"Page: {params.page}",
                "",
                "**Standings:**",
                "",
            ]

            for entry in results:
                rank_change = entry["rank"] - entry["last_rank"]
                rank_indicator = "↑" if rank_change < 0 else "↓" if rank_change > 0 else "="

                output.append(
                    f"{entry['rank']:3d}. {rank_indicator} {entry['entry_name']:30s} | "
                    f"{entry['player_name']:20s} | "
                    f"Team ID: {entry['entry']:7d} | "
                    f"GW: {entry['event_total']:3d} | Total: {entry['total']:4d}"
                )

            if standings.get("has_next"):
                output.append(
                    f"\n📄 More entries available. Use page={params.page + 1} to see the next page."
                )

            result = "\n".join(output)
            truncated, _ = check_and_truncate(
                result, CHARACTER_LIMIT, f"Use page={params.page + 1} for more results"
            )
            return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_get_manager_gameweek_team",
    annotations={
        "title": "Get Manager's FPL Gameweek Team",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_manager_gameweek_team(params: GetManagerGameweekTeamInput) -> str:
    """
    Get a manager's team selection for a specific gameweek.

    Shows the 15 players picked, captain/vice-captain choices, formation, points scored,
    transfers made, and automatic substitutions. Find manager by their name or team name
    within a specific league.

    Args:
        params (GetManagerGameweekTeamInput): Validated input parameters containing:
            - manager_name (str): Manager's name or team name
            - league_id (int): League ID where manager is found
            - gameweek (int): Gameweek number (1-38)

    Returns:
        str: Complete team sheet with starting XI, bench, and statistics

    Examples:
        - View team: manager_name="John Smith", league_id=12345, gameweek=13
        - Check transfers: manager_name="FC Warriors", league_id=12345, gameweek=15

    Error Handling:
        - Returns error if manager not found in league
        - Returns helpful message suggesting correct name if ambiguous
        - Returns formatted error message if API fails
    """
    try:
        client = await _create_client()

        # Find manager in league
        manager_info = await store.find_manager_by_name(
            client, params.league_id, params.manager_name
        )
        if not manager_info:
            return f"Could not find manager '{params.manager_name}' in league ID {params.league_id}. Try using the exact name from the league standings."

        manager_team_id = manager_info["entry"]

        # Fetch gameweek picks from API
        picks_data = await client.get_manager_gameweek_picks(manager_team_id, params.gameweek)

        picks = picks_data.get("picks", [])
        entry_history = picks_data.get("entry_history", {})
        auto_subs = picks_data.get("automatic_subs", [])

        if not picks:
            return f"No team data found for {manager_info['player_name']} in gameweek {params.gameweek}. The gameweek may not have started yet."

        # Rehydrate player names
        element_ids = [pick["element"] for pick in picks]
        players_info = store.rehydrate_player_names(element_ids)

        result = format_manager_squad(
            team_name=manager_info["entry_name"],
            player_name=manager_info["player_name"],
            team_id=manager_team_id,
            gameweek=params.gameweek,
            entry_history=entry_history,
            picks=picks,
            players_info=players_info,
            active_chip=picks_data.get("active_chip"),
        )

        if auto_subs:
            result += "\n\n**Automatic Substitutions:**"
            for sub in auto_subs:
                player_out = store.get_player_name(sub["element_out"])
                player_in = store.get_player_name(sub["element_in"])
                result += f"\n├─ {player_out} → {player_in}"

        truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
        return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_compare_managers",
    annotations={
        "title": "Compare FPL Managers",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_compare_managers(params: CompareManagersInput) -> str:
    """
    Compare multiple managers' teams for a specific gameweek side-by-side.

    Shows differences in player selection, captaincy choices, points scored, common
    players, and unique differentials. Useful for mini-league rivalry analysis and
    understanding what sets top managers apart.

    Args:
        params (CompareManagersInput): Validated input parameters containing:
            - manager_names (list[str]): 2-4 manager names to compare
            - league_id (int): League ID where managers are found
            - gameweek (int): Gameweek number to compare (1-38)

    Returns:
        str: Side-by-side manager comparison with differentials

    Examples:
        - Compare 2 managers: manager_names=["John", "Sarah"], league_id=12345, gameweek=13
        - Compare 4 managers: manager_names=["A", "B", "C", "D"], league_id=12345, gameweek=10

    Error Handling:
        - Returns error if fewer than 2 or more than 4 managers provided
        - Returns error if any manager not found (with helpful message)
        - Returns formatted error message if API fails
    """
    try:
        client = await _create_client()

        # Find all managers
        manager_ids = []
        manager_infos = []
        for name in params.manager_names:
            manager_info = await store.find_manager_by_name(client, params.league_id, name)
            if not manager_info:
                return f"Could not find manager '{name}' in league ID {params.league_id}. Try using the exact name from league standings."
            manager_ids.append(manager_info["entry"])
            manager_infos.append(manager_info)

        # Fetch all teams
        teams_data = []
        for team_id in manager_ids:
            picks_data = await client.get_manager_gameweek_picks(team_id, params.gameweek)
            teams_data.append((team_id, picks_data))

        output = [f"**Manager Comparison - Gameweek {params.gameweek}**\n"]

        # Performance summary
        output.append("**Performance Summary:**")
        for i, (_team_id, data) in enumerate(teams_data):
            entry_history = data.get("entry_history", {})
            manager_info = manager_infos[i]
            output.append(
                f"├─ {manager_info['player_name']} ({manager_info['entry_name']}): "
                f"{entry_history.get('points', 0)}pts | "
                f"Rank: {entry_history.get('overall_rank', 'N/A'):,} | "
                f"Transfers: {entry_history.get('event_transfers', 0)} "
                f"(-{entry_history.get('event_transfers_cost', 0)}pts)"
            )

        # Captain choices
        output.append("\n**Captain Choices:**")
        for i, (_team_id, data) in enumerate(teams_data):
            picks = data.get("picks", [])
            captain_pick = next((p for p in picks if p["is_captain"]), None)
            if captain_pick:
                captain_name = store.get_player_name(captain_pick["element"])
                multiplier = captain_pick.get("multiplier", 2)
                manager_info = manager_infos[i]
                output.append(f"├─ {manager_info['player_name']}: {captain_name} (x{multiplier})")

        # Find common and unique players
        all_players = {}
        for _i, (team_id, data) in enumerate(teams_data):
            picks = data.get("picks", [])
            starting_xi = [p["element"] for p in picks if p["position"] <= 11]
            all_players[team_id] = set(starting_xi)

        common_players = set.intersection(*all_players.values()) if len(all_players) > 1 else set()

        if common_players:
            output.append(f"\n**Common Players ({len(common_players)}):**")
            for element_id in list(common_players)[:10]:
                player_name = store.get_player_name(element_id)
                output.append(f"├─ {player_name}")

        # Unique players per team (differentials)
        output.append("\n**Unique Selections (Differentials):**")
        for i, team_id in enumerate(manager_ids):
            other_teams = [t for t in manager_ids if t != team_id]
            other_players = set()
            for other_id in other_teams:
                other_players.update(all_players.get(other_id, set()))

            unique = all_players[team_id] - other_players
            if unique:
                manager_info = manager_infos[i]
                output.append(f"\n{manager_info['player_name']} only:")
                for element_id in list(unique)[:5]:
                    player_name = store.get_player_name(element_id)
                    output.append(f"├─ {player_name}")

        result = "\n".join(output)
        truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
        return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_get_manager_squad",
    annotations={
        "title": "Get Manager's FPL Squad by Team ID",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_manager_squad(params: GetManagerSquadInput) -> str:
    """
    Get a manager's squad selection for a specific gameweek using their team ID.

    Shows the 15 players picked, captain/vice-captain choices, formation, points scored,
    transfers made, and automatic substitutions. This is a simpler alternative to
    fpl_get_manager_gameweek_team that uses team ID directly instead of requiring
    manager name and league ID lookup.

    Args:
        params (GetManagerSquadInput): Validated input parameters containing:
            - team_id (int): Manager's team ID (entry ID)
            - gameweek (int | None): Gameweek number (1-38), defaults to current GW
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: Complete team sheet with starting XI, bench, and statistics

    Examples:
        - View current team: team_id=123456
        - View specific gameweek: team_id=123456, gameweek=13
        - Get as JSON: team_id=123456, gameweek=15, response_format="json"

    Error Handling:
        - Returns error if team ID not found
        - Returns error if gameweek not started yet
        - Returns formatted error message if API fails
    """
    try:
        client = await _create_client()

        # Fetch manager entry to get team name
        entry_data = await client.get_manager_entry(params.team_id)
        team_name = entry_data.get("name", "Unknown Team")
        player_name = f"{entry_data.get('player_first_name', '')} {entry_data.get('player_last_name', '')}".strip()

        # Determine which gameweek to use
        gameweek = params.gameweek
        if gameweek is None:
            current_gw = store.get_current_gameweek()
            if not current_gw:
                return (
                    "Error: Could not determine current gameweek. Please specify a gameweek number."
                )
            gameweek = current_gw.id

        # Fetch gameweek picks from API
        picks_data = await client.get_manager_gameweek_picks(params.team_id, gameweek)

        picks = picks_data.get("picks", [])
        entry_history = picks_data.get("entry_history", {})
        auto_subs = picks_data.get("automatic_subs", [])

        if not picks:
            return f"No team data found for team ID {params.team_id} in gameweek {gameweek}. The gameweek may not have started yet or the team ID may be invalid."

        # Rehydrate player names
        element_ids = [pick["element"] for pick in picks]
        players_info = store.rehydrate_player_names(element_ids)

        if params.response_format == ResponseFormat.JSON:
            starting_xi = [p for p in picks if p["position"] <= 11]
            bench = [p for p in picks if p["position"] > 11]

            result = {
                "team_id": params.team_id,
                "team_name": team_name,
                "player_name": player_name,
                "gameweek": gameweek,
                "stats": {
                    "points": entry_history.get("points", 0),
                    "total_points": entry_history.get("total_points", 0),
                    "overall_rank": entry_history.get("overall_rank"),
                    "team_value": entry_history.get("value", 0) / 10,
                    "bank": entry_history.get("bank", 0) / 10,
                    "transfers": entry_history.get("event_transfers", 0),
                    "transfer_cost": entry_history.get("event_transfers_cost", 0),
                    "points_on_bench": entry_history.get("points_on_bench", 0),
                },
                "active_chip": picks_data.get("active_chip"),
                "starting_xi": [
                    {
                        "position": pick["position"],
                        "player_name": players_info.get(pick["element"], {}).get(
                            "web_name", "Unknown"
                        ),
                        "team": players_info.get(pick["element"], {}).get("team", "UNK"),
                        "player_position": players_info.get(pick["element"], {}).get(
                            "position", "UNK"
                        ),
                        "price": players_info.get(pick["element"], {}).get("price", 0),
                        "is_captain": pick["is_captain"],
                        "is_vice_captain": pick["is_vice_captain"],
                        "multiplier": pick["multiplier"],
                    }
                    for pick in starting_xi
                ],
                "bench": [
                    {
                        "position": pick["position"],
                        "player_name": players_info.get(pick["element"], {}).get(
                            "web_name", "Unknown"
                        ),
                        "team": players_info.get(pick["element"], {}).get("team", "UNK"),
                        "player_position": players_info.get(pick["element"], {}).get(
                            "position", "UNK"
                        ),
                        "price": players_info.get(pick["element"], {}).get("price", 0),
                    }
                    for pick in bench
                ],
                "automatic_subs": [
                    {
                        "player_out": store.get_player_name(sub["element_out"]),
                        "player_in": store.get_player_name(sub["element_in"]),
                    }
                    for sub in auto_subs
                ],
            }
            return format_json_response(result)
        else:
            result = format_manager_squad(
                team_name=team_name,
                player_name=player_name,
                team_id=params.team_id,
                gameweek=gameweek,
                entry_history=entry_history,
                picks=picks,
                players_info=players_info,
                active_chip=picks_data.get("active_chip"),
            )

            if auto_subs:
                result += "\n\n**Automatic Substitutions:**"
                for sub in auto_subs:
                    player_out = store.get_player_name(sub["element_out"])
                    player_in = store.get_player_name(sub["element_in"])
                    result += f"\n├─ {player_out} → {player_in}"

            truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
            return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_get_manager_by_team_id",
    annotations={
        "title": "Get Manager Profile by Team ID",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_manager_by_team_id(params: GetManagerByTeamIdInput) -> str:
    """
    Get manager profile and squad information using team ID directly.

    This tool provides the same functionality as fpl_get_manager_squad but with
    a name that better reflects its purpose - getting manager information without
    requiring league context. Shows the 15 players picked, captain/vice-captain
    choices, formation, points scored, transfers made, and automatic substitutions.

    Args:
        params (GetManagerByTeamIdInput): Validated input parameters containing:
            - team_id (int): Manager's team ID (entry ID)
            - gameweek (int | None): Gameweek number (1-38), defaults to current GW
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: Complete manager profile with squad, statistics, and team info

    Examples:
        - View current squad: team_id=123456
        - View specific gameweek: team_id=123456, gameweek=20
        - Get as JSON: team_id=123456, response_format="json"

    Error Handling:
        - Returns error if team ID not found (404)
        - Returns error if gameweek not started yet
        - Returns formatted error message if API fails
    """
    try:
        client = await _create_client()

        # Fetch manager entry to get team name and player name
        try:
            entry_data = await client.get_manager_entry(params.team_id)
        except Exception:
            return (
                f"Manager with team ID {params.team_id} not found. Verify the team ID is correct."
            )

        team_name = entry_data.get("name", "Unknown Team")
        player_name = f"{entry_data.get('player_first_name', '')} {entry_data.get('player_last_name', '')}".strip()

        # Determine which gameweek to use
        gameweek = params.gameweek
        if gameweek is None:
            current_gw = store.get_current_gameweek()
            if not current_gw:
                return (
                    "Error: Could not determine current gameweek. Please specify a gameweek number."
                )
            gameweek = current_gw.id

        # Fetch gameweek picks from API
        picks_data = await client.get_manager_gameweek_picks(params.team_id, gameweek)

        picks = picks_data.get("picks", [])
        entry_history = picks_data.get("entry_history", {})
        auto_subs = picks_data.get("automatic_subs", [])

        if not picks:
            return f"No team data found for team ID {params.team_id} in gameweek {gameweek}. Gameweek {gameweek} may not have started yet. Please choose an earlier gameweek or wait until GW{gameweek} begins."

        # Rehydrate player names
        element_ids = [pick["element"] for pick in picks]
        players_info = store.rehydrate_player_names(element_ids)

        if params.response_format == ResponseFormat.JSON:
            starting_xi = [p for p in picks if p["position"] <= 11]
            bench = [p for p in picks if p["position"] > 11]

            result = {
                "team_id": params.team_id,
                "team_name": team_name,
                "player_name": player_name,
                "gameweek": gameweek,
                "stats": {
                    "points": entry_history.get("points", 0),
                    "total_points": entry_history.get("total_points", 0),
                    "overall_rank": entry_history.get("overall_rank"),
                    "team_value": entry_history.get("value", 0) / 10,
                    "bank": entry_history.get("bank", 0) / 10,
                    "transfers": entry_history.get("event_transfers", 0),
                    "transfer_cost": entry_history.get("event_transfers_cost", 0),
                    "points_on_bench": entry_history.get("points_on_bench", 0),
                },
                "active_chip": picks_data.get("active_chip"),
                "starting_xi": [
                    {
                        "position": pick["position"],
                        "player_name": players_info.get(pick["element"], {}).get(
                            "web_name", "Unknown"
                        ),
                        "team": players_info.get(pick["element"], {}).get("team", "UNK"),
                        "player_position": players_info.get(pick["element"], {}).get(
                            "position", "UNK"
                        ),
                        "price": players_info.get(pick["element"], {}).get("price", 0),
                        "is_captain": pick["is_captain"],
                        "is_vice_captain": pick["is_vice_captain"],
                        "multiplier": pick["multiplier"],
                    }
                    for pick in starting_xi
                ],
                "bench": [
                    {
                        "position": pick["position"],
                        "player_name": players_info.get(pick["element"], {}).get(
                            "web_name", "Unknown"
                        ),
                        "team": players_info.get(pick["element"], {}).get("team", "UNK"),
                        "player_position": players_info.get(pick["element"], {}).get(
                            "position", "UNK"
                        ),
                        "price": players_info.get(pick["element"], {}).get("price", 0),
                    }
                    for pick in bench
                ],
                "automatic_subs": [
                    {
                        "player_out": store.get_player_name(sub["element_out"]),
                        "player_in": store.get_player_name(sub["element_in"]),
                    }
                    for sub in auto_subs
                ],
            }
            return format_json_response(result)
        else:
            result = format_manager_squad(
                team_name=team_name,
                player_name=player_name,
                team_id=params.team_id,
                gameweek=gameweek,
                entry_history=entry_history,
                picks=picks,
                players_info=players_info,
                active_chip=picks_data.get("active_chip"),
            )

            if auto_subs:
                result += "\n\n**Automatic Substitutions:**"
                for sub in auto_subs:
                    player_out = store.get_player_name(sub["element_out"])
                    player_in = store.get_player_name(sub["element_in"])
                    result += f"\n├─ {player_out} → {player_in}"

            truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
            return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_analyze_rival",
    annotations={
        "title": "Analyze FPL Rival",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_analyze_rival(params: AnalyzeRivalInput) -> str:
    """
    Compare your team against a specific rival manager.

    Provides a comprehensive head-to-head analysis including:
    - Points and Rank comparison
    - Chip usage history
    - Captaincy comparison
    - Key Differentials (players they own that you don't)

    Args:
        params (AnalyzeRivalInput): Validated input parameters containing:
            - my_team_id (int): Your team ID
            - rival_team_id (int): Rival's team ID
            - gameweek (int | None): Gameweek number (defaults to current)

    Returns:
        str: Detailed rival analysis and threat assessment

    Examples:
        - Compare me vs rival: my_team_id=123, rival_team_id=456
        - Analyze past GW: my_team_id=123, rival_team_id=456, gameweek=10

    Error Handling:
        - Returns error if either team ID invalid
        - Returns formatted error message if API fails
    """
    try:
        client = await _create_client()

        # Determine gameweek
        gameweek = params.gameweek
        if not gameweek:
            current = store.get_current_gameweek()
            if not current:
                return "Error: Could not determine current gameweek."
            gameweek = current.id

        # Fetch data for both managers
        try:
            my_entry = await client.get_manager_entry(params.my_team_id)
            rival_entry = await client.get_manager_entry(params.rival_team_id)
        except Exception:
            return "Error: Could not retrieve manager details. Check Team IDs."

        my_picks_data = await client.get_manager_gameweek_picks(params.my_team_id, gameweek)
        rival_picks_data = await client.get_manager_gameweek_picks(params.rival_team_id, gameweek)

        my_name = f"{my_entry.get('player_first_name')} {my_entry.get('player_last_name')}"
        rival_name = f"{rival_entry.get('player_first_name')} {rival_entry.get('player_last_name')}"

        my_team_name = my_entry.get("name")
        rival_team_name = rival_entry.get("name")

        # Extract picks (Starting XI + Bench)
        my_picks = my_picks_data.get("picks", [])
        rival_picks = rival_picks_data.get("picks", [])

        # Helper to get active players (Starting XI - first 11)
        # Note: Position 1-11 are starters, 12-15 bench
        my_starters = {p["element"] for p in my_picks if p["position"] <= 11}
        rival_starters = {p["element"] for p in rival_picks if p["position"] <= 11}

        # Differentials (My unique vs Rival unique)
        my_unique = my_starters - rival_starters
        rival_unique = rival_starters - my_starters
        common = my_starters & rival_starters

        # Captains
        my_cap = next((p for p in my_picks if p["is_captain"]), None)
        rival_cap = next((p for p in rival_picks if p["is_captain"]), None)

        my_cap_name = store.get_player_name(my_cap["element"]) if my_cap else "None"
        rival_cap_name = store.get_player_name(rival_cap["element"]) if rival_cap else "None"

        # Stats
        my_history = my_picks_data.get("entry_history", {})
        rival_history = rival_picks_data.get("entry_history", {})

        if params.response_format == ResponseFormat.JSON:
            result = {
                "gameweek": gameweek,
                "managers": {
                    "me": {
                        "name": my_name,
                        "team": my_team_name,
                        "points": my_history.get("points"),
                        "rank": my_history.get("overall_rank"),
                    },
                    "rival": {
                        "name": rival_name,
                        "team": rival_team_name,
                        "points": rival_history.get("points"),
                        "rank": rival_history.get("overall_rank"),
                    },
                },
                "comparison": {
                    "common_players_count": len(common),
                    "differentials_count": len(rival_unique),
                    "points_diff": my_history.get("points", 0) - rival_history.get("points", 0),
                },
                "captains": {"me": my_cap_name, "rival": rival_cap_name},
                "rival_differentials": [store.get_player_name(pid) for pid in rival_unique],
            }
            return format_json_response(result)

        # Markdown Output
        output = [
            f"## Rival Analysis: {my_name} vs {rival_name}",
            f"**Gameweek {gameweek}**",
            "",
            "### 🏆 Performance & Rank",
            f"| Metric | 👤 You ({my_team_name}) | 🆚 Rival ({rival_team_name}) | Diff |",
            "| :--- | :--- | :--- | :--- |",
            f"| **GW Points** | {my_history.get('points', 0)} | {rival_history.get('points', 0)} | {my_history.get('points', 0) - rival_history.get('points', 0):+d} |",
            f"| **Total Pts** | {my_history.get('total_points', 0)} | {rival_history.get('total_points', 0)} | {my_history.get('total_points', 0) - rival_history.get('total_points', 0):+d} |",
            f"| **Rank** | {my_history.get('overall_rank', 0):,} | {rival_history.get('overall_rank', 0):,} | --- |",
            f"| **Captain** | {my_cap_name} | {rival_cap_name} | {'✅ Same' if my_cap['element'] == rival_cap['element'] else '⚠️ Diff'} |",
            f"| **Chip** | {my_picks_data.get('active_chip') or 'None'} | {rival_picks_data.get('active_chip') or 'None'} | --- |",
            "",
            "### ⚠️ Threat Assessment (Differentials)",
            "Players in their starting XI that you DO NOT have:",
            "",
        ]

        if rival_unique:
            for pid in rival_unique:
                p_name = store.get_player_name(pid)
                # Get live points if possible
                p_data = next((p for p in store.bootstrap_data.elements if p.id == pid), None)
                points = p_data.event_points if p_data else "?"
                output.append(f"- **{p_name}** ({points} pts)")
        else:
            output.append("No starting XI differentials! You have a full template match.")

        output.append("")
        output.append("### 🛡️ Your Advantages")
        output.append("Players you have that they don't:")

        if my_unique:
            for pid in my_unique:
                p_name = store.get_player_name(pid)
                p_data = next((p for p in store.bootstrap_data.elements if p.id == pid), None)
                points = p_data.event_points if p_data else "?"
                output.append(f"- **{p_name}** ({points} pts)")
        else:
            output.append("No unique players.")

        return "\n".join(output)

    except Exception as e:
        return handle_api_error(e)

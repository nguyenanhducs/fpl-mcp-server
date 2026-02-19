"""FPL Player Tools - MCP tools for player search, analysis, and comparison."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..client import FPLClient
from ..constants import CHARACTER_LIMIT
from ..formatting import format_player_details
from ..state import store
from ..utils import (
    ResponseFormat,
    check_and_truncate,
    format_json_response,
    format_player_price,
    format_player_status,
    format_status_indicator,
    handle_api_error,
)
from . import mcp


class FindPlayerInput(BaseModel):
    """Input for finding a player with fuzzy matching."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    player_name: str = Field(
        ...,
        description="Player name with fuzzy matching support (e.g., 'Haalnd' will match 'Haaland')",
        min_length=2,
        max_length=100,
    )


class GetPlayerDetailsInput(BaseModel):
    """Input model for getting player details."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    player_name: str = Field(
        ...,
        description="Player name (e.g., 'Mohamed Salah', 'Erling Haaland')",
        min_length=2,
        max_length=100,
    )


class ComparePlayersInput(BaseModel):
    """Input model for comparing multiple players."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    player_names: list[str] = Field(
        ...,
        description="List of 2-5 player names to compare (e.g., ['Salah', 'Saka', 'Palmer'])",
        min_length=2,
        max_length=5,
    )

    @field_validator("player_names")
    @classmethod
    def validate_player_names(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            raise ValueError("Must provide at least 2 players to compare")
        if len(v) > 5:
            raise ValueError("Cannot compare more than 5 players at once")
        return v


class GetTopPlayersByMetricInput(BaseModel):
    """Input model for getting top players by various metrics over last N gameweeks."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    num_gameweeks: int = Field(
        default=5,
        description="Number of recent gameweeks to analyze (1-10)",
        ge=1,
        le=10,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class GetCaptainRecommendationsInput(BaseModel):
    """Input model for captain recommendations."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    team_id: int | None = Field(
        default=None, description="Your team ID (to analyze your specific squad)"
    )
    gameweek: int | None = Field(default=None, description="Gameweek to analyze (defaults to next)")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


async def _create_client():
    """Create an unauthenticated FPL client for public API access and ensure data is loaded."""
    client = FPLClient(store=store)
    # Ensure bootstrap data is loaded
    await store.ensure_bootstrap_data(client)
    # Ensure fixtures data is loaded
    await store.ensure_fixtures_data(client)
    return client


async def _aggregate_player_stats_from_fixtures(client: FPLClient, num_gameweeks: int) -> dict:
    """
    Aggregate player statistics from finished fixtures over the last N gameweeks.

    Args:
        client: FPL client instance
        num_gameweeks: Number of recent gameweeks to analyze

    Returns:
        Dictionary with aggregated stats by metric and player info
    """
    import asyncio
    from collections import defaultdict

    # Get current gameweek
    current_gw = store.get_current_gameweek()
    if not current_gw:
        return {}

    current_gw_id = current_gw.id

    # Determine gameweek range
    start_gw = max(1, current_gw_id - num_gameweeks)
    end_gw = current_gw_id - 1  # Only include finished gameweeks

    # Filter fixtures to the target gameweek range and finished status
    if not store.fixtures_data:
        return {}

    target_fixtures = [
        f
        for f in store.fixtures_data
        if f.event is not None and start_gw <= f.event <= end_gw and f.finished
    ]

    if not target_fixtures:
        return {
            "gameweek_range": f"GW {start_gw}-{end_gw}",
            "fixtures_analyzed": 0,
            "error": "No finished fixtures found in the specified gameweek range",
        }

    # Aggregate stats by player
    player_stats = defaultdict(
        lambda: {
            "goals_scored": 0,
            "assists": 0,
            "expected_goals": 0.0,
            "expected_assists": 0.0,
            "expected_goal_involvements": 0.0,
            "defensive_contribution": 0,
            "matches_played": 0,
        }
    )

    # Fetch fixture stats concurrently (with a reasonable limit to avoid overwhelming the API)
    async def fetch_fixture_stats(fixture_id: int):
        try:
            return await client.get_fixture_stats(fixture_id)
        except Exception:
            # Silently skip fixtures that fail to fetch
            return None

    # Fetch fixture stats in batches of 10 to avoid overwhelming the API
    batch_size = 10
    fixture_ids = [f.id for f in target_fixtures]

    for i in range(0, len(fixture_ids), batch_size):
        batch = fixture_ids[i : i + batch_size]
        results = await asyncio.gather(
            *[fetch_fixture_stats(fid) for fid in batch], return_exceptions=True
        )

        for fixture_stats in results:
            if fixture_stats and isinstance(fixture_stats, dict):
                # Process both home ('h') and away ('a') players
                for team_key in ["h", "a"]:
                    for player_stat in fixture_stats.get(team_key, []):
                        element_id = player_stat.get("element")
                        if not element_id or player_stat.get("minutes", 0) == 0:
                            continue

                        stats = player_stats[element_id]
                        stats["goals_scored"] += player_stat.get("goals_scored", 0)
                        stats["assists"] += player_stat.get("assists", 0)
                        stats["expected_goals"] += float(player_stat.get("expected_goals", "0.0"))
                        stats["expected_assists"] += float(
                            player_stat.get("expected_assists", "0.0")
                        )
                        stats["expected_goal_involvements"] += float(
                            player_stat.get("expected_goal_involvements", "0.0")
                        )
                        stats["defensive_contribution"] += player_stat.get(
                            "defensive_contribution", 0
                        )
                        if player_stat.get("minutes", 0) > 0:
                            stats["matches_played"] += 1

    # Enrich with player details and sort by each metric
    metrics = {
        "goals_scored": [],
        "expected_goals": [],
        "assists": [],
        "expected_assists": [],
        "expected_goal_involvements": [],
        "defensive_contribution": [],
    }

    for element_id, stats in player_stats.items():
        player = store.get_player_by_id(element_id)
        if not player:
            continue

        player_data = {
            "element_id": element_id,
            "name": player.web_name,
            "full_name": f"{player.first_name} {player.second_name}",
            "team": player.team_name,
            "position": player.position,
            "matches_played": stats["matches_played"],
        }

        # Add to each metric list with the stat value
        for metric in metrics:
            metric_value = stats[metric]
            if metric_value > 0:  # Only include players with non-zero stats
                metrics[metric].append({**player_data, "value": metric_value})

    # Sort each metric list by value (descending) and take top 10
    for metric in metrics:
        metrics[metric] = sorted(metrics[metric], key=lambda x: x["value"], reverse=True)[:10]

    return {
        "gameweek_range": f"GW {start_gw}-{end_gw}",
        "fixtures_analyzed": len(target_fixtures),
        "metrics": metrics,
    }


@mcp.tool(
    name="fpl_find_player",
    annotations={
        "title": "Find FPL Player with Fuzzy Matching",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_find_player(params: FindPlayerInput) -> str:
    """
    Find a Fantasy Premier League player by name with intelligent fuzzy matching.

    Handles variations in spelling, partial names, and common nicknames. If multiple
    players match, returns disambiguation options. More forgiving than exact search.

    Args:
        params (FindPlayerInput): Validated input parameters containing:
            - player_name (str): Player name with fuzzy support (e.g., 'Haalnd' matches 'Haaland')

    Returns:
        str: Player details if unique match, or list of matching players if ambiguous

    Examples:
        - Find with typo: player_name="Haalnd" (finds Haaland)
        - Partial name: player_name="Mo Salah" (finds Mohamed Salah)
        - Surname only: player_name="Son" (finds Son Heung-min)

    Error Handling:
        - Returns helpful message if no players found
        - Returns disambiguation list if multiple matches
        - Returns formatted error message if API fails
    """
    try:
        await _create_client()
        if not store.bootstrap_data:
            return "Error: Player data not available. Please try again later."

        matches = store.find_players_by_name(params.player_name, fuzzy=True)

        if not matches:
            return f"No players found matching '{params.player_name}'. Try a different spelling or use the player's surname."

        if len(matches) == 1 or (
            matches[0][1] >= 0.95 and len(matches) > 1 and matches[0][1] - matches[1][1] > 0.2
        ):
            player = matches[0][0]
            return format_player_details(player)

        # Multiple matches - show disambiguation
        output = [f"Found {len(matches)} players matching '{params.player_name}':\n"]

        for player, _score in matches[:10]:
            price = format_player_price(player.now_cost)
            status_ind = format_status_indicator(player.status, player.news)

            output.append(
                f"├─ {player.first_name} {player.second_name} ({player.web_name}) - "
                f"{player.team_name} {player.position} | {price} | "
                f"Form: {player.form} | PPG: {player.points_per_game}{status_ind}"
            )

        output.append("\nPlease use the full name or be more specific for detailed information.")
        result = "\n".join(output)
        truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
        return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_get_player_details",
    annotations={
        "title": "Get FPL Player Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_player_details(params: GetPlayerDetailsInput) -> str:
    """
    Get comprehensive information about a specific Fantasy Premier League player.

    Returns detailed player information including price, form, team, position,
    upcoming fixtures with difficulty ratings, recent gameweek performance,
    popularity, and season stats. Most comprehensive player tool.

    Args:
        params (GetPlayerDetailsInput): Validated input parameters containing:
            - player_name (str): Player name (e.g., 'Mohamed Salah', 'Erling Haaland')

    Returns:
        str: Comprehensive player information with fixtures, form, and stats

    Examples:
        - Get player info: player_name="Mohamed Salah"
        - Check fixtures: player_name="Bukayo Saka"
        - Review form: player_name="Erling Haaland"

    Error Handling:
        - Returns error if player not found
        - Suggests using fpl_find_player if name is ambiguous
        - Returns formatted error message if API fails
    """
    try:
        client = await _create_client()
        matches = store.find_players_by_name(params.player_name, fuzzy=True)

        if not matches:
            return f"No player found matching '{params.player_name}'. Use fpl_search_players to find the correct name."

        if len(matches) > 1 and matches[0][1] < 0.95:
            return f"Ambiguous player name. Use fpl_find_player to see all matches for '{params.player_name}'"

        player = matches[0][0]
        player_id = player.id

        # Fetch detailed summary from API including fixtures and history
        summary_data = await client.get_element_summary(player_id)

        # Enrich history and fixtures with team names
        history = summary_data.get("history", [])
        history = store.enrich_gameweek_history(history)

        fixtures = summary_data.get("fixtures", [])
        fixtures = store.enrich_fixtures(fixtures)

        # Format with comprehensive data
        result = format_player_details(player, history, fixtures)
        truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
        return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_compare_players",
    annotations={
        "title": "Compare FPL Players",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_compare_players(params: ComparePlayersInput) -> str:
    """
    Compare multiple Fantasy Premier League players side-by-side.

    Provides detailed comparison of 2-5 players including their stats, prices, form,
    and other key metrics. Useful for making transfer decisions.

    Args:
        params (ComparePlayersInput): Validated input parameters containing:
            - player_names (list[str]): 2-5 player names to compare

    Returns:
        str: Side-by-side comparison of players in markdown format

    Examples:
        - Compare wingers: player_names=["Salah", "Saka", "Palmer"]
        - Compare strikers: player_names=["Haaland", "Isak"]
        - Compare for transfers: player_names=["Son", "Maddison", "Odegaard"]

    Error Handling:
        - Returns error if fewer than 2 or more than 5 players provided
        - Returns error if any player name is ambiguous
        - Returns formatted error message if API fails
    """
    try:
        await _create_client()
        if not store.bootstrap_data:
            return "Error: Player data not available. Please try again later."

        players_to_compare = []
        ambiguous = []

        for name in params.player_names:
            matches = store.find_players_by_name(name, fuzzy=True)

            if not matches:
                return f"Error: No player found matching '{name}'. Use fpl_search_players to find the correct name."

            if len(matches) == 1 or (
                matches[0][1] >= 0.95 and len(matches) > 1 and matches[0][1] - matches[1][1] > 0.2
            ):
                players_to_compare.append(matches[0][0])
            else:
                ambiguous.append((name, matches[:3]))

        if ambiguous:
            output = ["Cannot compare - ambiguous player names:\n"]
            for name, matches in ambiguous:
                output.append(f"\n'{name}' could be:")
                for player, _score in matches:
                    output.append(
                        f"  - {player.first_name} {player.second_name} ({player.team_name})"
                    )
            output.append("\nPlease use more specific names or full names.")
            return "\n".join(output)

        # Construct Markdown Table
        headers = ["Metric"] + [f"**{p.web_name}**" for p in players_to_compare]
        output = [
            f"## Player Comparison ({len(players_to_compare)} players)",
            "",
            "| " + " | ".join(headers) + " |",
            "| :--- | " + " | ".join([":---"] * len(players_to_compare)) + " |",
        ]

        def get_stat(p, attr, default="0"):
            return str(getattr(p, attr, default))

        metrics = [
            ("Team", lambda p: p.team_name),
            ("Position", lambda p: p.position),
            ("Price", lambda p: format_player_price(p.now_cost)),
            ("Form", lambda p: str(p.form)),
            ("PPG", lambda p: str(p.points_per_game)),
            ("Total Points", lambda p: get_stat(p, "total_points", "N/A")),
            ("Selected By", lambda p: f"{get_stat(p, 'selected_by_percent', '0')}%"),
            (
                "Status",
                lambda p: f"{format_player_status(p.status)} {format_status_indicator(p.status, p.news)}",
            ),
            ("Minutes", lambda p: get_stat(p, "minutes", "0")),
            ("Goals", lambda p: get_stat(p, "goals_scored")),
            ("xG", lambda p: get_stat(p, "expected_goals", "0.00")),
            ("Assists", lambda p: get_stat(p, "assists")),
            ("xA", lambda p: get_stat(p, "expected_assists", "0.00")),
            ("Clean Sheets", lambda p: get_stat(p, "clean_sheets")),
            ("BPS", lambda p: get_stat(p, "bps")),
            ("Bonus", lambda p: get_stat(p, "bonus")),
            ("Def. Contribution", lambda p: get_stat(p, "defensive_contribution")),
            ("Yellow Cards", lambda p: get_stat(p, "yellow_cards")),
            ("Red Cards", lambda p: get_stat(p, "red_cards")),
        ]

        for label, getter in metrics:
            row = [f"**{label}**"] + [getter(p) for p in players_to_compare]
            output.append("| " + " | ".join(row) + " |")

        # News row
        if any(p.news for p in players_to_compare):
            row = ["**News**"] + [(p.news if p.news else "") for p in players_to_compare]
            output.append("| " + " | ".join(row) + " |")

        result = "\n".join(output)
        truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
        return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_get_top_performers",
    annotations={
        "title": "Get Top FPL Performers",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_top_performers(params: GetTopPlayersByMetricInput) -> str:
    """
    Get top 10 Fantasy Premier League performers over recent gameweeks.

    Analyzes player performance over the last N gameweeks and returns the top 10 players for
    each metric: Goals, Expected Goals (xG), Assists, Expected Assists (xA), and
    Expected Goal Involvements (xGI). Perfect for identifying in-form players for transfers.

    Args:
        params (GetTopPlayersByMetricInput): Validated input parameters containing:
            - num_gameweeks (int): Number of recent gameweeks to analyze, 1-10 (default: 5)
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: Top 10 players for each metric with their stats and team info

    Examples:
        - Last 5 gameweeks: num_gameweeks=5
        - Last 10 gameweeks: num_gameweeks=10
        - Get as JSON: num_gameweeks=5, response_format="json"

    Error Handling:
        - Returns error if no finished fixtures in range
        - Gracefully handles API failures for individual fixtures
        - Returns formatted error message if data unavailable

    Note:
        This tool might take a few seconds to complete due to the number of
        data points it needs to process.
    """
    try:
        client = await _create_client()

        # Aggregate stats from fixtures
        result = await _aggregate_player_stats_from_fixtures(client, params.num_gameweeks)

        if not result:
            msg = "No data available for the specified gameweek range."
            if params.response_format == ResponseFormat.JSON:
                return format_json_response({"error": msg})
            return msg

        if "error" in result:
            return f"Error: {result['error']}\nGameweek range: {result.get('gameweek_range', 'Unknown')}"

        if params.response_format == ResponseFormat.JSON:
            return format_json_response(result)
        else:
            # Format as markdown
            output = [
                f"# Top Performers ({result['gameweek_range']})\n",
            ]

            metric_names = {
                "goals_scored": "⚽ Goals Scored",
                "expected_goals": "📊 Expected Goals (xG)",
                "assists": "🎯 Assists",
                "expected_assists": "📈 Expected Assists (xA)",
                "expected_goal_involvements": "🔥 Expected Goal Involvements (xGI)",
                "defensive_contribution": "🛡️ Defensive Contribution",
            }

            for metric_key, metric_name in metric_names.items():
                players = result["metrics"].get(metric_key, [])
                if not players:
                    continue

                output.append(f"\n## {metric_name}\n")

                for i, player in enumerate(players, 1):
                    value = player["value"]
                    # Format value based on metric type
                    if metric_key in ("goals_scored", "assists", "defensive_contribution"):
                        value_str = f"{int(value)}"
                    else:
                        value_str = f"{value:.2f}"

                    output.append(
                        f"{i}. **{player['name']}** ({player['team']} - {player['position']}) | "
                        f"{value_str} | {player['matches_played']} matches"
                    )

            result_text = "\n".join(output)
            truncated, _ = check_and_truncate(result_text, CHARACTER_LIMIT)
            return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_get_captain_recommendations",
    annotations={
        "title": "Get Captain Recommendations",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_captain_recommendations(params: GetCaptainRecommendationsInput) -> str:
    """
    Get captaincy recommendations for the upcoming gameweek.

    Analyzes fixtures, form, and home/away advantage to recommend the best captain choices.
    If team_id is provided, analyzes YOUR specific squad. Otherwise, provides
    general recommendations from all players.

    Args:
        params (GetCaptainRecommendationsInput): Validated input parameters containing:
            - team_id (int | None): Your team ID to analyze your specific squad
            - gameweek (int | None): Gameweek to analyze (defaults to next)

    Returns:
        str: Top 3-5 captain recommendations with analysis

    Examples:
        - Analyze my team: team_id=123456
        - General picks for GW15: gameweek=15
        - General picks: (no args)

    Error Handling:
        - Returns error if gameweek invalid
        - Returns helpful message if team ID not found
        - Returns formatted error message if API fails
    """
    try:
        client = await _create_client()
        if not store.bootstrap_data:
            return "Error: Player data not available. Please try again later."

        # Determine gameweek
        gw = params.gameweek
        if not gw:
            current = store.get_current_gameweek()
            gw = (current.id + 1) if current else 1
            if gw > 38:
                gw = 38

        candidates = []

        # If team_id provided, fetch squad
        if params.team_id:
            try:
                # Fetch picks for previous GW (or current if live) to guess squad
                # For simplicity, we fetch picks for current event - 1 or current
                fetch_gw = gw - 1 if gw > 1 else 1
                picks_data = await client.get_manager_gameweek_picks(params.team_id, fetch_gw)
                picks = picks_data.get("picks", [])

                # Get element IDs
                element_ids = [p["element"] for p in picks]
                # Filter to playing players (bootstrap)
                candidates = [p for p in store.bootstrap_data.elements if p.id in element_ids]
            except Exception:
                return f"Error: Could not fetch squad for team ID {params.team_id}. Ensure the ID is correct."
        else:
            # General recommendations: Focus on top 50 by form and price > 6.0 (likely captains)
            candidates = [
                p
                for p in store.bootstrap_data.elements
                if float(p.form) > 3.0 and p.now_cost > 60 and p.status == "a"
            ]
            if len(candidates) < 10:
                candidates = sorted(
                    store.bootstrap_data.elements, key=lambda x: float(x.form), reverse=True
                )[:50]

        # Analyze candidates
        scored_candidates = []

        for p in candidates:
            # Skip GKP, DEF unless exceptional? Usually cap MID/FWD
            if p.element_type == 1:  # Skip GKP
                continue

            # Fetch Fixture
            player_fixture = None
            if store.fixtures_data:
                # Find fixture involving this player's team in target GW
                fixtures = [
                    f
                    for f in store.fixtures_data
                    if f.event == gw and (f.team_h == p.team or f.team_a == p.team)
                ]
                if fixtures:
                    player_fixture = fixtures[0]  # Assume 1 fixture

            difficulty = 3  # Default average
            is_home = False
            opponent = "Unknown"

            if player_fixture:
                if player_fixture.team_h == p.team:
                    difficulty = player_fixture.team_h_difficulty
                    is_home = True
                    opp_team = next(
                        (t for t in store.bootstrap_data.teams if t.id == player_fixture.team_a),
                        None,
                    )
                    opponent = opp_team.short_name if opp_team else "UNK"
                else:
                    difficulty = player_fixture.team_a_difficulty
                    is_home = False
                    opp_team = next(
                        (t for t in store.bootstrap_data.teams if t.id == player_fixture.team_h),
                        None,
                    )
                    opponent = opp_team.short_name if opp_team else "UNK"

            # Score Calculation
            form = float(p.form)
            ppg = float(p.points_per_game)

            score = (form * 1.5) + ((5 - difficulty) * 2.5) + (ppg * 0.5)
            if is_home:
                score += 1.0

            if p.status != "a":
                score = -1

            scored_candidates.append(
                {
                    "player": p,
                    "score": score,
                    "fixture": f"{opponent} ({'H' if is_home else 'A'})",
                    "difficulty": difficulty,
                    "is_home": is_home,
                    "form": form,
                }
            )

        # Sort and take top 5
        top_picks = sorted(scored_candidates, key=lambda x: x["score"], reverse=True)[:5]

        if params.response_format == ResponseFormat.JSON:
            result = {
                "gameweek": gw,
                "recommendations": [
                    {
                        "rank": i + 1,
                        "name": pick["player"].web_name,
                        "team": pick["player"].team_name,
                        "score": round(pick["score"], 1),
                        "fixture": pick["fixture"],
                        "difficulty": pick["difficulty"],
                        "form": pick["form"],
                    }
                    for i, pick in enumerate(top_picks)
                ],
            }
            return format_json_response(result)

        # Markdown
        output = [
            f"## 👑 Captain Recommendations (GW{gw})",
            "Based on form, fixture difficulty, and home advantage.",
            "",
        ]

        if params.team_id:
            output.append(f"**Analysis for Team ID: {params.team_id}**\n")

        for i, pick in enumerate(top_picks, 1):
            p = pick["player"]
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."

            output.append(f"### {medal} {p.web_name} ({p.team_name})")
            output.append(f"**Fixture:** {pick['fixture']} | **Diff:** {pick['difficulty']}/5")
            output.append(f"**Form:** {p.form} | **PPG:** {p.points_per_game}")
            output.append(
                f"**Rationale:** {'Great home fixture' if pick['is_home'] and pick['difficulty'] <= 2 else 'In excellent form'} "
                f"vs {pick['fixture'].split(' ')[0]}"
            )
            output.append("")

        if not top_picks:
            output.append("No suitable captain options found. Check your team ID or season status.")

        return "\n".join(output)

    except Exception as e:
        return handle_api_error(e)

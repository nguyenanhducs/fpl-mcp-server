"""FPL Fixtures Tools - MCP tools for fixture information and analysis."""

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


class GetFixturesForGameweekInput(BaseModel):
    """Input model for getting fixtures for a gameweek."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    gameweek: int = Field(
        ..., description="Gameweek number to get fixtures for (1-38)", ge=1, le=38
    )
    detailed: bool = Field(
        default=False, description="Include detailed match stats (all available metrics)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class FindFixtureOpportunitiesInput(BaseModel):
    """Input model for finding fixture opportunities."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    num_gameweeks: int = Field(
        default=5, description="Number of future gameweeks to analyze (default: 5)", ge=3, le=10
    )
    max_teams: int = Field(
        default=3, description="Number of top teams to return (default: 3)", ge=1, le=5
    )
    positions: list[str] | None = Field(
        default=None,
        description="Filter recommended players by position (e.g. ['Midfielder', 'Forward'])",
    )
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
    name="fpl_get_fixtures_for_gameweek",
    annotations={
        "title": "Get FPL Fixtures for Gameweek",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_fixtures_for_gameweek(params: GetFixturesForGameweekInput) -> str:
    """
    Get all Premier League fixtures for a specific gameweek.

    Returns complete fixture list with team names, kickoff times, scores (if finished),
    and difficulty ratings for both teams. Useful for planning transfers based on
    fixture difficulty and understanding upcoming matches.

    Args:
        params (GetFixturesForGameweekInput): Validated input parameters containing:
            - gameweek (int): Gameweek number between 1-38
            - detailed (bool): Include detailed stats (default: False)
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: Complete fixture list with times and difficulty ratings

    Examples:
        - View GW10 fixtures: gameweek=10
        - Check upcoming matches: gameweek=15
        - Get as JSON: gameweek=20, response_format="json"

    Error Handling:
        - Returns error if gameweek number invalid (must be 1-38)
        - Returns error if no fixtures found for gameweek
        - Returns formatted error message if data unavailable
    """
    try:
        await _create_client()
        if not store.fixtures_data:
            return "Error: Fixtures data not available. Please try again later."

        gw_fixtures = [f for f in store.fixtures_data if f.event == params.gameweek]

        if not gw_fixtures:
            return f"No fixtures found for gameweek {params.gameweek}. This gameweek may not exist or fixtures may not be scheduled yet."

        # Enrich fixtures with team names
        gw_fixtures_enriched = store.enrich_fixtures(gw_fixtures)
        gw_fixtures_sorted = sorted(gw_fixtures_enriched, key=lambda x: x.get("kickoff_time") or "")

        if params.response_format == ResponseFormat.JSON:
            result = {
                "gameweek": params.gameweek,
                "fixture_count": len(gw_fixtures_sorted),
                "fixtures": [],
            }

            for fixture in gw_fixtures_sorted:
                fixture_data = {
                    "home_team": fixture.get("team_h_name"),
                    "home_team_short": fixture.get("team_h_short"),
                    "away_team": fixture.get("team_a_name"),
                    "away_team_short": fixture.get("team_a_short"),
                    "kickoff_time": fixture.get("kickoff_time"),
                    "finished": fixture.get("finished"),
                    "home_score": fixture.get("team_h_score") if fixture.get("finished") else None,
                    "away_score": fixture.get("team_a_score") if fixture.get("finished") else None,
                    "home_difficulty": fixture.get("team_h_difficulty"),
                    "away_difficulty": fixture.get("team_a_difficulty"),
                }

                if params.detailed and fixture.get("stats"):
                    stats = {}
                    for stat in fixture.get("stats", []):
                        if hasattr(stat, "model_dump"):
                            stat_dict = stat.model_dump()
                        elif hasattr(stat, "__dict__"):
                            stat_dict = stat.__dict__
                        else:
                            stat_dict = stat

                        identifier = stat_dict.get("identifier")
                        if not identifier:
                            continue

                        stats[identifier] = {"h": [], "a": []}

                        # Process home stats
                        for item in stat_dict.get("h", []):
                            if hasattr(item, "value"):
                                value = item.value
                                element = item.element
                            else:
                                value = item.get("value")
                                element = item.get("element")

                            stats[identifier]["h"].append(
                                {
                                    "name": store.get_player_name(element),
                                    "value": value,
                                    "element": element,
                                }
                            )

                        # Process away stats
                        for item in stat_dict.get("a", []):
                            if hasattr(item, "value"):
                                value = item.value
                                element = item.element
                            else:
                                value = item.get("value")
                                element = item.get("element")

                            stats[identifier]["a"].append(
                                {
                                    "name": store.get_player_name(element),
                                    "value": value,
                                    "element": element,
                                }
                            )

                    fixture_data["stats"] = stats

                result["fixtures"].append(fixture_data)

            return format_json_response(result)
        else:
            output = [
                f"**Gameweek {params.gameweek} Fixtures ({len(gw_fixtures_enriched)} matches)**\n"
            ]

            for fixture in gw_fixtures_sorted:
                home_name = fixture.get("team_h_short", "Unknown")
                away_name = fixture.get("team_a_short", "Unknown")

                status = "✓" if fixture.get("finished") else "○"
                score = (
                    f"{fixture.get('team_h_score')}-{fixture.get('team_a_score')}"
                    if fixture.get("finished")
                    else "vs"
                )
                kickoff = (
                    fixture.get("kickoff_time", "")[:16].replace("T", " ")
                    if fixture.get("kickoff_time")
                    else "TBD"
                )

                output.append(
                    f"{status} {home_name} {score} {away_name} | "
                    f"Kickoff: {kickoff} | "
                    f"Difficulty: H:{fixture.get('team_h_difficulty')} A:{fixture.get('team_a_difficulty')}"
                )

                if params.detailed and fixture.get("stats"):
                    stats_output = []
                    # Filter for interesting stats or show all? Showing all as requested.
                    # Common stats order: goals_scored, assists, own_goals, penalties_saved, penalties_missed, yellow_cards, red_cards, bonus, saves, bps
                    priority_stats = [
                        "goals_scored",
                        "assists",
                        "bonus",
                        "yellow_cards",
                        "red_cards",
                        "saves",
                    ]
                    other_stats = []
                    for s in fixture.get("stats", []):
                        ident = s.identifier if hasattr(s, "identifier") else s.get("identifier")

                        if ident and ident not in priority_stats:
                            other_stats.append(ident)
                    all_stats = priority_stats + other_stats

                    for stat_name in all_stats:
                        # Find stat data
                        stat_data = None
                        for s in fixture.get("stats", []):
                            s_ident = (
                                s.identifier if hasattr(s, "identifier") else s.get("identifier")
                            )
                            if s_ident == stat_name:
                                stat_data = s
                                break
                        if not stat_data:
                            continue

                        # Convert to dict access if needed
                        if hasattr(stat_data, "h"):
                            h_items = stat_data.h
                            a_items = stat_data.a
                        else:
                            h_items = stat_data.get("h", [])
                            a_items = stat_data.get("a", [])

                        if not h_items and not a_items:
                            continue

                        # Format stat line: Stat: Name (val), Name (val) (H) | Name (val) (A)
                        h_strs = []
                        for item in h_items:
                            val = item.value if hasattr(item, "value") else item.get("value")
                            elem = item.element if hasattr(item, "element") else item.get("element")
                            h_strs.append(f"{store.get_player_name(elem)} ({val})")

                        a_strs = []
                        for item in a_items:
                            val = item.value if hasattr(item, "value") else item.get("value")
                            elem = item.element if hasattr(item, "element") else item.get("element")
                            a_strs.append(f"{store.get_player_name(elem)} ({val})")

                        stat_display = stat_name.replace("_", " ").title()
                        if stat_name == "goals_scored":
                            stat_display = "⚽ Goals"
                        elif stat_name == "assists":
                            stat_display = "🅰️ Assists"
                        elif stat_name == "bonus":
                            stat_display = "💎 Bonus"
                        elif stat_name == "yellow_cards":
                            stat_display = "🟨 Yellows"
                        elif stat_name == "red_cards":
                            stat_display = "🟥 Reds"
                        elif stat_name == "saves":
                            stat_display = "🧤 Saves"

                        if h_strs or a_strs:
                            line = f"   - **{stat_display}**: "
                            if h_strs:
                                line += f"{', '.join(h_strs)} ({home_name})"
                            if h_strs and a_strs:
                                line += " | "
                            if a_strs:
                                line += f"{', '.join(a_strs)} ({away_name})"
                            stats_output.append(line)

                    if stats_output:
                        output.extend(stats_output)
                        output.append("")  # Empty line separator

            result = "\n".join(output)
            truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
            return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_find_fixture_opportunities",
    annotations={
        "title": "Find Fixture Opportunities",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_find_fixture_opportunities(params: FindFixtureOpportunitiesInput) -> str:
    """
    Find teams with the easiest upcoming fixtures and their best assets.

    Analyzes fixture difficulty for all 20 teams over the next N gameweeks.
    Identifies teams with the most favorable schedule and recommends their
    top-performing players (filtered by position if requested).

    Args:
        params (FindFixtureOpportunitiesInput): Validated input parameters containing:
            - num_gameweeks (int): Number of gameweeks to analyze (3-10)
            - max_teams (int): Number of teams to recommend (1-5)
            - positions (list[str] | None): Optional position filter

    Returns:
        str: Analysis of best teams to target and their key players

    Examples:
        - Target next 5 GWs: num_gameweeks=5
        - Find best attackers: positions=['Midfielder', 'Forward']

    Error Handling:
        - Returns error if data unavailable
        - Returns formatted error message if API fails
    """
    try:
        await _create_client()
        if not store.bootstrap_data:
            return "Error: Player data not available."

        # Determine current gameweek
        current_gw_data = store.get_current_gameweek()
        current_gw = current_gw_data.id if current_gw_data else 1
        start_gw = current_gw + 1

        # Calculate average difficulty for each team
        team_difficulties = []

        # Helper to get difficulty for a team ID in a GW
        def get_team_fixtures(team_id):
            fixtures = []
            for gw in range(start_gw, start_gw + params.num_gameweeks):
                if gw > 38:
                    break
                # Find fixture for this team in this GW
                # Use enriched fixtures if pre-calculated, or search raw
                # Searching raw is faster here than full enrich loop
                matches = [
                    f
                    for f in store.fixtures_data
                    if f.event == gw and (f.team_h == team_id or f.team_a == team_id)
                ]
                for m in matches:
                    is_home = m.team_h == team_id
                    diff = m.team_h_difficulty if is_home else m.team_a_difficulty
                    opponent_id = m.team_a if is_home else m.team_h
                    opponent = next(
                        (t for t in store.bootstrap_data.teams if t.id == opponent_id), None
                    )
                    fixtures.append(
                        {
                            "gameweek": gw,
                            "difficulty": diff,
                            "opponent": opponent.short_name if opponent else "UNK",
                            "is_home": is_home,
                        }
                    )
            return fixtures

        for team in store.bootstrap_data.teams:
            fixtures = get_team_fixtures(team.id)
            if not fixtures:
                continue

            avg_diff = sum(f["difficulty"] for f in fixtures) / len(fixtures)
            team_difficulties.append({"team": team, "avg_diff": avg_diff, "fixtures": fixtures})

        # Sort by easiest (lowest avg difficulty)
        team_difficulties.sort(key=lambda x: x["avg_diff"])
        top_teams = team_difficulties[: params.max_teams]

        # Find top players for these teams
        # Map position string to element_type (1=GKP, 2=DEF, 3=MID, 4=FWD)
        pos_map = {"Goalkeeper": 1, "Defender": 2, "Midfielder": 3, "Forward": 4}
        target_types = []
        if params.positions:
            for p in params.positions:
                p_norm = p.capitalize()
                # Handle plurals
                if p_norm.endswith("s"):
                    p_norm = p_norm[:-1]
                idx = pos_map.get(p_norm)
                if idx:
                    target_types.append(idx)

        result_teams = []

        for item in top_teams:
            team = item["team"]
            # Get players for this team
            team_players = [
                p for p in store.bootstrap_data.elements if p.team == team.id and p.status != "u"
            ]

            if target_types:
                team_players = [p for p in team_players if p.element_type in target_types]

            # Sort by form (best assets)
            top_assets = sorted(team_players, key=lambda x: float(x.form), reverse=True)[:3]

            result_teams.append(
                {
                    "team_name": team.name,
                    "avg_diff": item["avg_diff"],
                    "fixtures": item["fixtures"],
                    "best_players": top_assets,
                }
            )

        if params.response_format == ResponseFormat.JSON:
            json_out = {
                "start_gameweek": start_gw,
                "end_gameweek": start_gw + params.num_gameweeks - 1,
                "opportunities": [],
            }
            for rt in result_teams:
                # Format fixtures string
                fixtures_list = [
                    f"{f['opponent']} ({'H' if f['is_home'] else 'A'})" for f in rt["fixtures"]
                ]
                json_out["opportunities"].append(
                    {
                        "team": rt["team_name"],
                        "difficulty_score": round(rt["avg_diff"], 2),
                        "fixtures": fixtures_list,
                        "recommended_players": [p.web_name for p in rt["best_players"]],
                    }
                )
            return format_json_response(json_out)

        # Markdown Output
        output = [
            f"## 🗓️ Fixture Opportunities (Next {params.num_gameweeks} GWs)",
            "Top teams with the easiest schedules to target:",
            "",
        ]

        for i, rt in enumerate(result_teams, 1):
            fixtures_str = " - ".join(
                [f"**{f['opponent']}** ({'H' if f['is_home'] else 'A'})" for f in rt["fixtures"]]
            )

            output.append(f"### {i}. {rt['team_name']} (Diff: {rt['avg_diff']:.1f})")
            output.append(f"🗓️ **Schedule:** {fixtures_str}")

            player_names = [f"{p.web_name} ({p.form} form)" for p in rt["best_players"]]
            output.append(f"🔥 **Targets:** {', '.join(player_names)}")
            output.append("")

        return "\n".join(output)

    except Exception as e:
        return handle_api_error(e)

"""FPL Transfer Tools - MCP tools for transfer statistics and live trends."""

from pydantic import BaseModel, ConfigDict, Field

from ..client import FPLClient
from ..constants import CHARACTER_LIMIT
from ..formatting import format_player_price
from ..state import store
from ..utils import (
    ResponseFormat,
    check_and_truncate,
    format_json_response,
    handle_api_error,
)
from . import mcp


class GetTopTransferredPlayersInput(BaseModel):
    """Input model for getting top transferred players."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    limit: int = Field(default=10, description="Number of players to return (1-50)", ge=1, le=50)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class GetManagerTransfersByGameweekInput(BaseModel):
    """Input model for getting manager transfers."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    team_id: int = Field(..., description="Manager's team ID (entry ID) from FPL", ge=1)
    gameweek: int = Field(..., description="Gameweek number (1-38)", ge=1, le=38)


class AnalyzeTransferInput(BaseModel):
    """Input model for analyzing a potential transfer."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    player_out: str = Field(
        ...,
        description="Name of player to transfer out (e.g., 'Salah')",
        min_length=2,
        max_length=100,
    )
    player_in: str = Field(
        ...,
        description="Name of player to transfer in (e.g., 'Palmer')",
        min_length=2,
        max_length=100,
    )
    my_team_id: int | None = Field(
        default=None, description="Your team ID to check budget/value impact (optional)"
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
    name="fpl_get_top_transferred_players",
    annotations={
        "title": "Get Top Transferred FPL Players",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_top_transferred_players(params: GetTopTransferredPlayersInput) -> str:
    """
    Get the most transferred in and out players for the current gameweek.

    Shows live transfer trends to identify popular moves happening right now. Uses
    real-time data from bootstrap for instant response. Essential for understanding
    the current template and finding differentials.

    Args:
        params (GetTopTransferredPlayersInput): Validated input parameters containing:
            - limit (int): Number of players to return, 1-50 (default: 10)
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: Top transferred in and out players with net transfers

    Examples:
        - Top 10: limit=10
        - Top 20: limit=20
        - Get as JSON: limit=15, response_format="json"

    Error Handling:
        - Returns error if no transfer data available
        - Returns formatted error message if current gameweek unavailable
    """
    try:
        await _create_client()
        if not store.bootstrap_data:
            return "Error: Player data not available. Please try again later."

        # Get current gameweek
        current_gw = store.get_current_gameweek()
        if not current_gw:
            return "Error: Could not determine current gameweek. Data may be unavailable."

        gameweek = current_gw.id

        # Use bootstrap data directly - instant, no API calls!
        players_with_transfers = []

        for player in store.bootstrap_data.elements:
            transfers_in = getattr(player, "transfers_in_event", 0)
            transfers_out = getattr(player, "transfers_out_event", 0)

            # Only include players with transfer activity
            if transfers_in > 0 or transfers_out > 0:
                players_with_transfers.append(
                    {
                        "player": player,
                        "transfers_in": transfers_in,
                        "transfers_out": transfers_out,
                        "net_transfers": transfers_in - transfers_out,
                        "points": getattr(player, "event_points", 0),
                    }
                )

        if not players_with_transfers:
            return f"No transfer data available for gameweek {gameweek}. The gameweek may not have started yet."

        # Sort by transfers in and out
        most_transferred_in = sorted(
            players_with_transfers, key=lambda x: x["transfers_in"], reverse=True
        )[: params.limit]
        most_transferred_out = sorted(
            players_with_transfers, key=lambda x: x["transfers_out"], reverse=True
        )[: params.limit]

        if params.response_format == ResponseFormat.JSON:
            result = {
                "gameweek": gameweek,
                "transferred_in": [
                    {
                        "rank": i + 1,
                        "player_name": data["player"].web_name,
                        "team": data["player"].team_name,
                        "position": data["player"].position,
                        "price": format_player_price(data["player"].now_cost),
                        "transfers_in": data["transfers_in"],
                        "net_transfers": data["net_transfers"],
                        "points": data["points"],
                    }
                    for i, data in enumerate(most_transferred_in)
                ],
                "transferred_out": [
                    {
                        "rank": i + 1,
                        "player_name": data["player"].web_name,
                        "team": data["player"].team_name,
                        "position": data["player"].position,
                        "price": format_player_price(data["player"].now_cost),
                        "transfers_out": data["transfers_out"],
                        "net_transfers": data["net_transfers"],
                        "points": data["points"],
                    }
                    for i, data in enumerate(most_transferred_out)
                ],
            }
            return format_json_response(result)
        else:
            output = [
                f"**Gameweek {gameweek} - Live Transfer Trends** 🔥",
                "",
                f"**Most Transferred IN (Top {min(params.limit, len(most_transferred_in))}):**",
                "",
            ]

            for i, data in enumerate(most_transferred_in, 1):
                player = data["player"]
                price = format_player_price(player.now_cost)
                output.append(
                    f"{i:2d}. {player.web_name:20s} ({player.team_name:15s} {player.position}) | "
                    f"{price} | In: {data['transfers_in']:,} | "
                    f"Net: {data['net_transfers']:+,} | {data['points']}pts"
                )

            output.extend(
                [
                    "",
                    f"**Most Transferred OUT (Top {min(params.limit, len(most_transferred_out))}):**",
                    "",
                ]
            )

            for i, data in enumerate(most_transferred_out, 1):
                player = data["player"]
                price = format_player_price(player.now_cost)
                output.append(
                    f"{i:2d}. {player.web_name:20s} ({player.team_name:15s} {player.position}) | "
                    f"{price} | Out: {data['transfers_out']:,} | "
                    f"Net: {data['net_transfers']:+,} | {data['points']}pts"
                )

            result = "\n".join(output)
            truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
            return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_get_manager_transfers_by_gameweek",
    annotations={
        "title": "Get Manager's FPL Transfers",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_manager_transfers_by_gameweek(
    params: GetManagerTransfersByGameweekInput,
) -> str:
    """
    Get all transfers made by a specific manager in a specific gameweek.

    Shows which players were transferred in and out, transfer costs, and timing.
    Useful for analyzing manager strategy and understanding when/why they made moves.
    Requires manager's team ID (entry ID) which can be found in the FPL URL.

    Args:
        params (GetManagerTransfersByGameweekInput): Validated input parameters containing:
            - team_id (int): Manager's team ID (entry ID)
            - gameweek (int): Gameweek number (1-38)

    Returns:
        str: Complete transfer history for the gameweek with costs

    Examples:
        - View transfers: team_id=123456, gameweek=20
        - Check costs: team_id=789012, gameweek=15

    Error Handling:
        - Returns error if team ID invalid
        - Returns message if no transfers in gameweek
        - Returns formatted error message if API fails
    """
    try:
        client = await _create_client()

        # Fetch manager entry info to get team name
        try:
            manager_entry = await client.get_manager_entry(params.team_id)
            manager_name = f"{manager_entry.get('player_first_name', '')} {manager_entry.get('player_last_name', '')}".strip()
            team_name = manager_entry.get("name", f"Team {params.team_id}")
        except Exception:
            manager_name = f"Manager {params.team_id}"
            team_name = f"Team {params.team_id}"

        # Fetch all transfer history
        transfers_data = await client.get_manager_transfers(params.team_id)

        # Filter transfers for the specific gameweek
        gw_transfers = [t for t in transfers_data if t.get("event") == params.gameweek]

        if not gw_transfers:
            return f"No transfers found for {manager_name} in gameweek {params.gameweek}. They may have used their free transfers or rolled them over."

        output = [
            f"**{team_name}** - {manager_name}",
            f"Gameweek {params.gameweek} Transfers",
            "",
        ]

        total_cost = 0
        for i, transfer in enumerate(gw_transfers, 1):
            # Get player details
            player_in_id = transfer.get("element_in")
            player_out_id = transfer.get("element_out")

            player_in_name = store.get_player_name(player_in_id)
            player_out_name = store.get_player_name(player_out_id)

            # Get player info for prices
            player_in_info = next(
                (p for p in store.bootstrap_data.elements if p.id == player_in_id), None
            )
            player_out_info = next(
                (p for p in store.bootstrap_data.elements if p.id == player_out_id),
                None,
            )

            price_in = format_player_price(player_in_info.now_cost) if player_in_info else "£0.0m"
            price_out = (
                format_player_price(player_out_info.now_cost) if player_out_info else "£0.0m"
            )

            # Transfer details
            transfer_time = transfer.get("time", "Unknown")
            cost = transfer.get("event_cost", 0)
            total_cost += cost

            output.append(f"**Transfer {i}:**")
            output.append(
                f"OUT: {player_out_name} ({player_out_info.team_name if player_out_info else 'Unknown'} "
                f"{player_out_info.position if player_out_info else 'UNK'}) - {price_out}"
            )
            output.append(
                f"IN:  {player_in_name} ({player_in_info.team_name if player_in_info else 'Unknown'} "
                f"{player_in_info.position if player_in_info else 'UNK'}) - {price_in}"
            )
            if cost > 0:
                output.append(f"Cost: -{cost} points")
            output.append(
                f"Time: {transfer_time[:19] if transfer_time != 'Unknown' else 'Unknown'}"
            )
            output.append("")

        output.extend(
            [
                "**Summary:**",
                f"├─ Total Transfers: {len(gw_transfers)}",
                f"├─ Total Cost: -{total_cost} points"
                if total_cost > 0
                else "├─ Free Transfers Used",
            ]
        )

        result = "\n".join(output)
        truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
        return truncated

    except Exception as e:
        return handle_api_error(e)


class GetManagerChipsInput(BaseModel):
    """Input model for getting manager chip usage."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    team_id: int = Field(..., description="Manager's team ID (entry ID) from FPL", ge=1)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


@mcp.tool(
    name="fpl_get_manager_chips",
    annotations={
        "title": "Get Manager's Chip Usage",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_get_manager_chips(params: GetManagerChipsInput) -> str:
    """
    Get a manager's chip usage showing which chips have been used and which are still available.

    Since the 2025/2026 season, FPL provides 4 chips per half-season.

    Shows used chips with gameweek and timing, plus remaining available chips.
    Essential for strategic chip planning and recommendations.

    Args:
        params (GetManagerChipsInput): Validated input parameters containing:
            - team_id (int): Manager's team ID (entry ID)
            - response_format (ResponseFormat): 'markdown' or 'json' (default: markdown)

    Returns:
        str: Chip usage summary with used and available chips

    Examples:
        - Check chip status: team_id=123456
        - JSON format: team_id=123456, response_format="json"

    Error Handling:
        - Returns error if team ID invalid
        - Returns formatted error message if API fails
    """
    try:
        client = await _create_client()

        # Fetch manager history for used chips
        history_data = await client.get_manager_history(params.team_id)
        used_chips = history_data.get("chips", [])

        # Get all available chips from bootstrap data
        bootstrap_chips = store.bootstrap_data.chips if store.bootstrap_data else []

        # Get current gameweek to determine which chips are available
        current_gw_data = store.get_current_gameweek()
        current_gw = current_gw_data.id if current_gw_data else 1

        # Build chip availability map
        # FPL chip names: "wildcard", "freehit", "bboost", "3xc"
        chip_display_names = {
            "wildcard": "Wildcard",
            "freehit": "Free Hit",
            "bboost": "Bench Boost",
            "3xc": "Triple Captain",
        }

        # Build available chips list
        # Match used chips to specific chip instances based on gameweek used
        available_chips = []
        for chip in bootstrap_chips:
            chip_name = chip.get("name")
            start_gw = chip.get("start_event", 1)
            end_gw = chip.get("stop_event", 38)

            # Check if this specific chip instance was used
            # Match by checking if any used chip has this name and was used within this chip's GW range
            chip_used = any(
                used_chip["name"] == chip_name and start_gw <= used_chip["event"] <= end_gw
                for used_chip in used_chips
            )

            # Chip is available if: within current gameweek range AND not used
            if start_gw <= current_gw <= end_gw and not chip_used:
                available_chips.append(
                    {
                        "name": chip_name,
                        "display_name": chip_display_names.get(chip_name, chip_name.title()),
                        "start_event": start_gw,
                        "stop_event": end_gw,
                        "half": "First Half" if end_gw <= 19 else "Second Half",
                    }
                )

        if params.response_format == ResponseFormat.JSON:
            result = {
                "team_id": params.team_id,
                "current_gameweek": current_gw,
                "used_chips": [
                    {
                        "name": chip["name"],
                        "display_name": chip_display_names.get(chip["name"], chip["name"].title()),
                        "gameweek": chip["event"],
                        "time": chip["time"],
                    }
                    for chip in used_chips
                ],
                "available_chips": available_chips,
            }
            return format_json_response(result)
        else:
            # Markdown output
            output = [
                f"**Chip Usage Summary** (Team ID: {params.team_id})",
                f"Current Gameweek: {current_gw}",
                "",
                f"**Used Chips ({len(used_chips)}):**",
                "",
            ]

            if used_chips:
                # Group used chips by half
                first_half_used = [c for c in used_chips if c["event"] <= 19]
                second_half_used = [c for c in used_chips if c["event"] >= 20]

                if first_half_used:
                    output.append("  **First Half (GW1-19):**")
                    for chip in first_half_used:
                        display_name = chip_display_names.get(chip["name"], chip["name"].title())
                        gw = chip["event"]
                        time = chip["time"][:10] if chip.get("time") else "Unknown"
                        output.append(f"    ✓ {display_name} - GW{gw} | Used: {time}")
                    output.append("")

                if second_half_used:
                    output.append("  **Second Half (GW20-38):**")
                    for chip in second_half_used:
                        display_name = chip_display_names.get(chip["name"], chip["name"].title())
                        gw = chip["event"]
                        time = chip["time"][:10] if chip.get("time") else "Unknown"
                        output.append(f"    ✓ {display_name} - GW{gw} | Used: {time}")
                    output.append("")
            else:
                output.append("No chips used yet")

            output.extend(
                [
                    "",
                    f"**Available Chips ({len(available_chips)}):**",
                    "",
                ]
            )

            if available_chips:
                # Group by half
                first_half_available = [c for c in available_chips if c["half"] == "First Half"]
                second_half_available = [c for c in available_chips if c["half"] == "Second Half"]

                if first_half_available:
                    output.append("  **First Half (GW1-19):**")
                    for chip in first_half_available:
                        output.append(f"    • {chip['display_name']}")
                    output.append("")

                if second_half_available:
                    output.append("  **Second Half (GW20-38):**")
                    for chip in second_half_available:
                        output.append(f"    • {chip['display_name']}")
            else:
                output.append("All chips have been used")

            result = "\n".join(output)
            truncated, _ = check_and_truncate(result, CHARACTER_LIMIT)
            return truncated

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="fpl_analyze_transfer",
    annotations={
        "title": "Analyze FPL Transfer",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fpl_analyze_transfer(params: AnalyzeTransferInput) -> str:
    """
    Analyze a potential transfer decision between two players.

    Compares the player being transferred out vs the player being transferred in.
    Analyzes form, upcoming fixtures (next 5), price difference, and overall value.
    Provides a direct recommendation based on the data.

    Args:
        params (AnalyzeTransferInput): Validated input parameters containing:
            - player_out (str): Name of player to remove
            - player_in (str): Name of player to add
            - my_team_id (int | None): Optional team ID to check budget impact

    Returns:
        str: Detailed transfer analysis and recommendation

    Examples:
        - Analyze move: player_out="Salah", player_in="Palmer"
        - Check budget: player_out="Saka", player_in="Foden", my_team_id=123456

    Error Handling:
        - Returns error if either player not found
        - Returns error if players play different positions (unless specified)
        - Returns formatted error message if API fails
    """
    try:
        client = await _create_client()
        if not store.bootstrap_data:
            return "Error: Player data not available. Please try again later."

        # Helper to find player
        def find_player(name):
            matches = store.find_players_by_name(name, fuzzy=True)
            if not matches:
                return None, f"Player '{name}' not found."
            if (
                len(matches) > 1
                and matches[0][1] < 0.95
                and not (matches[0][1] - matches[1][1] > 0.2)
            ):
                return (
                    None,
                    f"Ambiguous name '{name}'. Did you mean: {', '.join(m[0].web_name for m in matches[:3])}?",
                )
            return matches[0][0], None

        # Find both players
        p_out, err_out = find_player(params.player_out)
        if err_out:
            return f"Error finding player_out: {err_out}"

        p_in, err_in = find_player(params.player_in)
        if err_in:
            return f"Error finding player_in: {err_in}"

        # Check positions
        pos_names = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
        if p_out.element_type != p_in.element_type:
            # element_type 1=GKP, 2=DEF, 3=MID, 4=FWD
            # Get position names
            return (
                f"Invalid transfer: {p_out.web_name} is a {pos_names.get(p_out.element_type)} "
                f"while {p_in.web_name} is a {pos_names.get(p_in.element_type)}. "
                f"Transfers must be between players of the same position."
            )

        # Get fixtures for next 5 gameweeks
        current_gw_data = store.get_current_gameweek()
        start_gw = (current_gw_data.id + 1) if current_gw_data else 1
        # Handle case where season is over
        if start_gw > 38:
            start_gw = 38

        # Fetch detailed summaries for both
        summary_out = await client.get_element_summary(p_out.id)
        summary_in = await client.get_element_summary(p_in.id)

        # Process Fixtures
        fixtures_out = store.enrich_fixtures(summary_out.get("fixtures", []))
        fixtures_in = store.enrich_fixtures(summary_in.get("fixtures", []))

        # Filter next 5 fixtures
        next_5_out = [f for f in fixtures_out if f["event"] and f["event"] >= start_gw][:5]
        next_5_in = [f for f in fixtures_in if f["event"] and f["event"] >= start_gw][:5]

        # Calculate difficulty score (lower is easier)
        def calc_difficulty(fixtures, is_attacker):
            total = 0
            count = 0
            for f in fixtures:
                diff = (
                    f.get("team_h_difficulty") if f.get("is_home") else f.get("team_a_difficulty")
                )
                if diff is None:
                    diff = 3  # Default to average if missing
                total += int(diff)
                count += 1
            return total / count if count > 0 else 0

        # Heuristic: MIDs and FWDs are attackers, DEF and GKP defenders
        is_attacker = p_out.element_type in [3, 4]
        diff_out = calc_difficulty(next_5_out, is_attacker)
        diff_in = calc_difficulty(next_5_in, is_attacker)

        # Calculate budget impact
        price_diff = p_in.now_cost - p_out.now_cost

        if params.response_format == ResponseFormat.JSON:
            result = {
                "transfer": {
                    "out": p_out.web_name,
                    "in": p_in.web_name,
                    "position": p_out.position,
                },
                "analysis": {
                    "price_change": price_diff / 10,
                    "fixture_diff_score": {
                        "out": round(diff_out, 2),
                        "in": round(diff_in, 2),
                        "easier_fixtures": "in" if diff_in < diff_out else "out",
                    },
                    "form": {"out": float(p_out.form), "in": float(p_in.form)},
                    "points_per_game": {
                        "out": float(p_out.points_per_game),
                        "in": float(p_in.points_per_game),
                    },
                },
                "recommendation": "TRANSFER IN"
                if diff_in < diff_out and float(p_in.form) > float(p_out.form)
                else "HOLD",
            }
            return format_json_response(result)

        # Markdown Output
        output = [
            f"## Transfer Analysis: {p_out.web_name} ➔ {p_in.web_name}",
            f"**Position:** {pos_names.get(p_out.element_type)} | **Budget Impact:** {format_player_price(price_diff)}",
            "",
            "### 📊 Head-to-Head Comparison",
            f"| Metric | ❌ {p_out.web_name} (OUT) | ✅ {p_in.web_name} (IN) | Diff |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Price** | {format_player_price(p_out.now_cost)} | {format_player_price(p_in.now_cost)} | {format_player_price(price_diff)} |",
            f"| **Form** | {p_out.form} | {p_in.form} | {float(p_in.form) - float(p_out.form):.1f} |",
            f"| **PPG** | {p_out.points_per_game} | {p_in.points_per_game} | {float(p_in.points_per_game) - float(p_out.points_per_game):.1f} |",
            f"| **Total Pts** | {getattr(p_out, 'total_points', 0)} | {getattr(p_in, 'total_points', 0)} | {getattr(p_in, 'total_points', 0) - getattr(p_out, 'total_points', 0)} |",
            f"| **Ownership** | {getattr(p_out, 'selected_by_percent', '0.0')}% | {getattr(p_in, 'selected_by_percent', '0.0')}% | {float(getattr(p_in, 'selected_by_percent', '0.0')) - float(getattr(p_out, 'selected_by_percent', '0.0')):+.1f}% |",
            "",
            "### 🗓️ Upcoming Fixtures (Next 5)",
            "Lower difficulty score is better (easier fixtures).",
            "",
            f"**{p_out.web_name}** (Avg Diff: {diff_out:.2f})",
        ]

        # Helper to format fixture string
        def format_fixture(f):
            opp = f.get("team_a_short") if f.get("is_home") else f.get("team_h_short")
            if not opp:
                opp = "UNK"
            diff = f.get("difficulty", "?")
            loc = "H" if f.get("is_home") else "A"
            return f"{opp} ({loc}) [{diff}]"

        # Format fixtures
        out_fixtures_str = " | ".join([format_fixture(f) for f in next_5_out])
        output.append(f"└─ {out_fixtures_str}")

        output.append("")
        output.append(f"**{p_in.web_name}** (Avg Diff: {diff_in:.2f})")
        in_fixtures_str = " | ".join([format_fixture(f) for f in next_5_in])
        output.append(f"└─ {in_fixtures_str}")

        output.append("")
        output.append("### 💡 Recommendation")

        # Simple Logic
        better_fixtures = diff_in < diff_out
        better_form = float(p_in.form) > float(p_out.form)
        cheaper = price_diff < 0

        score = 0
        if better_fixtures:
            score += 2
        if better_form:
            score += 1
        if cheaper:
            score += 0.5
        if float(p_in.points_per_game) > float(p_out.points_per_game):
            score += 1

        if score >= 3:
            output.append(
                f"✅ **Recommended Transfer** - {p_in.web_name} is a strong upgrade with better fixtures and stats."
            )
        elif score >= 1.5:
            output.append(
                f"⚖️ **Consider Transfer** - {p_in.web_name} has some advantages, but it's close."
            )
        else:
            output.append(
                f"🛑 **Hold Transfer** - {p_out.web_name} looks like the better hold right now."
            )

        # Add availability check
        if p_in.status != "a":
            output.append(f"\n⚠️ **Warning:** {p_in.web_name} is currently flagged: {p_in.news}")

        return "\n".join(output)

    except Exception as e:
        return handle_api_error(e)

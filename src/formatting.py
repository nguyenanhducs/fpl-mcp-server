"""
Shared formatting utilities for FPL MCP tools and resources.
Centralizes Markdown generation logic to ensure consistency and reduce duplication.
"""

from typing import Any

from .utils import format_player_price


def format_player_details(
    player: Any,
    history: list[dict[str, Any]] | None = None,
    fixtures: list[dict[str, Any]] | None = None,
) -> str:
    """
    Format comprehensive player information including fixtures and history.

    Args:
        player: ElementData object or similar having player attributes
        history: Optional list of past gameweek performance dictionaries
        fixtures: Optional list of upcoming fixture dictionaries

    Returns:
        Formatted markdown string
    """
    # Handle potentially missing attributes
    team_name = getattr(player, "team_name", "Unknown")
    position = getattr(player, "position", "Unknown")

    price_val = getattr(player, "now_cost", 0)
    price = format_player_price(price_val)

    output = [
        f"**{player.web_name}** ({player.first_name} {player.second_name})",
        f"Team: {team_name} | Position: {position} | Price: {price}",
        "",
    ]

    # Upcoming Fixtures
    if fixtures:
        output.append(f"**Upcoming Fixtures ({len(fixtures)}):**")
        for fixture in fixtures[:5]:
            opponent_name = (
                fixture.get("team_h_short")
                if not fixture["is_home"]
                else fixture.get("team_a_short", "Unknown")
            )
            home_away = "H" if fixture["is_home"] else "A"
            difficulty = "●" * fixture["difficulty"]

            output.append(
                f"├─ GW{fixture['event']}: vs {opponent_name} ({home_away}) | "
                f"Difficulty: {difficulty} ({fixture['difficulty']}/5)"
            )
        output.append("")

    # Recent Gameweek History
    if history:
        recent_history = history[-5:]
        output.append(f"**Recent Performance (Last {len(recent_history)} GWs):**")

        for gw in recent_history:
            opponent_name = gw.get("opponent_team_short", "Unknown")
            home_away = "H" if gw["was_home"] else "A"
            xg = gw.get("expected_goals", "0.00")
            xa = gw.get("expected_assists", "0.00")

            output.append(
                f"├─ GW{gw['round']}: {gw['total_points']}pts vs {opponent_name} ({home_away}) | "
                f"{gw['minutes']}min | xG: {xg} G:{gw['goals_scored']} xA: {xa} A:{gw['assists']} "
                f"CS:{gw['clean_sheets']} | Bonus: {gw['bonus']}"
            )

        total_points = sum(gw["total_points"] for gw in recent_history)
        avg_points = total_points / len(recent_history) if recent_history else 0
        total_minutes = sum(gw["minutes"] for gw in recent_history)
        avg_minutes = total_minutes / len(recent_history) if recent_history else 0

        output.extend(
            [
                "",
                "**Recent Averages:**",
                f"├─ Points per game: {avg_points:.1f}",
                f"├─ Minutes per game: {avg_minutes:.0f}",
                "",
            ]
        )

    # Performance stats
    output.extend(
        [
            "**Performance:**",
            f"├─ Form: {player.form}",
            f"├─ Points per Game: {player.points_per_game}",
            f"├─ Total Points: {getattr(player, 'total_points', 'N/A')}",
            f"├─ Minutes: {getattr(player, 'minutes', 'N/A')}",
            "",
        ]
    )

    # Popularity
    if hasattr(player, "selected_by_percent"):
        output.extend(
            [
                "**Popularity:**",
                f"├─ Selected by: {getattr(player, 'selected_by_percent', 'N/A')}%",
                f"├─ Transfers in (GW): {getattr(player, 'transfers_in_event', 'N/A')}",
                f"├─ Transfers out (GW): {getattr(player, 'transfers_out_event', 'N/A')}",
                "",
            ]
        )

    # Season stats
    if hasattr(player, "goals_scored"):
        output.extend(
            [
                "**Season Stats:**",
                f"├─ Goals: {getattr(player, 'goals_scored', 0)}",
                f"├─ Assists: {getattr(player, 'assists', 0)}",
                f"├─ Clean Sheets: {getattr(player, 'clean_sheets', 0)}",
                f"├─ Bonus Points: {getattr(player, 'bonus', 0)}",
            ]
        )

    return "\n".join(output)


def format_team_details(team: dict[str, Any]) -> str:
    """Format team detailed information and strength ratings."""
    name = team.get("name", "Unknown")
    short_name = team.get("short_name", "UNK")

    output = [f"**{name} ({short_name})**", ""]

    if team.get("strength"):
        output.append(f"Overall Strength: {team['strength']}")

    if team.get("strength_overall_home") or team.get("strength_overall_away"):
        output.extend(
            [
                "",
                "**Overall Strength:**",
                f"Home: {team.get('strength_overall_home', 'N/A')}",
                f"Away: {team.get('strength_overall_away', 'N/A')}",
            ]
        )

    if team.get("strength_attack_home") or team.get("strength_attack_away"):
        output.extend(
            [
                "",
                "**Attack Strength:**",
                f"Home: {team.get('strength_attack_home', 'N/A')}",
                f"Away: {team.get('strength_attack_away', 'N/A')}",
            ]
        )

    if team.get("strength_defence_home") or team.get("strength_defence_away"):
        output.extend(
            [
                "",
                "**Defence Strength:**",
                f"Home: {team.get('strength_defence_home', 'N/A')}",
                f"Away: {team.get('strength_defence_away', 'N/A')}",
            ]
        )

    return "\n".join(output)


def format_gameweek_details(event: Any) -> str:
    """Format detailed gameweek information."""
    # Handle object or dict access if needed, assuming event is an object from bootstrap data
    is_current = getattr(event, "is_current", False)
    is_previous = getattr(event, "is_previous", False)
    is_next = getattr(event, "is_next", False)

    status_label = "Upcoming"
    if is_current:
        status_label = "Current"
    elif is_previous:
        status_label = "Previous"
    elif is_next:
        status_label = "Next"

    output = [
        f"**{event.name}**",
        f"Deadline: {event.deadline_time}",
        f"Status: {status_label}",
        f"Finished: {event.finished}",
        f"Released: {getattr(event, 'released', 'N/A')}",
        "",
    ]

    if event.finished:
        output.extend(
            [
                "**Statistics:**",
                f"Average Score: {event.average_entry_score}",
                f"Highest Score: {event.highest_score}",
                "",
            ]
        )

        # Note: top_element_info logic usually requires a separate name lookup
        # so we'll leave that to the caller to append if they have the name

    return "\n".join(output)


def format_manager_squad(
    team_name: str,
    player_name: str,
    team_id: int,
    gameweek: int,
    entry_history: dict[str, Any],
    picks: list[dict[str, Any]],
    players_info: dict[int, Any],
    active_chip: str | None = None,
    auto_subs: list[dict[str, Any]] = None,
) -> str:
    """Format a manager's squad for a specific gameweek."""

    output = [
        f"**{team_name}** - {player_name}" if player_name else f"**{team_name}**",
        f"Team ID: {team_id}",
        f"Gameweek {gameweek}",
        f"Points: {entry_history.get('points', 0)} | Total: {entry_history.get('total_points', 0)}",
        f"Overall Rank: {entry_history.get('overall_rank', 'N/A'):,}",
        f"Team Value: £{entry_history.get('value', 0) / 10:.1f}m | Bank: £{entry_history.get('bank', 0) / 10:.1f}m",
        f"Transfers: {entry_history.get('event_transfers', 0)} (Cost: {entry_history.get('event_transfers_cost', 0)}pts)",
        f"Points on Bench: {entry_history.get('points_on_bench', 0)}",
        "",
    ]

    if active_chip:
        output.append(f"**Active Chip:** {active_chip}")
        output.append("")

    starting_xi = [p for p in picks if p["position"] <= 11]
    bench = [p for p in picks if p["position"] > 11]

    output.append("**Starting XI:**")
    for pick in starting_xi:
        player = players_info.get(pick["element"], {})
        role = " (C)" if pick["is_captain"] else " (VC)" if pick["is_vice_captain"] else ""
        multiplier = f" x{pick['multiplier']}" if pick["multiplier"] > 1 else ""

        output.append(
            f"{pick['position']:2d}. {player.get('web_name', 'Unknown'):15s} "
            f"({player.get('team', 'UNK'):3s} {player.get('position', 'UNK')}) | "
            f"£{player.get('price', 0):.1f}m{role}{multiplier}"
        )

    output.append("\n**Bench:**")
    for pick in bench:
        player = players_info.get(pick["element"], {})
        output.append(
            f"{pick['position']:2d}. {player.get('web_name', 'Unknown'):15s} "
            f"({player.get('team', 'UNK'):3s} {player.get('position', 'UNK')}) | "
            f"£{player.get('price', 0):.1f}m"
        )

    # or we handle it if we pass the names.
    # For simplicity, let's assume the caller handles auto_subs appending
    # or we handle it if we pass the names.

    return "\n".join(output)


def format_difficulty_indicator(difficulty: int) -> str:
    """
    Format fixture difficulty as visual indicator.

    Args:
        difficulty: Difficulty rating (1-5)

    Returns:
        Visual difficulty indicator
    """
    return "●" * difficulty + "○" * (5 - difficulty)


def format_markdown_table_row(items: list[str], widths: list[int] | None = None) -> str:
    """
    Format a markdown table row with proper spacing.

    Args:
        items: List of cell contents
        widths: Optional list of column widths for padding

    Returns:
        Formatted markdown table row
    """
    if widths:
        padded = [str(item).ljust(width) for item, width in zip(items, widths, strict=True)]
        return "| " + " | ".join(padded) + " |"
    return "| " + " | ".join(str(item) for item in items) + " |"

"""
FPL MCP Prompts - Gameweek Analysis.

Prompts to analyze detailed match reports and provide transfer advice for a gameweek.
"""

from ..state import store
from ..tools import mcp
from ..tools.fixtures import (
    FindFixtureOpportunitiesInput,
    GetFixturesForGameweekInput,
    fpl_find_fixture_opportunities,
    fpl_get_fixtures_for_gameweek,
)


@mcp.prompt()
async def gameweek_analysis(gameweek: int | None = None) -> str:
    """
    Analyze detailed match reports for a specific gameweek.

    Provides a comprehensive analysis of all matches in a gameweek, highlighting
    key performers, tactical insights, and FPL implications based on detailed statistics.
    Also suggests transfer targets based on upcoming fixtures and form.

    Args:
        gameweek: Gameweek number to analyze (defaults to current gameweek if None)
    """
    if gameweek is None:
        gw_data = store.get_current_gameweek()
        if not gw_data:
            return "Error: Could not determine current gameweek."
        gameweek = gw_data.id

    # Fetch detailed fixtures
    fixtures_input = GetFixturesForGameweekInput(gameweek=gameweek, detailed=True)
    match_reports = await fpl_get_fixtures_for_gameweek(fixtures_input)

    # Fetch simple fixture difficulty context for next 5 gameweeks
    fixture_ops_input = FindFixtureOpportunitiesInput(num_gameweeks=5, max_teams=5)
    fixture_opportunities = await fpl_find_fixture_opportunities(fixture_ops_input)

    return f"""Analyze the following detailed match reports for Gameweek {gameweek}.

**Match Reports:**
{match_reports}

**Upcoming Fixture Context (Next 5 GWs):**
{fixture_opportunities}

**Analysis Objectives:**
1.  **Key Performers:** Identify the standout players based on goals, assists, and bonus points. Who is in top form?
2.  **Tactical Insights:** Are there any noticeable trends? (e.g., high-scoring games, defensive masterclasses, specific teams dominating).
3.  **FPL Implications:**
    -   **Buy:** Comparison of assets who performed well.
        -   **CRITICAL**: Cross-reference with Upcoming Fixture Context.
        -   Generally prioritize players with good upcoming fixtures.
        -   **EXCEPTION**: High-form elite players (fixture-proof) can be recommended even with tougher fixtures if their underlying stats are exceptional.
        -   Flag 'Trap' assets: players in bad teams who scored once but have terrible fixtures/stats.
    -   **Sell:** Notable failures or players who were benched/subbed early. Consider if it's a dip in form or a long-term issue.
    -   **Watchlist:** interesting differentials or returning players.
    -   **Analysis Depth**: When highlighting players, mention if their performance seems sustainable. Infer xG/xA quality from report descriptions if detailed stats suggest high involvement (e.g. many shots/key passes).
4.  **Upcoming Outlook:** Based on this performance, who looks essential for the next gameweek?

## 🔧 Tool Calls Strategy

1.  **Deep Dive**: Use `fpl_get_player_details(player_name=...)` to check full history and upcoming fixtures for any player who catches your eye.
2.  **Compare Options**: Use `fpl_compare_players(player_names=[...])` to decide between potential transfer targets.
3.  **Check Manager**: If analyzing a specific rival, use `fpl_get_manager_by_team_id`.

Provide a concise but deep analysis useful for an FPL manager making transfer decisions.
"""

"""
FPL MCP Prompts - League Analysis and Differentials.

Prompts guide the LLM in analyzing league standings, comparing
managers, and finding differential players.
"""

from ..tools import mcp


@mcp.prompt()
def compare_managers(league_id: int, gameweek: int, *manager_names: str) -> str:
    """
    Generate a prompt for comparing managers' teams in a league.

    This prompt guides the LLM to analyze differences in team selection,
    strategy, and performance between multiple managers.

    Args:
        league_id: ID of the league (from FPL URL)
        gameweek: Gameweek number to analyze
        *manager_names: Variable number of manager names (2-4 managers)
    """
    managers_str = ", ".join(manager_names) if manager_names else "{{manager1}}, {{manager2}}, ..."
    num_managers = len(manager_names) if manager_names else "2-4"

    return f"""Compare these managers' teams in league {league_id} for Gameweek {gameweek}: {managers_str}

**Comparison Framework:**

Analyze {num_managers} managers across multiple dimensions:

1. **Performance Summary:**
   For each manager:
   - Gameweek points scored
   - Overall rank
   - Total points for season
   - Transfers made and cost
   - Points left on bench

2. **Team Selection Analysis:**

   **Captain Choices:**
   - Who did each manager captain?
   - Captain points scored
   - Was it a differential or template choice?

   **Formation & Structure:**
   - Formation used (e.g., 3-4-3, 4-3-3)
   - Premium player allocation
   - Budget distribution

3. **Player Overlap Analysis:**

   **Common Players:**
   - Players owned by all managers
   - Template players (high ownership)
   - How many players in common?

   **Differential Picks:**
   - Unique players per manager
   - Which differentials performed well?
   - Which differentials flopped?

4. **Strategic Decisions:**

   **Chip Usage:**
   - Did anyone use a chip this gameweek?
   - Impact of chip usage on points

   **Transfer Strategy:**
   - Number of transfers made
   - Points hit taken (if any)
   - Transfer effectiveness

5. **Performance Drivers:**

   **Why did one manager outperform?**
   - Better captain choice?
   - Successful differentials?
   - Avoided blanks?
   - Chip usage?

   **Key Differences:**
   - Tactical variations
   - Risk vs safety approach
   - Budget allocation differences

6. **Bench Analysis:**
   - Points left on bench per manager
   - Bench strength comparison
   - Auto-substitutions made

7. **xGI-Based Differential Analysis:**

   For each unique differential pick:
   - **xGI Output**: Player's xGI/90 over last 5 GW
   - **xGI Delta**: Actual G+A minus xG+xA
     * Positive delta (+2+): Overperformed (lucky haul, may not repeat)
     * Negative delta (-2+): Underperformed (unlucky, due for improvement)
   - **Verdict**: Was the differential choice based on strong underlying stats or recency bias?

**Data Access:**

Step 1: Get league standings to find manager names and team IDs:
- Tool: `fpl_get_league_standings`
  - Parameters: league_id={league_id}
  - Returns: List of managers with their team_id, entry_name, player_name, and points

Step 2: Compare managers using one of these approaches:

**Option A - Individual manager analysis:**
- Tool: `fpl_get_manager_by_team_id`
  - Parameters:
    - team_id: [Team ID] (found in standings)
    - gameweek: {gameweek}
  - Returns: Detailed team sheet with starting XI, bench, captain, transfers, points

**Option B - Side-by-side comparison (General):**
- Tool: `fpl_compare_managers`
  - Parameters:
    - manager_names: ["Manager1", "Manager2"]
    - league_id: {league_id}
    - gameweek: {gameweek}
  - Returns: Comparison with common players, differentials, captain choices

**Option C - Deep Rival Analysis (Head-to-Head):**
- Tool: `fpl_analyze_rival`
  - Parameters:
    - my_team_id: [Your Team ID]
    - rival_team_id: [Rival Team ID]
    - gameweek: {gameweek}
  - Returns: Comprehensive stats, differentials, and threat assessment

**Additional data sources:**
- Resource `fpl://bootstrap/players` - All player details, ownership %, positions, prices
- Resource `fpl://current-gameweek` - Current gameweek status and deadline information
- For differentials: `fpl://player/{{{{player_name}}}}/summary` - Get xG, xA, xGI data

**Output Format:**
1. Performance summary table
2. Captain choices comparison
3. Common players list
4. Unique selections per manager
5. Key performance drivers analysis (include xGI context for differentials)
6. Strategic insights:
   - What worked well? (underlying stats or luck?)
   - What didn't work? (poor xGI or unlucky?)
   - Lessons learned
7. Recommendations for catching up (if behind)"""


@mcp.prompt()
def find_league_differentials(league_id: int, max_ownership: float = 30.0) -> str:
    """
    Generate a prompt for finding differential players in a league.

    This prompt guides the LLM to identify low-owned players that could
    provide a competitive advantage in a specific league.

    Args:
        league_id: ID of the league to analyze
        max_ownership: Maximum ownership % to consider as differential (default: 30%)
    """
    return f"""Find differential players for competitive advantage in league {league_id}.

**Differential Analysis Framework:**

1. **Definition:**
   Differentials are players owned by <{max_ownership}% of managers in your league
   who have strong potential for points.

2. **League Context Analysis:**
   - Total managers in league
   - Current league standings
   - Template players (high ownership)
   - Common captain choices

3. **Differential Categories:**

   **Premium Differentials (£9m+):**
   - High-priced players with low league ownership
   - Potential for big hauls
   - Higher risk but higher reward

   **Mid-Price Differentials (£6-9m):**
   - Value picks with good fixtures
   - Consistent performers
   - Lower risk, steady returns

   **Budget Differentials (<£6m):**
   - Enablers with attacking potential
   - Rotation risks but cheap
   - Good for bench options

4. **Evaluation Criteria (xGI-Based):**
   For each differential candidate:

   **Primary Metrics:**
   - **xGI/90**: Expected goal involvements per 90 minutes (last 5 GW)
     * >0.6 = Elite differential (rare but high upside)
     * 0.4-0.6 = Strong differential (good balance of risk/reward)
     * 0.2-0.4 = Budget differential (acceptable for cheap options)
     * <0.2 = Avoid (poor underlying output)

   - **xGI Delta**: Actual G+A minus xG+xA
     * Negative delta (-2+): Unlucky, prime differential opportunity (buy low)
     * Near zero: Performing to expectation
     * Positive delta (+2+): Lucky, avoid (regression risk)

   **Secondary Metrics:**
   - Upcoming fixture difficulty (next 4-6 GW)
   - Minutes played % (rotation risk if <70%)
   - Injury status
   - League ownership % vs global ownership %
   - Price and value

5. **Strategic Recommendations:**

   **When to use differentials:**
   - Chasing league leaders (need to take risks)
   - Good fixture runs ahead
   - Template players have tough fixtures

   **When to avoid differentials:**
   - Leading the league (play it safe)
   - Differential has injury concerns
   - Rotation risk too high

6. **Risk Assessment:**
   - High Risk: Low ownership, rotation risk, tough fixtures
   - Medium Risk: Moderate ownership, some rotation, mixed fixtures
   - Low Risk: Decent ownership, nailed on, good fixtures

**Data Access:**
- Use tool `fpl_get_league_standings` with league ID - League ownership patterns
- Tool `fpl_get_top_performers` - Identify current form players to find differential opportunities
- `fpl://bootstrap/players` - All players with ownership
- `fpl://player/{{{{player_name}}}}/summary` - Detailed player analysis
- `fpl://team/{{{{team_name}}}}/fixtures/{{{{num_gameweeks}}}}` - Fixture difficulty (default 5 GWs)

**Output Format:**
1. League template analysis (most owned players)
2. Differential candidates by price bracket:
   - Premium differentials
   - Mid-price differentials
   - Budget differentials
3. For each differential:
   - League ownership %
   - Overall ownership %
   - Form and fixtures
   - Risk level
   - Recommendation
4. Strategic advice:
   - Best differentials for your situation
   - Timing for bringing them in
   - Risk vs reward assessment"""

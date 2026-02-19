"""
FPL MCP Prompts - Chip Strategy Recommendations.

Prompts guide the LLM in analyzing chip strategies and timing
for optimal gameweek selection using quantitative analysis.
"""

from ..tools import mcp


@mcp.prompt()
def recommend_chip_strategy(team_id: int) -> str:
    """
    Analyze chip strategy with xGI-based metrics and EV calculations.

    This prompt guides the LLM to recommend optimal chip timing using
    quantitative expected value analysis rather than subjective assessments.

    Args:
        team_id: FPL team ID of the manager to analyze
    """
    return f"""Analyze available chips for team ID {team_id} and recommend optimal timing strategy.

**Chip Analysis Framework:**

For each available chip, provide strategic recommendations:

1. **🃏 WILDCARD Strategy:**
   - **Optimal Timing**: Use 1 GW before Double Gameweeks (DGW)
   - **Squad Health Check**: Count injured/unavailable players
   - **Trigger Points**:
     * DGW detected within next 5 gameweeks → HIGH priority
     * 3+ players injured/unavailable → HIGH priority
     * Major squad overhaul needed (5+ underperformers with xGI/90 <0.2) → MEDIUM priority
   - **Pro Tip**: Maximize new players' potential by wildcarding before DGW

2. **🎯 FREE HIT Strategy:**
   - **Optimal Timing**: Save for Blank Gameweeks (BGW)
   - **BGW Detection**: When <60% of teams play (typically <12 teams)
   - **BGW Scarcity Modeling**:
     * BGW with 4-6 teams playing → EXTREME value (limited options) → HIGH priority
     * BGW with 8-12 teams playing → MODERATE value → MEDIUM priority
     * DGW without BGW → LOW priority (backup option only)
   - **Pro Tip**: Best used when few teams play, allows one-week team transformation

3. **⭐ TRIPLE CAPTAIN Strategy:**
   - **Optimal Timing**: Premium players (£9m+) in DGW
   - **Analysis Required (xGI-Based)**:
     * Identify premium players in squad
     * For each premium, calculate **TC Expected Points**:
       - Base: xGI/90 × 180 minutes (DGW) = Expected goal involvements
       - Convert xGI to points: (xGI × 6 avg pts per involvement)
       - Multiply by 3 (captain) = TC Expected Points
     * Add fixture bonus:
       - Easy fixtures (FDR <2.5): +20%
       - Home fixtures: +15%
   - **Trigger Points**:
     * Premium has DGW + xGI/90 >0.7 → HIGH priority (expect 30+ TC pts)
     * Premium has easy home fixture (single GW) + xGI/90 >0.8 → MEDIUM priority (expect 15+ TC pts)
     * No premiums with xGI/90 >0.6 → LOW priority
   - **Pro Tip**: Maximum impact on high xGI players in double gameweeks

4. **📊 BENCH BOOST Strategy:**
   - **Optimal Timing**: When bench players have DGW

   **Bench Quality Check (xGI-Based):**
   For each bench player:
   - **xGI/90**: Expected output per 90 minutes
   - **Minutes Security**: % of minutes played last 5 GW (need >60% for reliability)
   - **Expected Points (DGW)**:
     * Attackers/Mids: (xGI/90 × 180 mins DGW ÷ 90) × 6 pts per involvement + 4 pts (2× appearance)
     * Defenders: (xGI/90 × 180 ÷ 90) × 6 + Clean Sheet Odds × 8 pts (2 CS × 4pts) + 4 pts
     * GKP: Clean Sheet Odds × 8 pts + 4 pts (2× appearance)

   **Bench Boost EV Calculation:**
   ```
   Total Bench EV = Sum of 4 bench players' expected points
   ```

   **Trigger Points**:
   - **Total Bench EV >25 pts in DGW** → HIGH priority (excellent bench boost)
   - **Total Bench EV 18-25 pts** → MEDIUM priority (good bench boost)
   - **Total Bench EV <18 pts** → LOW priority (weak bench, improve first)
   - **2+ bench players have DGW** → Required for consideration

   **Bench Improvement Suggestions** (if weak):
   - Target players with xGI/90 >0.15 under £5.5m
   - Prioritize nailed-on starters (minutes >70%) in teams with upcoming DGW

   - **Pro Tip**: Maximize returns when bench has DGW + strong xGI output

**Fixture Analysis (Next 10 Gameweeks):**
Scan for:
- **Double Gameweeks (DGW)**: Teams playing twice in one GW
- **Blank Gameweeks (BGW)**: <60% of teams playing
  * Count teams playing each GW to assess scarcity
- Pattern recognition for optimal chip timing

**Priority Ranking:**
Sort recommendations by:
- 🔴 HIGH: Immediate opportunity or urgent need (DGW within 3 GW, bench boost EV >25)
- 🟡 MEDIUM: Good opportunity within 5 gameweeks (bench boost EV 18-25)
- 🟢 LOW: No immediate opportunity, save for later (wait for DGW/BGW)

**Data Access:**
Use these tools and resources to gather chip and squad data:
- Tool `fpl_get_manager_chips` with team_id={team_id} - Get used and available chips with timing
- Resource `fpl://manager/{{{team_id}}}/chips` - Chip usage summary
- Tool `fpl_get_manager_squad` with team_id={team_id} - Squad composition for chip analysis
- Resource `fpl://current-gameweek` - Current gameweek info
- Resource `fpl://gameweek/{{{{gw}}}}/fixtures` - Fixtures for each upcoming GW to detect DGWs/BGWs
- Resource `fpl://player/{{{{player_name}}}}/summary` - Premium player xGI analysis

**Output Format:**
1. Available chips list
2. For each chip:
   - Strategic recommendation
   - Specific gameweek suggestion (if applicable)
   - **Quantitative Justification**:
     * Triple Captain: Expected TC points
     * Bench Boost: Total Bench EV calculation
   - Priority level with reasoning
   - Pro tip
3. Upcoming fixture overview (next 6 GWs)
   - Highlight DGWs and BGWs
   - Team counts per gameweek (for BGW scarcity assessment)
4. If Bench Boost weak: Specific improvement targets (players with xGI/90 >0.15, <£5.5m, minutes >70%)"""

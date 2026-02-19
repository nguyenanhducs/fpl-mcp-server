"""
FPL MCP Prompts - Squad Performance Analysis.

Prompts guide the LLM in analyzing squad performance over recent gameweeks
using underlying metrics and regression analysis.
"""

from ..tools import mcp


@mcp.prompt()
def analyze_squad_performance(team_id: int, num_gameweeks: int = 5) -> str:
    """
    Analyze squad performance using xGI-based metrics and regression analysis.

    This prompt guides the LLM to identify underperforming/overperforming players
    using underlying stats (xG, xA, xGI) rather than retrospective points.

    Args:
        team_id: FPL team ID of the manager to analyze
        num_gameweeks: Number of recent gameweeks to analyze (default: 5)
    """
    return f"""Analyze FPL squad performance for team ID {team_id} over the last {num_gameweeks} gameweeks.

**OBJECTIVE: Create a PRO-LEVEL transfer strategy using Underlying Stats (xGI), Fixture Swings, and Chip Strategy.**

---

## 🏗️ **Step 1: Strategic Context (The "Manager's Eye")**

Before analyzing players, assess the macro state of the squad:
1.  **Financial Health:**
    - Check `bank` balance. Can we afford luxury upgrades?
    - Check `value` trends.
2.  **Chip Status:**
    - Which chips are available? (Wildcard, Free Hit, Bench Boost, Triple Captain)
    - **Strategy:** If Wildcard is available and squad has >4 "issues", suggest Wildcard.
3.  **Fixture Scan (Next 5 GW):**
    - Identify teams with **Major Fixture Swings** (turning Good → Bad or Bad → Good).
    - *Target:* Players from teams entering a "green run".
    - *Avoid:* Players from teams entering a "red run".

---

## 📊 **Step 2: Player Performance Analysis (xGI Model)**

Analyze each player using the **xGI Regression Model** (Output vs Expected):

### **The Regression Framework:**
- **xGI Delta** = `Actual G+A` - `Expected GI (xG + xA)`
- **Interpretation:**
    - **Huge Overperformance (+3.0+)**: *Elite Finisher* (e.g., Salah/Son) OR *Luck*? -> **HOLD** unless fixtures turn terrible.
    - **Significant Underperformance (-2.0 to -3.0)**: *Unlucky*. If xGI is high (>0.5/90), **KEEP** or even **CAPTAIN**.
    - **Poor Underlying (xGI < 0.2/90)**: *Ghosting*. Regardless of points, this is a **SELL** priority.

### **Categorization:**
- 🛡️ **Defensive Rocks**: Clean sheet potential + BP system appeal.
- 🚜 **Workhorses**: Consistent xGI (0.4-0.6), nailed minutes.
- 💣 **Explosive Differentials**: High xGI but low ownership (<10%).
- 📉 **Dead Wood**: Low xGI + Bad Fixtures + Rotation Risk.

---

## 🔄 **Step 3: Transfer Planning (The "Next 3 Moves")**

Instead of just "Buy X", provide a 3-Gameweek Plan:

**Scenario A: The Surgery** (3+ Issues)
- **GW{num_gameweeks + 1}:** Sell [Player A] -> Buy [Target A] (Reason: Fixture Swing)
- **GW{num_gameweeks + 2}:** Roll Transfer / Sell [Player B]
- **Long-term:** target [Premium Asset] in GW{num_gameweeks + 3}

**Scenario B: The Luxury Move** (Squd is fine)
- Upgrade specific position or build bank for future premium.

**Prioritization Rules:**
1.  **Injuries/Suspensions**: Immediate priority.
2.  **Fixture Cliffs**: Selling players hitting a run of red fixtures.
3.  **xGI Underperformers**: Selling players with low xGI (not just low points).

---

## 💡 **Recommendations & Targets**

For each position (GKP, DEF, MID, FWD), recommend **Replacement Targets** based on:
1.  **Fixture Swing**: Teams with Easiest Next 4 Games.
2.  **Underlying Data**: Top xGI performers in those teams.
3.  **Price Structure**: Must fit within budget (Bank + Sale Price).

---

## 🔧 **Tool Calls Strategy**

1.  **Get Context**: `fpl_get_manager_by_team_id` (Squad, Bank, Rank) AND `fpl_get_manager_chips`.
2.  **Scan Landscape**: `fpl_find_fixture_opportunities` (Identify teams to target).
3.  **Analyze Squad**: `fpl_get_player_details` for current squad loop.
4.  **Find Replacements**: `fpl_get_top_performers` (Cross-reference with Fixture Opportunities).
5.  **Captaincy**: `fpl_get_captain_recommendations` for immediate GW.

---

## ⚠️ **Veteran Advice**
- **Don't chase last week's points.** Look at who is *about* to score.
- **Roll transfers** if the squad is healthy. 2 FTs is a superpower.
- **Value < Points.** Don't hold a falling player just to save 0.1m if they aren't scoring.
"""

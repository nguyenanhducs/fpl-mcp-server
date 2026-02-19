"""
FPL MCP Prompts - Team Selection.

Prompts guide the LLM in selecting the optimal starting XI and bench ordering
for a specific gameweek.
"""

from ..tools import mcp


@mcp.prompt()
def select_team(team_id: int, gameweek: int | None = None) -> str:
    """
    Optimize Starting XI and Bench using fixture analysis and player status.

    This prompt guides the LLM to choose the best starting lineup and bench order
    based on fixture difficulty, player availability, and form.

    Args:
        team_id: Manager's FPL team ID
        gameweek: Target gameweek (defaults to current/next if None)
    """
    gameweek_text = f"gameweek {gameweek}" if gameweek else "the upcoming gameweek"
    gameweek_display = f"{gameweek}" if gameweek else "Upcoming"

    return f"""Optimize the Starting XI and Bench for team ID {team_id} in {gameweek_text}.
**OBJECTIVE: Select the highest-scoring Starting XI and optimize Bench ordering.**

---

## 🚦 **Workflow & Logic**

1.  **Get Squad & Status**: Fetch manager's team and check for injuries/suspensions.
2.  **Analyze Fixtures**: Evaluate opponent strength (Attack vs Defense).
3.  **Select Lineup**: Best 11 players regardless of formation (valid formations only: 3-4-3, 3-5-2, 4-4-2, 4-3-3, 5-3-2, etc.).

---

## 🧠 **Selection Strategy**

### **1. Starting XI Priority (Must Starts)**
*   **Premiums**: Always start (e.g., Salah, Haaland) unless injured.
*   **Form Attackers**: Start players with xGI > 0.5 recently, even with tricky fixtures (Attack beats Defense).
*   **Defenders with Clean Sheet Potential**: Start defenders vs Bottom 5 Attacks.
*   **Attacking Defenders**: Start defenders with high xA (e.g., Trent, Porro) regardless of fixture, unless playing Man City/Arsenal away.

### **2. Bench Decisions (The "Dilemma" Area)**
*   **Bench Defenders vs Top 6 Attack**: If you have a decent backup mid/fwd, bench the defender playing a top team.
*   **Bench Rotation Risks**: If a player is a massive rotation risk (e.g., Pep Roulette), they can still start if the ceiling is high, but have a secure #1 bench sub ready.
*   **Bench Injured/Suspended**: Move to slots #2 and #3.

### **3. Optimizing Bench Order**
*   **Slot 1**: **Highest Ceiling**. The player who can score 10+ points if they come on (e.g., Explosive Winger vs tough defense > 2pt Defender).
*   **Slot 2**: **Safety**. The 90-min defender who guarantees 1-2 points if Slot 1 doesn't play.
*   **Slot 3**: **Fodder/Red Flags**.

---

## 📝 **Output Format:**

**Recommended Lineup for Gameweek {gameweek_display}**

*(Formation: [e.g. 3-4-3])*

 **Defense**
*   **GK**: [Name] (vs [Opponent])
    *   *Rationale*: [One line reason, e.g., "Opponent lowest xG in league"]
*   **DEF**: [Name] (vs [Opponent])
*   **DEF**: [Name] (vs [Opponent])
*   ...

**Midfield**
*   **MID**: [Name] (vs [Opponent])
*   **MID**: [Name] (vs [Opponent])
*   ...

**Forwards**
*   **FWD**: [Name] (vs [Opponent])
*   ...

**©️ Captain**: [Name] (Run `recommend_captain` for detailed analysis)
**⚡ Vice-Captain**: [Name] (Secure starter with highest ceiling)

---

**Bench (Critical Order)**
1.  **[Name]** ([Pos] vs [Opponent])
    *   *Why #1?*: [e.g., "High ceiling upside despite tough fixture"]
2.  **[Name]** ([Pos] vs [Opponent])
3.  **[Name]** ([Pos] vs [Opponent])
4.  **GK [Name]** ([Pos] vs [Opponent])

---

## ⚠️ **Transfer Alert (Optional)**
*   If the team has **>2 non-playing players** (Red flags/Bench fodder) in the starting XI/Bench 1:
    *   **Recommendation**: "Consider a transfer for [Player Name] → [Replacement Tool]"

## 🔧 **Tool Usage**
1.  `fpl_get_manager_by_team_id(team_id={team_id})` → Get squad.
2.  `fpl_get_gameweek_fixtures(gameweek={gameweek})` → Get matchups.
3.  `fpl_get_player_summary(player_id=...)` -> Check status if flagged.

**Begin Selection Analysis.**
"""

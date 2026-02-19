"""
FPL MCP Prompts - Player Comparison and Analysis.

Prompts guide the LLM in comparing multiple players side-by-side
for informed transfer decisions.
"""

from ..tools import mcp


@mcp.prompt()
def compare_players(*player_names: str) -> str:
    """
    Compare players using underlying metrics and probability-based projections.

    This prompt prioritizes xG/xA/xGI over retrospective points, identifies positive/negative
    regression candidates, and accounts for ownership context.

    Args:
        *player_names: 2-5 player names to compare
    """
    players_str = ", ".join(player_names) if player_names else "{{player1}}, {{player2}}, ..."

    return f"""Compare these FPL players: {players_str}

**CRITICAL: Prioritize underlying stats over retrospective points. Identify regression candidates.**

---

## 📊 **Comparison Matrix**

For each player, extract and compare:

### **1. Underlying Output Metrics (PRIMARY)**
- **npxG (Non-Penalty Expected Goals)**: Total over last 5 GW + per 90 min
- **xA (Expected Assists)**: Total over last 5 GW + per 90 min
- **xGI (Expected Goal Involvements)**: npxG + xA over last 5 GW + per 90 min
- **Big Chances Received**: Count over last 5 GW (proxy for service quality)
- **Touches in Penalty Box**: Per 90 min (attackers only)
- **Defensive Contribution**: Per 90 min (defenders/mids with defensive role)

### **2. Regression Analysis (CRITICAL)**
Calculate **xGI Delta** for each player:
- `Actual G+A (last 5 GW)` MINUS `xG + xA (last 5 GW)`
- **Positive Delta (+2 to +4)**: Player is OVERPERFORMING → Sell risk (negative regression incoming)
- **Negative Delta (-2 to -4)**: Player is UNDERPERFORMING → BUY OPPORTUNITY (positive regression likely)
- **Near Zero (-1 to +1)**: Performing to expectation → Stable asset

### **3. Price Efficiency (Secondary)**
- **Cost per xGI/90**: `Price ÷ (xGI per 90 minutes)`
  *Lower = better value*
- **Recent Price Changes**: +/-0.1m in last 7 days?
  *Rising price = urgency to buy before lockout*
- **Transfer Delta (last 3 GW)**: Net transfers in/out
  *Rising ownership = potential price rise = urgency*

### **4. Fixture Analysis (4-6 GW Horizon)**
For next **6 gameweeks**:
- **Average FDR**: Simple mean of fixture difficulty (1-5)
- **Fixture Swing Detection**:
  - If FDR drops by >1.0 after GW[X], note: "Target for GW[X] transfer"
  - If DGW detected, FLAG with 🔥
- **Home/Away Balance**: Defenders favor HOME fixtures (higher clean sheet odds)

### **5. Ownership Context (Differential Math)**
- **Global Ownership %**: From bootstrap data
- **Effective Ownership (EO) Estimate**:
  - If Top 100K avg = 25% but global = 15%, EO ≈ 25% (use Top 100K proxy)
  - **Template Players**: EO >40% → Must own for *rank protection*
  - **Differentials**: EO <15% → High risk, high reward if chasing rank

### **6. Availability & Minutes Security**
- **Status**: Available / Doubtful / Injured / Suspended
- **Minutes Played (last 5 GW)**: Total + % of available minutes
  *<75% of possible minutes = rotation risk*
- **Benchings (last 5 GW)**: Count of games started on bench

---

## 🎯 **Output Format**

### **1. Quick Comparison Table**
Present side-by-side:

| Metric | {players_str} |
|--------|{"-" * (len(players_str) + 2)}|
| **npxG (5 GW)** | ... |
| **xA (5 GW)** | ... |
| **xGI (5 GW)** | ... |
| **xGI Delta** | ... (🔴 overperforming / 🟢 underperforming / ⚪ stable) |
| **Cost/xGI per 90** | ... |
| **Avg FDR (6 GW)** | ... |
| **Ownership %** | ... |
| **Minutes (5 GW)** | ... / 450 possible |

### **2. Regression Insights**
- **Positive Regression Targets** (underperforming xGI): [List players with negative delta]
  → *"Buy low, sell high" candidates*
- **Negative Regression Risks** (overperforming xGI): [List players with positive delta]
  → *Consider selling before decline*

### **3. Fixture Advantage**
- **Best Fixtures (Next 6 GW)**: [Player with lowest avg FDR]
- **Fixture Swing Alert**: [Any player with FDR drop >1.0]
- **DGW Candidates**: [Flag any players in teams with DGW detected]

### **4. Recommendation**

**Best Overall Bet:**
[Player name] — Justification using:
- xGI/90 dominance
- Positive regression potential (if negative xGI delta)
- Fixture advantage
- Price efficiency

**Differential Pick (if chasing rank):**
[Player with <15% ownership + strong xGI]

**Avoid:**
[Player with negative regression risk OR tough fixtures OR rotation risk]

---

## 🔧 **Tool Calls**

1. **`fpl_compare_players(player_names=[p1, p2, ...])`** → Get comprehensive stats, fixtures, history side-by-side
   *Provides: xG, xA, xGI, minutes, goals, assists, upcoming fixtures*
2. **`fpl://bootstrap/players`** → Get ownership %, price, transfer trends
   *Provides: selected_by_percent, now_cost, transfers_in/out_event*
3. **`fpl_get_top_performers(num_gameweeks=5)`** → Benchmark against top xGI players

---

## ⚠️ **Critical Rules**

1. **NEVER recommend based on "form" or "PPG" alone** → Use xGI/90 + xGI delta
2. **ALWAYS calculate xGI Delta** → Regression is the #1 alpha source
3. **FLAG price rise urgency** → If transfers_in >50K last 3 days, note "Buy before rise"
4. **Context ownership** → Template (>40%) vs. Differential (<15%)
"""

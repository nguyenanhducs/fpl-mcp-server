"""
FPL MCP Prompts - Transfer Recommendations.

Prompts guide the LLM in analyzing transfer strategies based on
available free transfers and squad needs.
"""

from ..tools import mcp


@mcp.prompt()
def recommend_transfers(team_id: int, free_transfers: int = 1) -> str:
    """
    Identify targets using xGI delta, fixture swings, and price urgency.

    Args:
        team_id: Manager's FPL team ID
        free_transfers: Available free transfers
    """
    return f"""Analyze squad {team_id} and recommend ELITE-LEVEL transfer strategy.

**FRAMEWORK: Prioritize xGI underperformers (sell) → xGI overperformers with good fixtures (buy) → Price rise urgency.**

---

## 🔍 **STEP 1: Identify Transfer-Out Candidates**

For each squad player, calculate **SELL PRIORITY SCORE**:

### **Automatic Triggers (+100 pts each)**
- ❌ Injured / Suspended / Flagged as doubtful
- ❌ DNP last 2 games (did not play)

### **Regression Risk (+30-50 pts)**
- **xGI Delta (last 5 GW)**: Actual G+A MINUS xG+xA
  - **+3 or higher**: +50 pts (*Massively overperforming → sell before regression*)
  - **+2 to +2.9**: +30 pts (*Moderately overperforming*)

### **Fixture Deterioration (+20-40 pts)**
- **Next 4 GW Avg FDR**:
  - **>4.0**: +40 pts (*Nightmare run*)
  - **3.5-4.0**: +20 pts (*Tough fixtures*)

### **Minutes Risk (+25 pts)**
- **Last 5 GW minutes** <60% of possible → +25 pts (*Rotation risk*)

### **Price Drop Urgency (+15 pts)**
- **Net transfers out >5% of ownership** in last 3 days → +15 pts (*Price drop imminent*)

---

## 🎯 **STEP 2: Rank Transfer-Out Targets**

Sort squad players by **SELL PRIORITY SCORE** (descending). Present top 5:

| Player | Sell Priority | Reason Breakdown |
|--------|---------------|------------------|
| [Name] | 130 | ❌ Injured + 🔴 FDR 4.2 next 4 GW |
| [Name] | 80 | 🔴 xGI Delta +3.5 (overperforming) + Tough fixtures |
| ... | ... | ... |

**Urgency Tiers:**
- 🚨 **URGENT (100+ pts)**: Transfer out THIS gameweek (injured/suspended)
- ⚠️ **HIGH (50-99 pts)**: Transfer out within 2 GW (regression risk + fixtures)
- 🟡 **MEDIUM (30-49 pts)**: Consider if spare FT available
- 🟢 **LOW (<30 pts)**: Monitor, no action needed

---

## 💰 **STEP 3: Identify Transfer-In Targets**

Search for players matching:

### **Positive Regression Candidates (Priority #1)**
Using `fpl_get_top_performers(num_gameweeks=5)`:
- Filter for **xGI Delta <-2.0** (underperforming their xG+xA by 2+ goal involvements)
  → *These are "unlucky" players due for points explosion*
- Exclude if: Injured, rotation risk (minutes <60%), or FDR >3.5 next 4 GW

### **Fixture Swing Beneficiaries (Priority #2)**
- Players in teams with **FDR swing** (rolling avg drops >1.0 starting next GW)
- OR players with **DGW in next 4 GW** 🔥

### **Price Rise Opportunities (Priority #3)**
- Players with **net transfers in >100K last 3 days** → Price rise imminent
  → *Buy before 0.1m increase locks you out*

### **Budget Constraints**
- Max price: `[Current player's selling price + £X.Xm ITB]`

---

## 📊 **STEP 4: Transfer Strategy by Free Transfers**

### **{free_transfers} Free Transfer(s) Available:**

{
        '''
🔴 **0 Free Transfers** — Only take a -4 hit if:
- Player is injured/suspended (guaranteed 0 pts)
- Replacement has DGW (expected +8 pts minimum)
- Replacement expected to outscore by 6+ pts (break even + profit)
- **Otherwise**: Bank the GW, take 2 FT next week
'''
        if free_transfers == 0
        else ""
    }

{
        '''
🟡 **1 Free Transfer** — Decision tree:
- **If 🚨 URGENT issue exists** (injured player): Use FT to fix
- **If no urgent issue**: Bank FT → Next week you'll have 2 FT (more flexibility)
- **Exception**: DGW in next 2 GW → Use FT to bring in DGW player now
'''
        if free_transfers == 1
        else ""
    }

{
        '''
🟢 **2 Free Transfers** — Optimal flexibility:
- Address top 2 **SELL PRIORITY** players (unless both are LOW tier)
- Don't waste FTs on sideways moves (similar xGI/90, no fixture improvement)
- Remember: FTs don't bank beyond 2 → USE THEM or LOSE THEM
'''
        if free_transfers >= 2
        else ""
    }

---

## 🎯 **STEP 5: Recommended Transfers**

### **Transfer Out:**
1. **[Player Name]** (Sell Priority: [Score])
   *Reason*: [injury / xGI overperformance / fixtures]
   *Urgency*: [URGENT / HIGH / MEDIUM]

### **Transfer In:**
1. **[Player Name]** (£X.Xm)
   *Why*: xGI Delta -2.8 (underperforming) + FDR 2.1 next 4 GW + Rising (150K transfers in)
   *Expected Impact*: [X.X xGI/90 vs current player's Y.Y]

### **Points Hit Economics:**
- If recommending -4 hit:
  → *"[New player] expected to outscore [old player] by 6+ pts based on xGI/90 + fixtures"*

---

## 🔧 **Tool Calls**

1. `fpl_get_manager_by_team_id(team_id={team_id})` → Current squad with transfer context
2. `fpl_get_top_performers(num_gameweeks=5)` → Find high xGI players for replacements
3. Use `fpl_analyze_transfer(player_out=..., player_in=...)` to validate your top priority move.
4. For other candidates:
   - `fpl://player/{{{{name}}}}/summary` → xG, xA, fixtures, status
5. `fpl://bootstrap/players` → Price, ownership, transfer trends

---

## ⚠️ **Critical Rules**

1. **Prioritize xGI Delta** over form/PPG → Regression is alpha
2. **Never chase last week's points** → Use xGI to predict NEXT week's points
3. **Account for price rise windows** → Buying before rise = free 0.1m
4. **DGW overrides everything** → Double fixtures = double xGI opportunity
"""

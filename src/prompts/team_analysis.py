"""
FPL MCP Prompts - Team Fixture Analysis.

Prompts guide the LLM in analyzing team fixtures and identifying
optimal times to invest in or avoid team assets using fixture swing methodology.
"""

from ..tools import mcp


@mcp.prompt()
def analyze_team_fixtures(team_name: str, num_gameweeks: int = 6) -> str:
    """
    Detect FDR trend shifts to time transfers optimally.

    Accounts for:
    - Fixture difficulty horizon (4-6 GW)
    - DGW/BGW detection
    - Home/away xG splits
    - "Green arrow" timing (when to invest)

    Args:
        team_name: Team to analyze
        num_gameweeks: Fixture horizon (default: 6 for trend detection)
    """
    return f"""Analyze {team_name}'s fixtures for OPTIMAL TRANSFER TIMING using FIXTURE SWING methodology.

**OBJECTIVE: Identify "green arrow" periods (FDR improves) to time {team_name} asset acquisition.**

---

## 📅 **Fixture Difficulty Assessment (Next {num_gameweeks} GW)**

For each upcoming fixture:

### **1. Opponent Strength Proxy**
Instead of static FDR (1-5), use:
- **Opponent xGC (Expected Goals Conceded) per game** → Higher xGC = weaker defense = favorable for attackers
- **Opponent xGA (Expected Goals Against) per game** → Lower xGA = weaker attack = favorable for defenders

*Note: If xGC/xGA data unavailable, fall back to FDR but note as "proxy only"*

### **2. Home/Away Context**
For each fixture, note:
- **{team_name} Home/Away**
- **Historical Home/Away xG**: {team_name}'s average xG at home vs. away
  *(Some teams like Newcastle are ELITE at home, average away)*

### **3. Double/Blank Gameweek Detection**
- **DGW**: If {team_name} plays TWICE in any GW → 🔥 **FLAG FOR CHIP STRATEGY**
- **BGW**: If {team_name} BLANKS (no fixture) → ⚠️ **AVOID or FREE HIT**

---

## 📈 **Fixture Swing Analysis (CRITICAL)**

Calculate **rolling 3-GW average FDR**:

| GW | Opponent | FDR | Rolling 3-GW Avg FDR |
|----|----------|-----|----------------------|
| 23 | Liverpool (H) | 4 | 3.7 |
| 24 | Bournemouth (A) | 2 | 3.3 |
| 25 | Luton (H) | 1 | 2.3 👈 **SWING DETECTED** |
| 26 | Fulham (A) | 2 | 1.7 |

**SWING LOGIC:**
- **Green Arrow** 🟢: Rolling avg drops by >1.0 → **OPTIMAL BUY WINDOW**
  → *"Transfer in {team_name} assets before GW[X] to maximize good fixtures"*
- **Red Arrow** 🔴: Rolling avg increases by >1.0 → **SELL WINDOW**
  → *"Avoid {team_name} assets during GW[X]-[Y]"*

---

## 🎯 **Strategic Recommendations**

### **For Attacking Assets (FWD/MID)**
1. **Best Acquisition Window**: GW[X] (before fixture swing to easy run)
   *Rationale: FDR drops from [avg] to [avg] starting GW[X+1]*
2. **Captaincy Windows**: GW[Y], GW[Z] (lowest FDR + home fixtures)
3. **Avoid Period**: GW[A]-[B] (FDR >3.5 avg)

### **For Defensive Assets (DEF/GKP)**
1. **Clean Sheet Windows**: GW[X], GW[Y] (opponent xGA <1.0 + home fixture)
   *Note: Home fixtures ~15% more likely for clean sheets*
2. **Bench These Weeks**: GW[Z] (facing Man City/Liverpool/Arsenal away)

### **DGW/BGW Impact**
- **If DGW Detected in GW[X]**:
  → Priority for Bench Boost / Triple Captain
  → Bring in {team_name} assets on GW[X-1] wildcard
- **If BGW Detected in GW[Y]**:
  → Free Hit opportunity OR transfer out before GW[Y]

---

## 📊 **Overall Fixture Run Classification**

- **GREEN (Favorable)**: Avg FDR <2.5 over {num_gameweeks} GW
  → *"Strong buy window for {team_name} assets"*
- **AMBER (Moderate)**: Avg FDR 2.5-3.5
  → *"Selective buy — premium assets only"*
- **RED (Difficult)**: Avg FDR >3.5
  → *"Avoid {team_name} assets OR sell before this period"*

**Current Classification**: [GREEN/AMBER/RED] (Avg FDR: [X.X])

---

## 🔧 **Tool Calls**

Use: `fpl_analyze_team_fixtures(team_name="{team_name}", num_gameweeks={num_gameweeks})`
For broader analysis (finding ANY team with good fixtures), use `fpl_find_fixture_opportunities`.
Enrich with: `fpl://bootstrap/teams` for opponent strength proxy (if xGC not available, use team strength rank)

---

## ⚠️ **Critical Rules**

1. **ALWAYS detect fixture swings** → Rolling 3-GW FDR changes >1.0
2. **FLAG all DGW/BGW** → These override normal fixture logic
3. **Account for home/away splits** → Especially for defensive assets
"""

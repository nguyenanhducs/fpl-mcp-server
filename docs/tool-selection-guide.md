# Tool Selection Guide

This guide provides a comprehensive reference to all available tools, resources, and prompts in the FPL MCP Server.

## Quick Navigation

- [Tools](#tools) - 19 interactive functions for FPL analysis
- [Resources](#resources) - 4 URI-based data endpoints
- [Prompts](#prompts) - 10 structured analysis templates

---

## Tools

Interactive functions that perform specific FPL analysis tasks. All tools accept structured inputs and return formatted data. Many tools support an optional `response_format` parameter (`markdown` or `json`).

### Player Tools (5 tools)

| Tool Name                         | Description                                         | Key Parameters                           |
| --------------------------------- | --------------------------------------------------- | ---------------------------------------- |
| `fpl_find_player`                 | Find player with fuzzy name matching                | `player_name`                            |
| `fpl_get_player_details`          | Comprehensive player info with fixtures and history | `player_name`                            |
| `fpl_compare_players`             | Compare multiple players side-by-side               | `player_names[]`                         |
| `fpl_get_top_performers`          | Top 10 players by goals, xG, assists, xA, xGI       | `num_gameweeks`, `response_format`       |
| `fpl_get_captain_recommendations` | Get top captain picks for upcoming gameweek         | `team_id`, `gameweek`, `response_format` |

### Team Tools (1 tool)

| Tool Name                   | Description                         | Key Parameters                                  |
| --------------------------- | ----------------------------------- | ----------------------------------------------- |
| `fpl_analyze_team_fixtures` | Assess upcoming fixtures for a team | `team_name`, `num_gameweeks`, `response_format` |

### Gameweek Tools (1 tool)

| Tool Name                  | Description                          | Key Parameters    |
| -------------------------- | ------------------------------------ | ----------------- |
| `fpl_get_current_gameweek` | Current or upcoming gameweek details | `response_format` |

### Fixtures Tools (2 tools)

| Tool Name                        | Description                                            | Key Parameters                                               |
| -------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------ |
| `fpl_get_fixtures_for_gameweek`  | All matches in a specific gameweek (basic or detailed) | `gameweek`, `detailed`, `response_format`                    |
| `fpl_find_fixture_opportunities` | Find teams with easiest upcoming fixtures              | `num_gameweeks`, `max_teams`, `positions`, `response_format` |

### League & Manager Tools (6 tools)

| Tool Name                       | Description                            | Key Parameters                                               |
| ------------------------------- | -------------------------------------- | ------------------------------------------------------------ |
| `fpl_get_league_standings`      | League rankings and points             | `league_id`, `page`, `response_format`                       |
| `fpl_get_manager_gameweek_team` | Manager team by name within a league   | `manager_name`, `league_id`, `gameweek`                      |
| `fpl_compare_managers`          | Side-by-side manager comparison        | `manager_names[]`, `league_id`, `gameweek`                   |
| `fpl_get_manager_squad`         | Manager squad by team ID               | `team_id`, `gameweek`, `response_format`                     |
| `fpl_get_manager_by_team_id`    | Manager profile without league context | `team_id`, `gameweek`, `response_format`                     |
| `fpl_analyze_rival`             | Head-to-head analysis with a rival     | `my_team_id`, `rival_team_id`, `gameweek`, `response_format` |

### Transfer Tools (4 tools)

| Tool Name                               | Description                           | Key Parameters                                             |
| --------------------------------------- | ------------------------------------- | ---------------------------------------------------------- |
| `fpl_analyze_transfer`                  | Analyze a potential transfer decision | `player_out`, `player_in`, `my_team_id`, `response_format` |
| `fpl_get_top_transferred_players`       | Most transferred in/out right now     | `limit`, `response_format`                                 |
| `fpl_get_manager_transfers_by_gameweek` | Transfers made by a manager           | `team_id`, `gameweek`                                      |
| `fpl_get_manager_chips`                 | View used and available chips         | `team_id`, `response_format`                               |

---

## Resources

URI-based resources provide efficient access to FPL data. Use these for quick data retrieval without complex analysis.

### Bootstrap Resources (4 resources)

| Resource URI                | Description                  | Example                     |
| --------------------------- | ---------------------------- | --------------------------- |
| `fpl://bootstrap/players`   | All players with basic stats | `fpl://bootstrap/players`   |
| `fpl://bootstrap/teams`     | All teams with metadata      | `fpl://bootstrap/teams`     |
| `fpl://bootstrap/gameweeks` | All gameweeks with status    | `fpl://bootstrap/gameweeks` |
| `fpl://current-gameweek`    | Current gameweek information | `fpl://current-gameweek`    |

---

## Prompts

Structured templates that guide analysis workflows. Prompts combine multiple tools and resources for comprehensive insights.

| Prompt Name                 | Description                                                                                              | Parameters                                | Use Case                                                             |
| --------------------------- | -------------------------------------------------------------------------------------------------------- | ----------------------------------------- | -------------------------------------------------------------------- |
| `analyze_squad_performance` | Squad performance over recent gameweeks                                                                  | `team_id`, `num_gameweeks`                | Identify underperformers and transfer candidates                     |
| `analyze_team_fixtures`     | Team fixture difficulty analysis                                                                         | `team_name`, `num_gameweeks`              | Find optimal times to invest in team assets                          |
| `select_team`               | Starting XI and bench optimization                                                                       | `team_id`, `gameweek`                     | Pick the optimal lineup for a specific gameweek                      |
| `recommend_transfers`       | Transfer strategy recommendations                                                                        | `team_id`, `free_transfers`               | Generate transfer in/out suggestions                                 |
| `recommend_chip_strategy`   | Chip timing and strategy                                                                                 | `team_id`                                 | Optimize Wildcard, Free Hit, Triple Captain, Bench Boost             |
| `recommend_captain`         | Top 3 captain picks with Pro-Level scoring (Weighted: xGI 40%, Fixtures 30%, Nailedness 20%, Upside 10%) | `team_id`, `gameweek`, `response_format`  | Optimize weekly captain selection with weighted data-driven insights |
| `compare_players`           | Side-by-side player comparison                                                                           | `*player_names`                           | Choose between transfer targets                                      |
| `compare_managers`          | Manager team comparison                                                                                  | `league_id`, `gameweek`, `*manager_names` | Analyze league rivals' strategies                                    |
| `find_league_differentials` | Find low-ownership differentials                                                                         | `league_id`, `max_ownership`              | Gain competitive advantage in mini-leagues                           |
| `gameweek_analysis`         | Detailed match reports & transfer implications                                                           | `gameweek`                                | Review completed gameweek stats and identify trends                  |

---

## Quick Decision Guide

### Finding Players

- **Know exact name?** → `fpl_get_player_details` - Comprehensive player info with fixtures, history, and stats
- **Partial name/typos?** → `fpl_find_player` - Fuzzy matching finds players even with spelling variations
- **Want captain picks?** → `fpl_get_captain_recommendations` - Top weighted captaincy picks
- **Want top by metrics?** → `fpl_get_top_performers` - Top 10 players by goals, xG, assists, xA, xGI over recent gameweeks

### Analyzing Teams

- **Fixture difficulty?** → `fpl_analyze_team_fixtures` - Assess upcoming fixtures for a specific team
- **Find easy fixtures?** → `fpl_find_fixture_opportunities` - Recommend teams with easiest upcoming runs

### Gameweek Information

- **Current gameweek?** → `fpl_get_current_gameweek` - Current or upcoming gameweek details
- **Gameweek fixtures?** → `fpl_get_fixtures_for_gameweek` - All matches in a specific gameweek
- **Gameweek review?** → `gameweek_analysis` - Comprehensive match analysis and transfer implications

### Lineup & Captaincy

- **Pick a starting XI and bench?** → `select_team` - Lineup optimization for a specific gameweek
- **Captain decision?** → `recommend_captain` - Weighted captaincy analysis

### League & Manager Analysis

- **League standings?** → `fpl_get_league_standings` - Rankings and points (requires league ID)
- **View team by manager name?** → `fpl_get_manager_gameweek_team` - Find a manager within a league and view their GW team
- **View any team by ID?** → `fpl_get_manager_by_team_id` - Direct access to manager profile via team ID
- **Compare managers?** → `fpl_compare_managers` - Side-by-side team comparison within a league
- **Analyze rival?** → `fpl_analyze_rival` - Deep dive head-to-head vs a specific rival
- **Manager transfers?** → `fpl_get_manager_transfers_by_gameweek` - Transfers made by a manager

### Transfer Intelligence

- **Analyze move?** → `fpl_analyze_transfer` - Deep dive comparison of player OUT vs player IN
- **Current trends?** → `fpl_get_top_transferred_players` - Most transferred in/out right now
- **Manager chip usage?** → `fpl_get_manager_chips` - View used and available chips (2025/26 half-season system)

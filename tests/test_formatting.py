"""
Tests for formatting module.
"""

from unittest.mock import Mock

from src.formatting import (
    format_difficulty_indicator,
    format_gameweek_details,
    format_manager_squad,
    format_markdown_table_row,
    format_player_details,
    format_team_details,
)


class TestFormatPlayerDetails:
    """Tests for format_player_details function."""

    def test_basic_player_info(self):
        """Test formatting basic player information."""
        player = Mock()
        player.web_name = "Salah"
        player.first_name = "Mohamed"
        player.second_name = "Salah"
        player.team_name = "Liverpool"
        player.position = "MID"
        player.now_cost = 130
        player.form = "8.5"
        player.points_per_game = "7.2"

        result = format_player_details(player)

        assert "**Salah** (Mohamed Salah)" in result
        assert "Team: Liverpool | Position: MID | Price: £13.0m" in result
        assert "**Performance:**" in result
        assert "Form: 8.5" in result
        assert "Points per Game: 7.2" in result

    def test_player_with_fixtures(self):
        """Test formatting player with upcoming fixtures."""
        player = Mock()
        player.web_name = "Salah"
        player.first_name = "Mohamed"
        player.second_name = "Salah"
        player.now_cost = 130
        player.form = "8.5"
        player.points_per_game = "7.2"

        fixtures = [
            {
                "event": 10,
                "team_h_short": "ARS",
                "team_a_short": "LIV",
                "is_home": False,
                "difficulty": 4,
            },
            {
                "event": 11,
                "team_h_short": "LIV",
                "team_a_short": "CHE",
                "is_home": True,
                "difficulty": 3,
            },
        ]

        result = format_player_details(player, fixtures=fixtures)

        assert "**Upcoming Fixtures (2):**" in result
        assert "GW10: vs ARS (A)" in result
        assert "Difficulty: ●●●● (4/5)" in result
        assert "GW11: vs CHE (H)" in result
        assert "Difficulty: ●●● (3/5)" in result

    def test_player_with_history(self):
        """Test formatting player with gameweek history."""
        player = Mock()
        player.web_name = "Haaland"
        player.first_name = "Erling"
        player.second_name = "Haaland"
        player.now_cost = 140
        player.form = "9.0"
        player.points_per_game = "8.5"

        history = [
            {
                "round": 8,
                "total_points": 12,
                "opponent_team_short": "BRE",
                "was_home": True,
                "minutes": 90,
                "expected_goals": "1.23",
                "expected_assists": "0.45",
                "goals_scored": 2,
                "assists": 1,
                "clean_sheets": 0,
                "bonus": 3,
            },
            {
                "round": 9,
                "total_points": 6,
                "opponent_team_short": "ARS",
                "was_home": False,
                "minutes": 85,
                "expected_goals": "0.67",
                "expected_assists": "0.12",
                "goals_scored": 1,
                "assists": 0,
                "clean_sheets": 0,
                "bonus": 0,
            },
        ]

        result = format_player_details(player, history=history)

        assert "**Recent Performance (Last 2 GWs):**" in result
        assert "GW8: 12pts vs BRE (H)" in result
        assert "90min" in result
        assert "xG: 1.23" in result
        assert "G:2" in result
        assert "**Recent Averages:**" in result
        assert "Points per game: 9.0" in result
        assert "Minutes per game: 88" in result

    def test_player_with_popularity(self):
        """Test formatting player with popularity stats."""
        player = Mock()
        player.web_name = "Salah"
        player.first_name = "Mohamed"
        player.second_name = "Salah"
        player.now_cost = 130
        player.form = "8.5"
        player.points_per_game = "7.2"
        player.selected_by_percent = "45.3"
        player.transfers_in_event = 123456
        player.transfers_out_event = 45678

        result = format_player_details(player)

        assert "**Popularity:**" in result
        assert "Selected by: 45.3%" in result
        assert "Transfers in (GW): 123456" in result
        assert "Transfers out (GW): 45678" in result

    def test_player_with_season_stats(self):
        """Test formatting player with season statistics."""
        player = Mock()
        player.web_name = "Kane"
        player.first_name = "Harry"
        player.second_name = "Kane"
        player.now_cost = 115
        player.form = "7.5"
        player.points_per_game = "6.8"
        player.goals_scored = 15
        player.assists = 3
        player.clean_sheets = 2
        player.bonus = 12

        result = format_player_details(player)

        assert "**Season Stats:**" in result
        assert "Goals: 15" in result
        assert "Assists: 3" in result
        assert "Clean Sheets: 2" in result
        assert "Bonus Points: 12" in result


class TestFormatTeamDetails:
    """Tests for format_team_details function."""

    def test_basic_team_info(self):
        """Test formatting basic team information."""
        team = {"name": "Arsenal", "short_name": "ARS"}

        result = format_team_details(team)

        assert "**Arsenal (ARS)**" in result

    def test_team_with_strength(self):
        """Test formatting team with strength ratings."""
        team = {
            "name": "Manchester City",
            "short_name": "MCI",
            "strength": 5,
            "strength_overall_home": 1400,
            "strength_overall_away": 1350,
            "strength_attack_home": 1420,
            "strength_attack_away": 1380,
            "strength_defence_home": 1380,
            "strength_defence_away": 1320,
        }

        result = format_team_details(team)

        assert "**Manchester City (MCI)**" in result
        assert "Overall Strength: 5" in result
        assert "**Overall Strength:**" in result
        assert "Home: 1400" in result
        assert "Away: 1350" in result
        assert "**Attack Strength:**" in result
        assert "Home: 1420" in result
        assert "Away: 1380" in result
        assert "**Defence Strength:**" in result
        assert "Home: 1380" in result
        assert "Away: 1320" in result

    def test_team_with_partial_stats(self):
        """Test formatting team with only some stats."""
        team = {
            "name": "Liverpool",
            "short_name": "LIV",
            "strength_attack_home": 1380,
            "strength_attack_away": 1350,
        }

        result = format_team_details(team)

        assert "**Liverpool (LIV)**" in result
        assert "**Attack Strength:**" in result
        assert "Home: 1380" in result


class TestFormatGameweekDetails:
    """Tests for format_gameweek_details function."""

    def test_current_gameweek(self):
        """Test formatting current gameweek."""
        event = Mock()
        event.name = "Gameweek 10"
        event.deadline_time = "2024-11-09T18:30:00Z"
        event.is_current = True
        event.is_previous = False
        event.is_next = False
        event.finished = False
        event.released = True

        result = format_gameweek_details(event)

        assert "**Gameweek 10**" in result
        assert "Deadline: 2024-11-09T18:30:00Z" in result
        assert "Status: Current" in result
        assert "Finished: False" in result

    def test_finished_gameweek(self):
        """Test formatting finished gameweek with stats."""
        event = Mock()
        event.name = "Gameweek 9"
        event.deadline_time = "2024-11-02T18:30:00Z"
        event.is_current = False
        event.is_previous = True
        event.is_next = False
        event.finished = True
        event.released = True
        event.average_entry_score = 56
        event.highest_score = 102

        result = format_gameweek_details(event)

        assert "**Gameweek 9**" in result
        assert "Status: Previous" in result
        assert "Finished: True" in result
        assert "**Statistics:**" in result
        assert "Average Score: 56" in result
        assert "Highest Score: 102" in result

    def test_next_gameweek(self):
        """Test formatting next gameweek."""
        event = Mock()
        event.name = "Gameweek 11"
        event.deadline_time = "2024-11-16T18:30:00Z"
        event.is_current = False
        event.is_previous = False
        event.is_next = True
        event.finished = False
        event.released = True

        result = format_gameweek_details(event)

        assert "Status: Next" in result


class TestFormatManagerSquad:
    """Tests for format_manager_squad function."""

    def test_basic_squad_formatting(self):
        """Test formatting manager squad."""
        entry_history = {
            "points": 65,
            "total_points": 720,
            "overall_rank": 123456,
            "value": 1020,
            "bank": 5,
            "event_transfers": 1,
            "event_transfers_cost": 4,
            "points_on_bench": 8,
        }

        picks = [
            {
                "element": 1,
                "position": 1,
                "is_captain": False,
                "is_vice_captain": False,
                "multiplier": 1,
            },
            {
                "element": 2,
                "position": 2,
                "is_captain": False,
                "is_vice_captain": False,
                "multiplier": 1,
            },
            {
                "element": 3,
                "position": 11,
                "is_captain": True,
                "is_vice_captain": False,
                "multiplier": 2,
            },
            {
                "element": 4,
                "position": 12,
                "is_captain": False,
                "is_vice_captain": True,
                "multiplier": 1,
            },
        ]

        players_info = {
            1: {"web_name": "Pickford", "team": "EVE", "position": "GKP", "price": 4.5},
            2: {"web_name": "Saliba", "team": "ARS", "position": "DEF", "price": 6.0},
            3: {"web_name": "Salah", "team": "LIV", "position": "MID", "price": 13.0},
            4: {"web_name": "Haaland", "team": "MCI", "position": "FWD", "price": 14.0},
        }

        result = format_manager_squad(
            team_name="Test Team",
            player_name="John Doe",
            team_id=12345,
            gameweek=10,
            entry_history=entry_history,
            picks=picks,
            players_info=players_info,
        )

        assert "**Test Team** - John Doe" in result
        assert "Team ID: 12345" in result
        assert "Gameweek 10" in result
        assert "Points: 65 | Total: 720" in result
        assert "Overall Rank: 123,456" in result
        assert "Team Value: £102.0m | Bank: £0.5m" in result
        assert "Transfers: 1 (Cost: 4pts)" in result
        assert "Points on Bench: 8" in result
        assert "**Starting XI:**" in result
        assert "Salah" in result
        assert "(C)" in result
        assert "x2" in result
        assert "**Bench:**" in result
        assert "Haaland" in result
        # Note: (VC) is only shown in bench, not in the current format

    def test_squad_with_active_chip(self):
        """Test formatting squad with active chip."""
        entry_history = {
            "points": 65,
            "total_points": 720,
            "overall_rank": 50000,  # Add this to avoid formatting error
            "value": 1000,
            "bank": 0,
            "event_transfers": 0,
            "event_transfers_cost": 0,
            "points_on_bench": 0,
        }
        picks = [
            {
                "element": 1,
                "position": 1,
                "is_captain": False,
                "is_vice_captain": False,
                "multiplier": 1,
            }
        ]
        players_info = {1: {"web_name": "Pickford", "team": "EVE", "position": "GKP", "price": 4.5}}

        result = format_manager_squad(
            team_name="Test Team",
            player_name="",
            team_id=12345,
            gameweek=10,
            entry_history=entry_history,
            picks=picks,
            players_info=players_info,
            active_chip="3xc",
        )

        assert "**Active Chip:** 3xc" in result
        assert "**Test Team**" in result  # No player name


class TestFormatDifficultyIndicator:
    """Tests for format_difficulty_indicator function."""

    def test_difficulty_levels(self):
        """Test formatting different difficulty levels."""
        assert format_difficulty_indicator(1) == "●○○○○"
        assert format_difficulty_indicator(2) == "●●○○○"
        assert format_difficulty_indicator(3) == "●●●○○"
        assert format_difficulty_indicator(4) == "●●●●○"
        assert format_difficulty_indicator(5) == "●●●●●"


class TestFormatMarkdownTableRow:
    """Tests for format_markdown_table_row function."""

    def test_simple_row(self):
        """Test formatting simple row without widths."""
        result = format_markdown_table_row(["Name", "Team", "Price"])
        assert result == "| Name | Team | Price |"

    def test_row_with_widths(self):
        """Test formatting row with specified widths."""
        result = format_markdown_table_row(["Salah", "LIV", "13.0"], widths=[15, 5, 6])
        assert result == "| Salah           | LIV   | 13.0   |"

    def test_row_with_numbers(self):
        """Test formatting row with numeric values."""
        result = format_markdown_table_row([1, 2, 3])
        assert result == "| 1 | 2 | 3 |"

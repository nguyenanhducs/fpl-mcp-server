"""
Pytest fixtures and configuration for FPL MCP Server tests.
"""

import pytest

from src.client import FPLClient
from src.models import BootstrapData, ElementData, ElementTypeData, EventData, FixtureData, TeamData
from src.state import SessionStore


@pytest.fixture
def mock_teams() -> list[TeamData]:
    """Mock team data for testing."""
    return [
        TeamData(id=1, name="Arsenal", short_name="ARS"),
        TeamData(id=2, name="Liverpool", short_name="LIV"),
        TeamData(id=3, name="Man City", short_name="MCI"),
    ]


@pytest.fixture
def mock_element_types() -> list[ElementTypeData]:
    """Mock position types for testing."""
    return [
        ElementTypeData(id=1, singular_name_short="GKP", plural_name_short="GKPs"),
        ElementTypeData(id=2, singular_name_short="DEF", plural_name_short="DEFs"),
        ElementTypeData(id=3, singular_name_short="MID", plural_name_short="MIDs"),
        ElementTypeData(id=4, singular_name_short="FWD", plural_name_short="FWDs"),
    ]


@pytest.fixture
def mock_players(mock_teams, mock_element_types) -> list[ElementData]:
    """Mock player data for testing."""
    return [
        ElementData(
            id=1,
            web_name="Salah",
            first_name="Mohamed",
            second_name="Salah",
            team=2,  # Liverpool
            element_type=3,  # MID
            now_cost=130,
            form="8.5",
            points_per_game="7.2",
            news="",
            status="a",
        ),
        ElementData(
            id=2,
            web_name="Haaland",
            first_name="Erling",
            second_name="Haaland",
            team=3,  # Man City
            element_type=4,  # FWD
            now_cost=140,
            form="9.0",
            points_per_game="8.5",
            news="",
            status="a",
        ),
        ElementData(
            id=3,
            web_name="Saka",
            first_name="Bukayo",
            second_name="Saka",
            team=1,  # Arsenal
            element_type=3,  # MID
            now_cost=95,
            form="6.5",
            points_per_game="5.8",
            news="",
            status="a",
        ),
    ]


@pytest.fixture
def mock_events() -> list[EventData]:
    """Mock gameweek event data."""
    return [
        EventData(
            id=1,
            name="Gameweek 1",
            deadline_time="2024-08-16T17:30:00Z",
            average_entry_score=None,
            finished=True,
            data_checked=True,
            highest_scoring_entry=None,
            deadline_time_epoch=1692203400,
            highest_score=None,
            is_previous=True,
            is_current=False,
            is_next=False,
            can_enter=False,
            released=True,
        ),
        EventData(
            id=2,
            name="Gameweek 2",
            deadline_time="2024-08-23T17:30:00Z",
            average_entry_score=None,
            finished=False,
            data_checked=False,
            highest_scoring_entry=None,
            deadline_time_epoch=1692808200,
            highest_score=None,
            is_previous=False,
            is_current=True,
            is_next=False,
            can_enter=True,
            released=True,
        ),
    ]


@pytest.fixture
def mock_bootstrap_data(mock_players, mock_teams, mock_element_types, mock_events) -> BootstrapData:
    """Mock bootstrap data with all required components."""
    return BootstrapData(
        elements=mock_players,
        teams=mock_teams,
        element_types=mock_element_types,
        events=mock_events,
        chips=[
            {
                "id": 1,
                "name": "wildcard",
                "start_event": 1,
                "stop_event": 38,
                "chip_type": "transfer",
                "number": 1,
            },
            {
                "id": 2,
                "name": "freehit",
                "start_event": 1,
                "stop_event": 38,
                "chip_type": "transfer",
                "number": 1,
            },
            {
                "id": 3,
                "name": "3xc",
                "start_event": 1,
                "stop_event": 38,
                "chip_type": "team",
                "number": 1,
            },
            {
                "id": 4,
                "name": "bboost",
                "start_event": 1,
                "stop_event": 38,
                "chip_type": "team",
                "number": 1,
            },
        ],
    )


@pytest.fixture
def session_store(mock_bootstrap_data, mock_fixtures_data) -> SessionStore:
    """Create a SessionStore with mock bootstrap data."""
    store = SessionStore()
    store.bootstrap_data = mock_bootstrap_data
    store.fixtures_data = [FixtureData(**f) for f in mock_fixtures_data]
    store._build_player_indices()
    return store


@pytest.fixture(autouse=True)
def patch_global_store(session_store, monkeypatch):
    """Patch all tool modules to use test session_store instead of global store."""
    # Patch the store in all tool modules
    monkeypatch.setattr("src.tools.fixtures.store", session_store)
    monkeypatch.setattr("src.tools.players.store", session_store)
    monkeypatch.setattr("src.tools.teams.store", session_store)
    monkeypatch.setattr("src.tools.gameweeks.store", session_store)
    monkeypatch.setattr("src.tools.leagues.store", session_store)
    monkeypatch.setattr("src.tools.transfers.store", session_store)
    return session_store


@pytest.fixture
def mock_client(session_store) -> FPLClient:
    """Create a mock FPL client."""
    return FPLClient(store=session_store)


@pytest.fixture
def mock_fixtures_data() -> list[dict]:
    """Mock fixture data for testing."""
    return [
        {
            "id": 1,
            "code": 1001,
            "event": 2,
            "team_h": 1,
            "team_a": 2,
            "team_h_score": None,
            "team_a_score": None,
            "finished": False,
            "finished_provisional": False,
            "minutes": 0,
            "provisional_start_time": False,
            "started": False,
            "kickoff_time": "2024-08-24T14:00:00Z",
            "team_h_difficulty": 3,
            "team_a_difficulty": 3,
            "stats": [],
            "pulse_id": 1,
        },
        {
            "id": 2,
            "code": 1002,
            "event": 2,
            "team_h": 3,
            "team_a": 1,
            "team_h_score": None,
            "team_a_score": None,
            "finished": False,
            "finished_provisional": False,
            "minutes": 0,
            "provisional_start_time": False,
            "started": False,
            "kickoff_time": "2024-08-24T16:30:00Z",
            "team_h_difficulty": 2,
            "team_a_difficulty": 4,
            "stats": [],
            "pulse_id": 2,
        },
        {
            # Past fixture (GW1)
            "id": 3,
            "code": 1000,
            "event": 1,
            "team_h": 2,  # Liverpool
            "team_a": 1,  # Arsenal
            "team_h_score": 1,
            "team_a_score": 0,
            "finished": True,
            "finished_provisional": True,
            "minutes": 90,
            "provisional_start_time": False,
            "started": True,
            "kickoff_time": "2024-08-17T14:00:00Z",
            "team_h_difficulty": 3,
            "team_a_difficulty": 3,
            "stats": [],
            "pulse_id": 3,
        },
    ]


@pytest.fixture
def mock_element_summary() -> dict:
    """Mock detailed player summary data."""
    return {
        "fixtures": [
            {
                "id": 1,
                "event": 2,
                "team_h": 2,
                "team_a": 1,
                "is_home": True,
                "difficulty": 3,
                "kickoff_time": "2024-08-24T14:00:00Z",
            }
        ],
        "history": [
            {
                "element": 1,
                "fixture": 0,
                "opponent_team": 3,
                "total_points": 12,
                "was_home": True,
                "kickoff_time": "2024-08-17T14:00:00Z",
                "team_h_score": 2,
                "team_a_score": 1,
                "round": 1,
                "minutes": 90,
                "goals_scored": 1,
                "assists": 1,
                "clean_sheets": 0,
                "goals_conceded": 1,
                "own_goals": 0,
                "penalties_saved": 0,
                "penalties_missed": 0,
                "yellow_cards": 0,
                "red_cards": 0,
                "saves": 0,
                "bonus": 3,
                "bps": 45,
                "influence": "80.0",
                "creativity": "75.0",
                "threat": "85.0",
                "ict_index": "24.0",
                "value": 130,
                "transfers_balance": 50000,
                "selected": 2000000,
                "transfers_in": 100000,
                "transfers_out": 50000,
            }
        ],
        "history_past": [
            {
                "season_name": "2023/24",
                "element_code": 123456,
                "start_cost": 125,
                "end_cost": 130,
                "total_points": 280,
                "minutes": 3240,
                "goals_scored": 20,
                "assists": 15,
                "clean_sheets": 12,
                "goals_conceded": 30,
                "own_goals": 0,
                "penalties_saved": 0,
                "penalties_missed": 1,
                "yellow_cards": 3,
                "red_cards": 0,
                "saves": 0,
                "bonus": 25,
                "bps": 850,
                "influence": "1500.0",
                "creativity": "1400.0",
                "threat": "1600.0",
                "ict_index": "450.0",
            }
        ],
    }


@pytest.fixture
def mock_manager_entry() -> dict:
    """Mock manager entry data."""
    return {
        "id": 12345,
        "player_first_name": "John",
        "player_last_name": "Doe",
        "name": "John's Team",
        "summary_overall_points": 550,
        "summary_overall_rank": 150000,
        "summary_event_points": 65,
        "summary_event_rank": 2500000,
        "current_event": 2,
        "leagues": {"classic": [{"id": 999, "name": "Test League", "rank": 5, "entry_rank": 5}]},
    }


@pytest.fixture
def mock_manager_picks() -> dict:
    """Mock manager gameweek picks data."""
    return {
        "active_chip": None,
        "automatic_subs": [],
        "entry_history": {
            "event": 2,
            "points": 65,
            "total_points": 550,
            "rank": 2500000,
            "rank_sort": 2500000,
            "overall_rank": 150000,
            "bank": 5,
            "value": 1000,
            "event_transfers": 1,
            "event_transfers_cost": 0,
            "points_on_bench": 8,
        },
        "picks": [
            {
                "element": 1,
                "position": 1,
                "multiplier": 2,
                "is_captain": True,
                "is_vice_captain": False,
            },
            {
                "element": 2,
                "position": 2,
                "multiplier": 1,
                "is_captain": False,
                "is_vice_captain": True,
            },
            {
                "element": 3,
                "position": 3,
                "multiplier": 1,
                "is_captain": False,
                "is_vice_captain": False,
            },
        ],
    }


@pytest.fixture
def mock_league_standings() -> dict:
    """Mock league standings data."""
    return {
        "league": {
            "id": 999,
            "name": "Test League",
            "created": "2024-08-01T12:00:00Z",
            "closed": False,
            "rank": None,
            "max_entries": None,
            "league_type": "x",
            "scoring": "c",
            "start_event": 1,
            "code_privacy": "p",
            "has_cup": False,
            "cup_league": None,
            "admin_entry": 12345,
        },
        "standings": {
            "has_next": False,
            "page": 1,
            "results": [
                {
                    "id": 12345,
                    "event_total": 65,
                    "player_name": "John Doe",
                    "rank": 1,
                    "last_rank": 1,
                    "rank_sort": 1,
                    "total": 550,
                    "entry": 12345,
                    "entry_name": "John's Team",
                },
                {
                    "id": 67890,
                    "event_total": 60,
                    "player_name": "Jane Smith",
                    "rank": 2,
                    "last_rank": 2,
                    "rank_sort": 2,
                    "total": 540,
                    "entry": 67890,
                    "entry_name": "Jane's Squad",
                },
            ],
        },
    }


@pytest.fixture
def mock_transfers_list() -> list[dict]:
    """Mock transfer history data."""
    return [
        {
            "element_in": 1,
            "element_in_cost": 130,
            "element_out": 10,
            "element_out_cost": 95,
            "entry": 12345,
            "event": 2,
            "time": "2024-08-23T10:30:00Z",
        },
        {
            "element_in": 2,
            "element_in_cost": 140,
            "element_out": 11,
            "element_out_cost": 80,
            "entry": 12345,
            "event": 1,
            "time": "2024-08-16T09:00:00Z",
        },
    ]


@pytest.fixture
def mock_manager_history() -> dict:
    """Mock manager history data including chips."""
    return {
        "current": [
            {
                "event": 1,
                "points": 485,
                "total_points": 485,
                "rank": 3000000,
                "rank_sort": 3000000,
                "overall_rank": 3000000,
                "bank": 10,
                "value": 1000,
                "event_transfers": 0,
                "event_transfers_cost": 0,
                "points_on_bench": 12,
            },
            {
                "event": 2,
                "points": 65,
                "total_points": 550,
                "rank": 2500000,
                "rank_sort": 2500000,
                "overall_rank": 150000,
                "bank": 5,
                "value": 1000,
                "event_transfers": 1,
                "event_transfers_cost": 0,
                "points_on_bench": 8,
            },
        ],
        "past": [],
        "chips": [
            {
                "name": "wildcard",
                "time": "2024-08-23T10:30:00Z",
                "event": 2,
            },
            {
                "name": "freehit",
                "time": None,
                "event": 5,
            },
            {
                "name": "3xc",
                "time": None,
                "event": 10,
            },
            {
                "name": "bboost",
                "time": None,
                "event": 15,
            },
        ],
    }

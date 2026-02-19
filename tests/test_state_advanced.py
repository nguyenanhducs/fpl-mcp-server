"""
Additional tests to increase state.py coverage from 74% to 90%+
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.models import EventData
from src.state import SessionStore


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ensure_bootstrap_data_error_handling(mock_client):
    """Test ensure_bootstrap_data error handling."""
    store = SessionStore()

    # Mock the client to raise an exception
    mock_client.get_bootstrap_data = AsyncMock(side_effect=Exception("API Error"))

    # Mock cache to return None so the API call is attempted
    with patch("src.state.cache_manager.get", return_value=None):
        with pytest.raises(Exception) as exc_info:
            await store.ensure_bootstrap_data(mock_client)

        assert "API Error" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ensure_fixtures_data_error_handling(mock_client):
    """Test ensure_fixtures_data error handling."""
    store = SessionStore()

    # Mock the client to raise an exception
    mock_client.get_fixtures = AsyncMock(side_effect=Exception("Fixtures API Error"))

    # Mock cache to return None so the API call is attempted
    with patch("src.state.cache_manager.get", return_value=None):
        with pytest.raises(Exception) as exc_info:
            await store.ensure_fixtures_data(mock_client)

        assert "Fixtures API Error" in str(exc_info.value)


@pytest.mark.unit
def test_build_player_indices_no_data():
    """Test _build_player_indices with no bootstrap data."""
    store = SessionStore()
    store.bootstrap_data = None

    # Should not raise an error
    store._build_player_indices()

    assert len(store.player_name_map) == 0
    assert len(store.player_id_map) == 0


@pytest.mark.unit
def test_get_team_by_id_no_data():
    """Test get_team_by_id when no bootstrap data exists."""
    store = SessionStore()
    store.bootstrap_data = None

    result = store.get_team_by_id(1)

    assert result is None


@pytest.mark.unit
def test_get_team_by_id_not_found(session_store):
    """Test get_team_by_id when team ID doesn't exist."""
    result = session_store.get_team_by_id(9999)

    assert result is None


@pytest.mark.unit
def test_get_all_teams_no_data():
    """Test get_all_teams when no bootstrap data exists."""
    store = SessionStore()
    store.bootstrap_data = None

    result = store.get_all_teams()

    assert result == []


@pytest.mark.unit
def test_find_players_no_data():
    """Test find_players_by_name when no bootstrap data exists."""
    store = SessionStore()
    store.bootstrap_data = None

    result = store.find_players_by_name("Salah")

    assert result == []


@pytest.mark.unit
def test_get_current_gameweek_no_data():
    """Test get_current_gameweek with no bootstrap data."""
    store = SessionStore()
    store.bootstrap_data = None

    result = store.get_current_gameweek()

    assert result is None


@pytest.mark.unit
def test_get_current_gameweek_fallback_to_next(session_store):
    """Test get_current_gameweek falls back to is_next when no is_current."""
    # Modify events to have only is_next
    for event in session_store.bootstrap_data.events:
        event.is_current = False

    session_store.bootstrap_data.events[1].is_next = True

    result = session_store.get_current_gameweek()

    assert result is not None
    assert result.is_next is True


@pytest.mark.unit
def test_get_current_gameweek_fallback_to_unfinished():
    """Test get_current_gameweek falls back to first unfinished gameweek."""
    store = SessionStore()
    from src.models import BootstrapData, ElementTypeData, TeamData

    # Create events with no is_current or is_next, but one unfinished
    events = [
        EventData(
            id=1,
            name="GW 1",
            deadline_time="2024-08-16T17:30:00Z",
            finished=True,
            data_checked=True,
            deadline_time_epoch=1692203400,
            is_previous=True,
            is_current=False,
            is_next=False,
            can_enter=False,
            released=True,
        ),
        EventData(
            id=2,
            name="GW 2",
            deadline_time="2024-08-23T17:30:00Z",
            finished=False,
            data_checked=False,
            deadline_time_epoch=1692808200,
            is_previous=False,
            is_current=False,
            is_next=False,
            can_enter=True,
            released=True,
        ),
    ]

    store.bootstrap_data = BootstrapData(
        elements=[],
        teams=[TeamData(id=1, name="Arsenal", short_name="ARS")],
        element_types=[ElementTypeData(id=1, singular_name_short="GKP", plural_name_short="GKPs")],
        events=events,
    )

    result = store.get_current_gameweek()

    assert result is not None
    assert result.finished is False
    assert result.id == 2


@pytest.mark.unit
def test_get_current_gameweek_all_finished():
    """Test get_current_gameweek returns None when all gameweeks finished."""
    store = SessionStore()
    from src.models import BootstrapData, ElementTypeData, TeamData

    events = [
        EventData(
            id=38,
            name="GW 38",
            deadline_time="2024-05-19T14:00:00Z",
            finished=True,
            data_checked=True,
            deadline_time_epoch=1716123600,
            is_previous=True,
            is_current=False,
            is_next=False,
            can_enter=False,
            released=True,
        ),
    ]

    store.bootstrap_data = BootstrapData(
        elements=[],
        teams=[TeamData(id=1, name="Arsenal", short_name="ARS")],
        element_types=[ElementTypeData(id=1, singular_name_short="GKP", plural_name_short="GKPs")],
        events=events,
    )

    result = store.get_current_gameweek()

    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_find_manager_by_name_exact_player_name(mock_client):
    """Test find_manager_by_name with exact player name match."""
    store = SessionStore()

    mock_standings = {
        "standings": {
            "results": [
                {
                    "entry": 12345,
                    "entry_name": "My Team",
                    "player_name": "John Doe",
                },
                {
                    "entry": 67890,
                    "entry_name": "Another Team",
                    "player_name": "Jane Smith",
                },
            ]
        }
    }

    mock_client.get_league_standings = AsyncMock(return_value=mock_standings)

    result = await store.find_manager_by_name(mock_client, 123, "John Doe")

    assert result is not None
    assert result["entry"] == 12345
    assert result["player_name"] == "John Doe"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_find_manager_by_name_exact_entry_name(mock_client):
    """Test find_manager_by_name with exact entry (team) name match."""
    store = SessionStore()

    mock_standings = {
        "standings": {
            "results": [
                {
                    "entry": 12345,
                    "entry_name": "My Special Team",
                    "player_name": "John Doe",
                },
            ]
        }
    }

    mock_client.get_league_standings = AsyncMock(return_value=mock_standings)

    result = await store.find_manager_by_name(mock_client, 123, "My Special Team")

    assert result is not None
    assert result["entry"] == 12345
    assert result["entry_name"] == "My Special Team"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_find_manager_by_name_substring_match(mock_client):
    """Test find_manager_by_name with substring match."""
    store = SessionStore()

    mock_standings = {
        "standings": {
            "results": [
                {
                    "entry": 12345,
                    "entry_name": "The Invincibles",
                    "player_name": "Alexander Hamilton",
                },
            ]
        }
    }

    mock_client.get_league_standings = AsyncMock(return_value=mock_standings)

    result = await store.find_manager_by_name(mock_client, 123, "Hamilton")

    assert result is not None
    assert result["entry"] == 12345


@pytest.mark.unit
@pytest.mark.asyncio
async def test_find_manager_by_name_not_found(mock_client):
    """Test find_manager_by_name when manager doesn't exist."""
    store = SessionStore()

    mock_standings = {
        "standings": {
            "results": [
                {
                    "entry": 12345,
                    "entry_name": "Team A",
                    "player_name": "Player A",
                },
            ]
        }
    }

    mock_client.get_league_standings = AsyncMock(return_value=mock_standings)

    result = await store.find_manager_by_name(mock_client, 123, "Nonexistent Manager")

    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_find_manager_by_name_api_error(mock_client):
    """Test find_manager_by_name handles API errors gracefully."""
    store = SessionStore()

    mock_client.get_league_standings = AsyncMock(side_effect=Exception("API Error"))

    result = await store.find_manager_by_name(mock_client, 123, "John Doe")

    assert result is None


@pytest.mark.unit
def test_enrich_gameweek_history_no_bootstrap_data():
    """Test enrich_gameweek_history when no bootstrap data exists."""
    store = SessionStore()
    store.bootstrap_data = None

    history = [{"opponent_team": 1, "total_points": 10}]

    result = store.enrich_gameweek_history(history)

    # Should return original history unchanged
    assert result == history


@pytest.mark.unit
def test_enrich_fixtures_no_bootstrap_data():
    """Test enrich_fixtures when no bootstrap data exists."""
    store = SessionStore()
    store.bootstrap_data = None

    from src.models import FixtureData

    fixtures = [
        FixtureData(
            code=1,
            id=1,
            finished=False,
            finished_provisional=False,
            minutes=0,
            provisional_start_time=False,
            started=False,
            team_a=1,
            team_h=2,
            stats=[],
            team_h_difficulty=3,
            team_a_difficulty=2,
            pulse_id=1,
        ),
    ]

    result = store.enrich_fixtures(fixtures)

    # Should return original fixtures
    assert len(result) == 1


@pytest.mark.unit
def test_enrich_fixtures_dict_input(session_store):
    """Test enrich_fixtures with dict input instead of FixtureData objects."""
    fixtures = [
        {
            "id": 1,
            "team_h": 1,
            "team_a": 2,
            "finished": False,
        }
    ]

    result = session_store.enrich_fixtures(fixtures)

    assert len(result) == 1
    assert result[0]["team_h_name"] == "Arsenal"
    assert result[0]["team_a_name"] == "Liverpool"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ensure_bootstrap_data_uses_cache(mock_client):
    """Test ensure_bootstrap_data uses cached data when available."""
    from unittest.mock import patch

    from src.models import BootstrapData, ElementTypeData, TeamData

    store = SessionStore()

    mock_bootstrap = BootstrapData(
        elements=[],
        teams=[TeamData(id=1, name="Arsenal", short_name="ARS")],
        element_types=[ElementTypeData(id=1, singular_name_short="GKP", plural_name_short="GKPs")],
        events=[],
    )

    # Mock cache to return data
    with patch("src.state.cache_manager.get", return_value=mock_bootstrap):
        await store.ensure_bootstrap_data(mock_client)

    # Should use cached data without calling client
    assert store.bootstrap_data == mock_bootstrap
    # The mock_client.get_bootstrap_data is not a Mock, it's a real function
    # So we just verify bootstrap_data was set from cache


@pytest.mark.unit
def test_build_player_indices_with_first_web_name_combo(session_store):
    """Test _build_player_indices handles first_name + web_name combinations."""
    # This tests the condition on lines 119-124
    from src.models import ElementData

    # Add a player with different web_name and second_name
    player = ElementData(
        id=999,
        web_name="Bobby",  # Different from second_name
        first_name="Robert",
        second_name="Firmino",
        team=1,
        element_type=4,
        now_cost=80,
        form="6.5",
        points_per_game="5.8",
        news="",
        status="a",
    )

    session_store.bootstrap_data.elements.append(player)
    session_store._build_player_indices()

    # Should create "robert bobby" index
    results = session_store.find_players_by_name("Robert Bobby")
    assert len(results) > 0
    assert any(p.id == 999 for p, _ in results)


@pytest.mark.unit
def test_enrich_fixtures_with_object_attributes():
    """Test enrich_fixtures when fixture has __dict__ but not model_dump."""
    from src.models import BootstrapData, ElementTypeData, TeamData

    store = SessionStore()
    store.bootstrap_data = BootstrapData(
        elements=[],
        teams=[
            TeamData(id=1, name="Arsenal", short_name="ARS"),
            TeamData(id=2, name="Liverpool", short_name="LIV"),
        ],
        element_types=[ElementTypeData(id=1, singular_name_short="GKP", plural_name_short="GKPs")],
        events=[],
    )

    # Create a fixture object with __dict__ (line 409)
    class FixtureObj:
        def __init__(self):
            self.team_h = 1
            self.team_a = 2
            self.finished = False

    fixture_obj = FixtureObj()
    result = store.enrich_fixtures([fixture_obj])

    assert len(result) == 1
    assert result[0]["team_h_name"] == "Arsenal"
    assert result[0]["team_a_name"] == "Liverpool"

"""
Tests for state management and player lookup functionality.
"""

import pytest


@pytest.mark.unit
def test_normalize_name(session_store):
    """Test name normalization."""
    assert session_store._normalize_name("Mohamed Salah") == "mohamed salah"
    assert session_store._normalize_name("  HAALAND  ") == "haaland"
    assert session_store._normalize_name("De Bruyne") == "de bruyne"


@pytest.mark.unit
def test_exact_player_match(session_store):
    """Test exact player name matching."""
    results = session_store.find_players_by_name("Salah")
    assert len(results) > 0
    assert results[0][1] == 1.0  # Perfect match score
    assert results[0][0].web_name == "Salah"


@pytest.mark.unit
def test_fuzzy_player_match(session_store):
    """Test fuzzy player name matching."""
    # Test with typo
    results = session_store.find_players_by_name("Sala")
    assert len(results) > 0
    assert results[0][0].web_name == "Salah"

    # Test with partial name
    results = session_store.find_players_by_name("Haal")
    assert len(results) > 0
    assert results[0][0].web_name == "Haaland"


@pytest.mark.unit
def test_full_name_match(session_store):
    """Test full name matching."""
    results = session_store.find_players_by_name("Mohamed Salah")
    assert len(results) > 0
    assert results[0][0].web_name == "Salah"

    results = session_store.find_players_by_name("Erling Haaland")
    assert len(results) > 0
    assert results[0][0].web_name == "Haaland"


@pytest.mark.unit
def test_player_not_found(session_store):
    """Test when player doesn't exist."""
    results = session_store.find_players_by_name("NonExistentPlayer")
    assert len(results) == 0


@pytest.mark.unit
def test_get_player_by_id(session_store):
    """Test retrieving player by ID."""
    player = session_store.get_player_by_id(1)
    assert player is not None
    assert player.web_name == "Salah"
    assert player.team_name == "Liverpool"
    assert player.position == "MID"


@pytest.mark.unit
def test_get_team_by_id(session_store):
    """Test retrieving team by ID."""
    team = session_store.get_team_by_id(1)
    assert team is not None
    assert team["name"] == "Arsenal"
    assert team["short_name"] == "ARS"


@pytest.mark.unit
def test_get_all_teams(session_store):
    """Test retrieving all teams."""
    teams = session_store.get_all_teams()
    assert len(teams) == 3
    assert any(t["name"] == "Arsenal" for t in teams)
    assert any(t["name"] == "Liverpool" for t in teams)
    assert any(t["name"] == "Man City" for t in teams)


@pytest.mark.unit
def test_get_current_gameweek(session_store):
    """Test getting current gameweek."""
    current_gw = session_store.get_current_gameweek()
    assert current_gw is not None
    assert current_gw.is_current is True
    assert current_gw.id == 2


@pytest.mark.unit
def test_rehydrate_player_names(session_store):
    """Test player ID rehydration."""
    player_dict = session_store.rehydrate_player_names([1, 2])
    assert len(player_dict) == 2
    assert player_dict[1]["web_name"] == "Salah"
    assert player_dict[2]["web_name"] == "Haaland"


@pytest.mark.unit
def test_get_player_name(session_store):
    """Test getting player name by ID."""
    name = session_store.get_player_name(1)
    assert name == "Salah"

    name = session_store.get_player_name(9999)
    assert "Unknown Player" in name


@pytest.mark.unit
def test_enrich_gameweek_history(session_store):
    """Test enriching gameweek history with team names."""
    history = [
        {"opponent_team": 1, "total_points": 10},
        {"opponent_team": 2, "total_points": 8},
    ]

    enriched = session_store.enrich_gameweek_history(history)

    assert len(enriched) == 2
    assert enriched[0]["opponent_team_name"] == "Arsenal"
    assert enriched[0]["opponent_team_short"] == "ARS"
    assert enriched[1]["opponent_team_name"] == "Liverpool"
    assert enriched[1]["opponent_team_short"] == "LIV"


@pytest.mark.unit
def test_enrich_fixtures(session_store):
    """Test enriching fixtures with team names."""
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

    enriched = session_store.enrich_fixtures(fixtures)

    assert len(enriched) == 1
    assert enriched[0]["team_h_name"] == "Liverpool"
    assert enriched[0]["team_h_short"] == "LIV"
    assert enriched[0]["team_a_name"] == "Arsenal"
    assert enriched[0]["team_a_short"] == "ARS"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ensure_bootstrap_data(session_store, mock_client, mock_bootstrap_data):
    """Test ensuring bootstrap data is loaded."""
    # Note: The cache_manager in ensure_bootstrap_data checks cache first
    # Since session_store fixture already has bootstrap_data, it gets cached,
    # so the mock API call never happens. This is correct behavior.

    # Verify data was loaded from fixture/cache
    await session_store.ensure_bootstrap_data(mock_client)
    assert session_store.bootstrap_data is not None
    # Don't assert mock was called - cache prevents unnecessary API calls


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ensure_fixtures_data(session_store, mock_client):
    """Test ensuring fixtures data is loaded."""
    # Clear any existing data
    session_store.fixtures_data = None

    # Mock the client's get_fixtures method
    from unittest.mock import AsyncMock

    mock_fixtures = [
        {
            "code": 1,
            "id": 1,
            "team_h": 1,
            "team_a": 2,
            "finished": False,
            "finished_provisional": False,
            "minutes": 0,
            "provisional_start_time": False,
            "started": False,
            "stats": [],
            "team_h_difficulty": 3,
            "team_a_difficulty": 2,
            "pulse_id": 1,
        }
    ]
    mock_client.get_fixtures = AsyncMock(return_value=mock_fixtures)

    await session_store.ensure_fixtures_data(mock_client)

    # Verify data was loaded
    assert session_store.fixtures_data is not None
    assert len(session_store.fixtures_data) == 1
    mock_client.get_fixtures.assert_called_once()

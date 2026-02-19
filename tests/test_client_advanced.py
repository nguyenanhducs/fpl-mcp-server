"""
Additional tests to increase client.py coverage from 52% to 80%+
"""

from unittest.mock import AsyncMock

import pytest

from src.client import FPLClient
from src.models import BootstrapData, ElementData, ElementTypeData, EventData, TeamData
from src.state import SessionStore


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_players_with_store(session_store):
    """Test get_players when store has bootstrap data."""
    client = FPLClient(store=session_store)

    players = await client.get_players()

    assert len(players) == 3
    assert players[0].web_name == "Salah"
    assert players[0].team_name == "Liverpool"
    assert players[0].position == "MID"
    assert players[0].price == 13.0  # 130 / 10


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_players_without_store():
    """Test get_players when no store is available (fallback to API)."""
    client = FPLClient()

    # Mock the bootstrap API call
    mock_data = {
        "elements": [
            {
                "id": 1,
                "web_name": "Kane",
                "first_name": "Harry",
                "second_name": "Kane",
                "team": 1,
                "element_type": 4,
                "now_cost": 115,
                "form": "7.0",
                "points_per_game": "6.5",
                "news": "",
            }
        ],
        "teams": [{"id": 1, "name": "Spurs", "short_name": "TOT"}],
        "element_types": [{"id": 4, "singular_name_short": "FWD", "plural_name_short": "FWDs"}],
    }

    client.get_bootstrap_data = AsyncMock(return_value=mock_data)

    players = await client.get_players()

    assert len(players) == 1
    assert players[0].web_name == "Kane"
    assert players[0].team_name == "Spurs"
    assert players[0].position == "FWD"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_players_without_store_no_bootstrap():
    """Test get_players fetches from API when store has no bootstrap data."""
    store = SessionStore()
    # Store exists but has no bootstrap data
    store.bootstrap_data = None

    client = FPLClient(store=store)

    mock_data = {
        "elements": [
            {
                "id": 2,
                "web_name": "Bruno",
                "first_name": "Bruno",
                "second_name": "Fernandes",
                "team": 2,
                "element_type": 3,
                "now_cost": 105,
                "form": "8.0",
                "points_per_game": "7.0",
                "news": "",
            }
        ],
        "teams": [{"id": 2, "name": "Man Utd", "short_name": "MUN"}],
        "element_types": [{"id": 3, "singular_name_short": "MID", "plural_name_short": "MIDs"}],
    }

    client.get_bootstrap_data = AsyncMock(return_value=mock_data)

    players = await client.get_players()

    assert len(players) == 1
    assert players[0].web_name == "Bruno"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_top_players_by_position_with_data(session_store):
    """Test get_top_players_by_position with bootstrap data available."""
    client = FPLClient(store=session_store)

    result = await client.get_top_players_by_position()

    # Should have all position keys
    assert "GKP" in result
    assert "DEF" in result
    assert "MID" in result
    assert "FWD" in result

    # Check that MID has players (we have Salah and Saka as MID in fixtures)
    assert len(result["MID"]) > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_top_players_by_position_no_store():
    """Test get_top_players_by_position when no store is available."""
    client = FPLClient()

    result = await client.get_top_players_by_position()

    # Should return empty dict for all positions
    assert result == {"GKP": [], "DEF": [], "MID": [], "FWD": []}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_top_players_by_position_no_bootstrap_data():
    """Test get_top_players_by_position when store has no bootstrap data."""
    store = SessionStore()
    store.bootstrap_data = None

    client = FPLClient(store=store)

    result = await client.get_top_players_by_position()

    # Should return empty dict for all positions
    assert result == {"GKP": [], "DEF": [], "MID": [], "FWD": []}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_top_players_sorting():
    """Test that get_top_players_by_position sorts by points_per_game."""
    store = SessionStore()

    # Create test data with different PPG values
    elements = [
        ElementData(
            id=1,
            web_name="Player1",
            first_name="First",
            second_name="Player1",
            team=1,
            element_type=3,  # MID
            now_cost=100,
            form="5.0",
            points_per_game="3.0",
            news="",
            status="a",
        ),
        ElementData(
            id=2,
            web_name="Player2",
            first_name="Second",
            second_name="Player2",
            team=1,
            element_type=3,  # MID
            now_cost=110,
            form="7.0",
            points_per_game="8.5",  # Highest
            news="",
            status="a",
        ),
        ElementData(
            id=3,
            web_name="Player3",
            first_name="Third",
            second_name="Player3",
            team=1,
            element_type=3,  # MID
            now_cost=90,
            form="6.0",
            points_per_game="5.2",
            news="",
            status="a",
        ),
    ]

    teams = [TeamData(id=1, name="Arsenal", short_name="ARS")]
    element_types = [ElementTypeData(id=3, singular_name_short="MID", plural_name_short="MIDs")]
    events = [
        EventData(
            id=1,
            name="GW1",
            deadline_time="2024-08-16T17:30:00Z",
            finished=False,
            data_checked=False,
            deadline_time_epoch=1692203400,
            is_previous=False,
            is_current=True,
            is_next=False,
            can_enter=True,
            released=True,
        )
    ]

    store.bootstrap_data = BootstrapData(
        elements=elements,
        teams=teams,
        element_types=element_types,
        events=events,
    )

    client = FPLClient(store=store)

    result = await client.get_top_players_by_position()

    # MID should be sorted by PPG descending
    assert len(result["MID"]) == 3
    assert result["MID"][0]["name"] == "Player2"  # 8.5 PPG
    assert result["MID"][1]["name"] == "Player3"  # 5.2 PPG
    assert result["MID"][2]["name"] == "Player1"  # 3.0 PPG


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_top_players_limits():
    """Test that get_top_players_by_position respects position limits."""
    store = SessionStore()

    # Create 30 GKP players
    elements = []
    for i in range(30):
        elements.append(
            ElementData(
                id=i + 1,
                web_name=f"GK{i + 1}",
                first_name="Keeper",
                second_name=f"Number{i + 1}",
                team=1,
                element_type=1,  # GKP
                now_cost=45,
                form="5.0",
                points_per_game=str(30 - i),  # Descending PPG
                news="",
                status="a",
            )
        )

    teams = [TeamData(id=1, name="Arsenal", short_name="ARS")]
    element_types = [ElementTypeData(id=1, singular_name_short="GKP", plural_name_short="GKPs")]
    events = [
        EventData(
            id=1,
            name="GW1",
            deadline_time="2024-08-16T17:30:00Z",
            finished=False,
            data_checked=False,
            deadline_time_epoch=1692203400,
            is_previous=False,
            is_current=True,
            is_next=False,
            can_enter=True,
            released=True,
        )
    ]

    store.bootstrap_data = BootstrapData(
        elements=elements,
        teams=teams,
        element_types=element_types,
        events=events,
    )

    client = FPLClient(store=store)

    result = await client.get_top_players_by_position()

    # Should return only top 5 GKP
    assert len(result["GKP"]) == 5
    assert result["GKP"][0]["name"] == "GK1"  # Highest PPG


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_top_players_ppg_value_error():
    """Test that get_top_players_by_position handles invalid PPG values."""
    store = SessionStore()

    elements = [
        ElementData(
            id=1,
            web_name="Player1",
            first_name="First",
            second_name="Player1",
            team=1,
            element_type=4,  # FWD
            now_cost=100,
            form="5.0",
            points_per_game="invalid",  # Invalid value
            news="",
            status="a",
        ),
        ElementData(
            id=2,
            web_name="Player2",
            first_name="Second",
            second_name="Player2",
            team=1,
            element_type=4,  # FWD
            now_cost=110,
            form="7.0",
            points_per_game="",  # Empty string
            news="",
            status="a",
        ),
    ]

    teams = [TeamData(id=1, name="Arsenal", short_name="ARS")]
    element_types = [ElementTypeData(id=4, singular_name_short="FWD", plural_name_short="FWDs")]
    events = [
        EventData(
            id=1,
            name="GW1",
            deadline_time="2024-08-16T17:30:00Z",
            finished=False,
            data_checked=False,
            deadline_time_epoch=1692203400,
            is_previous=False,
            is_current=True,
            is_next=False,
            can_enter=True,
            released=True,
        )
    ]

    store.bootstrap_data = BootstrapData(
        elements=elements,
        teams=teams,
        element_types=element_types,
        events=events,
    )

    client = FPLClient(store=store)

    result = await client.get_top_players_by_position()

    # Should handle invalid PPG gracefully and default to 0.0
    assert len(result["FWD"]) == 2
    # Both should have ppg of 0.0
    for player in result["FWD"]:
        assert player["points_per_game"] == 0.0

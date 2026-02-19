"""
Tests for FPL API client in src/client.py
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.client import FPLClient
from src.state import SessionStore


@pytest.mark.unit
class TestFPLClientInitialization:
    """Test FPLClient initialization."""

    def test_client_creation_without_store(self):
        """Test creating client without store."""
        client = FPLClient()

        assert client.session is not None
        assert client._store is None

    def test_client_creation_with_store(self):
        """Test creating client with store."""
        store = SessionStore()
        client = FPLClient(store=store)

        assert client._store is store

    def test_client_has_base_url(self):
        """Test that client has correct base URL."""
        client = FPLClient()

        assert client.BASE_URL == "https://fantasy.premierleague.com/api/"


@pytest.mark.unit
class TestFPLClientClose:
    """Test FPLClient close method."""

    @pytest.mark.asyncio
    async def test_close_method(self):
        """Test that close method closes the session."""
        client = FPLClient()

        # Mock the session close method
        client.session.aclose = AsyncMock()

        await client.close()

        client.session.aclose.assert_called_once()


@pytest.mark.unit
class TestFPLClientRequest:
    """Test FPLClient _request method."""

    @pytest.mark.asyncio
    async def test_request_get(self):
        """Test making a GET request."""
        client = FPLClient()

        # Mock the session request
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = MagicMock()

        client.session.request = AsyncMock(return_value=mock_response)

        result = await client._request("GET", "test-endpoint")

        assert result == {"data": "test"}
        client.session.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_with_params(self):
        """Test making request with query parameters."""
        client = FPLClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = MagicMock()

        client.session.request = AsyncMock(return_value=mock_response)

        await client._request("GET", "test", params={"page": 1})

        # Verify params were passed
        call_args = client.session.request.call_args
        assert call_args[1]["params"] == {"page": 1}

    @pytest.mark.asyncio
    async def test_request_with_data(self):
        """Test making request with data payload."""
        client = FPLClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = MagicMock()

        client.session.request = AsyncMock(return_value=mock_response)

        await client._request("POST", "test", data={"key": "value"})

        # Verify data was passed
        call_args = client.session.request.call_args
        assert call_args[1]["json"] == {"key": "value"}


@pytest.mark.unit
class TestFPLClientBootstrapData:
    """Test FPLClient get_bootstrap_data method."""

    @pytest.mark.asyncio
    async def test_get_bootstrap_data(self):
        """Test fetching bootstrap data."""
        client = FPLClient()

        mock_data = {
            "elements": [],
            "teams": [],
            "element_types": [],
            "events": [],
        }

        client._request = AsyncMock(return_value=mock_data)

        result = await client.get_bootstrap_data()

        assert result == mock_data
        client._request.assert_called_once_with("GET", "bootstrap-static/")


@pytest.mark.unit
class TestFPLClientFixtures:
    """Test FPLClient get_fixtures method."""

    @pytest.mark.asyncio
    async def test_get_fixtures(self):
        """Test fetching fixtures."""
        client = FPLClient()

        mock_fixtures = [
            {"id": 1, "team_h": 1, "team_a": 2},
            {"id": 2, "team_h": 3, "team_a": 4},
        ]

        client._request = AsyncMock(return_value=mock_fixtures)

        result = await client.get_fixtures()

        assert result == mock_fixtures
        client._request.assert_called_once_with("GET", "fixtures/")


@pytest.mark.unit
class TestFPLClientElementSummary:
    """Test FPLClient get_element_summary method."""

    @pytest.mark.asyncio
    async def test_get_element_summary(self):
        """Test fetching player element summary."""
        client = FPLClient()

        mock_summary = {
            "fixtures": [],
            "history": [],
            "history_past": [],
        }

        client._request = AsyncMock(return_value=mock_summary)

        result = await client.get_element_summary(123)

        assert result == mock_summary
        client._request.assert_called_once_with("GET", "element-summary/123/")


@pytest.mark.unit
class TestFPLClientManagerEntry:
    """Test FPLClient get_manager_entry method."""

    @pytest.mark.asyncio
    async def test_get_manager_entry(self):
        """Test fetching manager entry."""
        client = FPLClient()

        mock_entry = {
            "id": 12345,
            "player_first_name": "John",
            "player_last_name": "Doe",
        }

        client._request = AsyncMock(return_value=mock_entry)

        result = await client.get_manager_entry(12345)

        assert result == mock_entry
        client._request.assert_called_once_with("GET", "entry/12345/")


@pytest.mark.unit
class TestFPLClientLeagueStandings:
    """Test FPLClient get_league_standings method."""

    @pytest.mark.asyncio
    async def test_get_league_standings_default_params(self):
        """Test fetching league standings with default parameters."""
        client = FPLClient()

        mock_standings = {
            "league": {"id": 123, "name": "Test League"},
            "standings": {"results": []},
        }

        client._request = AsyncMock(return_value=mock_standings)

        result = await client.get_league_standings(123)

        assert result == mock_standings
        client._request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_league_standings_custom_params(self):
        """Test fetching league standings with custom parameters."""
        client = FPLClient()

        client._request = AsyncMock(return_value={})

        await client.get_league_standings(
            league_id=123, page_standings=2, page_new_entries=3, phase=2
        )

        # Verify the endpoint was called with params
        call_args = client._request.call_args
        assert "params" in call_args[1]
        params = call_args[1]["params"]
        assert params["page_standings"] == 2
        assert params["page_new_entries"] == 3
        assert params["phase"] == 2


@pytest.mark.unit
class TestFPLClientGameweekPicks:
    """Test FPLClient get_manager_gameweek_picks method."""

    @pytest.mark.asyncio
    async def test_get_manager_gameweek_picks(self):
        """Test fetching manager gameweek picks."""
        client = FPLClient()

        mock_picks = {
            "active_chip": None,
            "automatic_subs": [],
            "entry_history": {},
            "picks": [],
        }

        client._request = AsyncMock(return_value=mock_picks)

        result = await client.get_manager_gameweek_picks(12345, 10)

        assert result == mock_picks
        client._request.assert_called_once_with("GET", "entry/12345/event/10/picks/")


@pytest.mark.unit
class TestFPLClientManagerTransfers:
    """Test FPLClient get_manager_transfers method."""

    @pytest.mark.asyncio
    async def test_get_manager_transfers(self):
        """Test fetching manager transfers."""
        client = FPLClient()

        mock_transfers = [
            {"element_in": 100, "element_out": 200, "event": 5},
            {"element_in": 150, "element_out": 250, "event": 7},
        ]

        client._request = AsyncMock(return_value=mock_transfers)

        result = await client.get_manager_transfers(12345)

        assert result == mock_transfers
        client._request.assert_called_once_with("GET", "entry/12345/transfers/")


@pytest.mark.unit
class TestFPLClientManagerHistory:
    """Test FPLClient get_manager_history method."""

    @pytest.mark.asyncio
    async def test_get_manager_history(self):
        """Test fetching manager history."""
        client = FPLClient()

        mock_history = {
            "current": [],
            "past": [],
            "chips": [],
        }

        client._request = AsyncMock(return_value=mock_history)

        result = await client.get_manager_history(12345)

        assert result == mock_history
        client._request.assert_called_once_with("GET", "entry/12345/history/")


@pytest.mark.unit
class TestFPLClientGetCurrentGameweek:
    """Test FPLClient get_current_gameweek method."""

    @pytest.mark.asyncio
    async def test_get_current_gameweek_with_next(self):
        """Test getting current gameweek when is_next exists."""
        client = FPLClient()

        # Mock the get_bootstrap_data method
        mock_data = {
            "events": [
                {"id": 9, "is_next": False},
                {"id": 10, "is_next": True},
                {"id": 11, "is_next": False},
            ]
        }

        client.get_bootstrap_data = AsyncMock(return_value=mock_data)

        result = await client.get_current_gameweek()

        assert result == 10

    @pytest.mark.asyncio
    async def test_get_current_gameweek_no_next(self):
        """Test getting current gameweek when no is_next exists."""
        client = FPLClient()

        # Mock data with no is_next
        mock_data = {
            "events": [
                {"id": 38, "is_next": False},
            ]
        }

        client.get_bootstrap_data = AsyncMock(return_value=mock_data)

        result = await client.get_current_gameweek()

        assert result == 38

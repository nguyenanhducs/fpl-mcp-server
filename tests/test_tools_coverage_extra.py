from unittest.mock import AsyncMock, patch

import pytest

from src.tools.leagues import GetLeagueStandingsInput, fpl_get_league_standings
from src.tools.transfers import (
    GetManagerTransfersByGameweekInput,
    GetTopTransferredPlayersInput,
    fpl_get_manager_transfers_by_gameweek,
    fpl_get_top_transferred_players,
)


@pytest.mark.asyncio
class TestExtraCoverage:
    """Extra coverage tests."""

    async def test_fpl_get_manager_transfers_error(self, session_store):
        """Test manager transfers API error."""
        params = GetManagerTransfersByGameweekInput(team_id=12345, gameweek=2)

        with patch(
            "src.tools.transfers._create_client", new_callable=AsyncMock
        ) as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client

            mock_client.get_manager_entry.side_effect = Exception("API Error")
            # Should catch and fallback to defaults names, then continue or fail elsewhere?
            # get_manager_transfers might also fail
            mock_client.get_manager_transfers.side_effect = Exception("Transfers API Error")

            result = await fpl_get_manager_transfers_by_gameweek(params)

            assert "Error" in result

    async def test_fpl_get_top_transferred_players_no_transfers(self, session_store):
        """Test top transferred when no transfers."""
        params = GetTopTransferredPlayersInput()

        # Mock bootstrap data elements with 0 transfers
        # session_store uses mock_bootstrap_data where elements have transfers_in_event=0?
        # Check conftest: elements have transfers_in_event=10000 etc.
        # We need to set them to 0.

        # Directly modify session_store elements?
        for p in session_store.bootstrap_data.elements:
            p.transfers_in_event = 0
            p.transfers_out_event = 0

        with patch(
            "src.tools.transfers._create_client", new_callable=AsyncMock
        ) as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client

            result = await fpl_get_top_transferred_players(params)

            assert "No transfer data available" in result

    async def test_fpl_get_league_standings_error(self, session_store):
        """Test league standings API error."""
        params = GetLeagueStandingsInput(league_id=999)

        with patch(
            "src.tools.leagues._create_client", new_callable=AsyncMock
        ) as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client

            mock_client.get_league_standings.side_effect = Exception("League Not Found")

            result = await fpl_get_league_standings(params)

            assert "Error" in result or "League Not Found" in result

    async def test_fpl_get_manager_transfers_coverage(self, session_store):
        """Test manager transfers with populated list to hit loop."""
        params = GetManagerTransfersByGameweekInput(team_id=12345, gameweek=2)

        # Explicit mock data matching logic
        # element_in=1 (Salah), element_out=2 (Saka) in mock_players?
        # mock_players in conftest: element 1 is Salah, element 2 is Saka.

        mock_transfers = [
            {
                "id": 100,
                "event": 2,
                "time": "2024-08-23T10:00:00Z",
                "element_in": 1,
                "element_out": 2,
                "element_in_cost": 125,
                "element_out_cost": 100,
                "entry": 12345,
                "event_cost": 4,
            }
        ]

        with patch(
            "src.tools.transfers._create_client", new_callable=AsyncMock
        ) as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client

            mock_client.get_manager_transfers.return_value = mock_transfers

            # mock manager entry for name
            mock_client.get_manager_entry.return_value = {
                "player_first_name": "Test",
                "player_last_name": "User",
                "name": "FC Test",
            }

            result = await fpl_get_manager_transfers_by_gameweek(params)

            assert "FC Test" in result
            assert "OUT:" in result
            assert "IN:" in result
            assert "Cost: -4 points" in result

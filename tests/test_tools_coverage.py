from unittest.mock import AsyncMock, patch

import pytest

from src.tools.transfers import (
    AnalyzeTransferInput,
    GetManagerChipsInput,
    fpl_analyze_transfer,
    fpl_get_manager_chips,
)
from src.utils import ResponseFormat


@pytest.mark.asyncio
class TestTransferCoverage:
    """Coverage tests for transfer tools."""

    async def test_fpl_analyze_transfer_basic(self, session_store, mock_element_summary):
        """Test analyzing a valid transfer."""
        params = AnalyzeTransferInput(player_out="Salah", player_in="Saka")

        # Create mock summaries for both players
        summary_out = mock_element_summary.copy()
        summary_in = mock_element_summary.copy()

        # Ensure they have same position (Element 3 = MID)
        # mock_players in conftest usually sets element_type=3 for Salah (ID 1), Saka (ID 2)
        # Check conftest:
        # Salah id=1, type=3. Saka id=2, type=3.
        # But wait, find_players_by_name uses mock_players.
        # params player_out="Salah" -> finds Salah.
        # params player_in="Saka" -> finds Saka.

        with patch(
            "src.tools.transfers._create_client", new_callable=AsyncMock
        ) as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client

            mock_client.get_element_summary.side_effect = [summary_out, summary_in]

            result = await fpl_analyze_transfer(params)

            assert "Transfer Analysis" in result
            assert "Salah" in result
            assert "Saka" in result
            assert "Recommendation" in result

    async def test_fpl_analyze_transfer_invalid_position(self, session_store):
        """Test analyzing transfer with different positions."""
        params = AnalyzeTransferInput(player_out="Salah", player_in="Haaland")
        # Salah=MID(3), Haaland=FWD(4) in typical mock data.
        # Need to ensure Haaland exists in mock_players with type 4.

        # Using mock_players from conftest:
        # ID 1: Salah (3)
        # ID 2: Saka (3)
        # ID 3: Haaland (4)

        with patch(
            "src.tools.transfers._create_client", new_callable=AsyncMock
        ) as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client

            result = await fpl_analyze_transfer(params)

            assert "Invalid transfer" in result
            assert "must be between players of the same position" in result

    async def test_fpl_analyze_transfer_json(self, session_store, mock_element_summary):
        """Test analyze transfer JSON output."""
        params = AnalyzeTransferInput(
            player_out="Salah", player_in="Saka", response_format=ResponseFormat.JSON
        )

        with patch(
            "src.tools.transfers._create_client", new_callable=AsyncMock
        ) as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client

            mock_client.get_element_summary.return_value = mock_element_summary

            result = await fpl_analyze_transfer(params)

            assert "{" in result
            assert "analysis" in result
            assert "recommendation" in result

    async def test_fpl_get_manager_chips_json(self, session_store, mock_manager_history):
        """Test getting manager chips in JSON."""
        params = GetManagerChipsInput(team_id=12345, response_format=ResponseFormat.JSON)

        with patch(
            "src.tools.transfers._create_client", new_callable=AsyncMock
        ) as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client

            mock_client.get_manager_history.return_value = mock_manager_history

            result = await fpl_get_manager_chips(params)

            assert "{" in result
            assert "used_chips" in result
            assert "available_chips" in result

    async def test_fpl_get_manager_chips_none_used(self, session_store):
        """Test manager chips when none used."""
        params = GetManagerChipsInput(team_id=12345)

        mock_history = {"chips": []}

        with patch(
            "src.tools.transfers._create_client", new_callable=AsyncMock
        ) as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client

            mock_client.get_manager_history.return_value = mock_history

            result = await fpl_get_manager_chips(params)

            assert "No chips used yet" in result
            assert "Available Chips" in result

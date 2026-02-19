from unittest.mock import AsyncMock, patch

import pytest

from src.prompts.gameweek_analysis import gameweek_analysis


@pytest.mark.asyncio
async def test_gameweek_analysis_prompt():
    """Test that gameweek analysis prompt calls dependencies and formats output correctly."""

    # Mock dependencies
    with (
        patch("src.prompts.gameweek_analysis.store") as mock_store,
        patch(
            "src.prompts.gameweek_analysis.fpl_get_fixtures_for_gameweek", new_callable=AsyncMock
        ) as mock_get_fixtures,
        patch(
            "src.prompts.gameweek_analysis.fpl_find_fixture_opportunities", new_callable=AsyncMock
        ) as mock_find_opportunities,
    ):
        # Setup mock returns
        mock_store.get_current_gameweek.return_value.id = 5
        mock_get_fixtures.return_value = "Detailed Match Reports Content"
        mock_find_opportunities.return_value = "Top Teams: Arsenal, Liverpool"

        # Call prompt
        result = await gameweek_analysis(gameweek=None)

        # Verify calls
        mock_store.get_current_gameweek.assert_called_once()
        mock_get_fixtures.assert_called_once()
        mock_find_opportunities.assert_called_once()

        # Check call arguments
        fixtures_call_arg = mock_get_fixtures.call_args[0][0]
        assert fixtures_call_arg.gameweek == 5
        assert fixtures_call_arg.detailed is True

        ops_call_arg = mock_find_opportunities.call_args[0][0]
        assert ops_call_arg.num_gameweeks == 5
        assert ops_call_arg.max_teams == 5

        # Verify output content
        assert "Gameweek 5" in result
        assert "Detailed Match Reports Content" in result
        assert "Upcoming Fixture Context" in result
        assert "Top Teams: Arsenal, Liverpool" in result

        assert "cross-reference" in result.lower()
        assert "fixture-proof" in result
        assert "trap" in result.lower()

        # Check for tool strategy
        assert "Tool Calls Strategy" in result
        assert "fpl_get_player_details" in result
        assert "fpl_compare_players" in result

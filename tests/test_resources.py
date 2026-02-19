"""
Integration tests for FPL MCP Resource endpoints.

Tests MCP resource endpoints for bootstrap data (players, teams, gameweeks).
"""

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
class TestBootstrapResources:
    """Integration tests for bootstrap resource endpoints."""

    async def test_get_all_players_resource(self, session_store):
        """Test getting all players resource."""
        from src.resources.bootstrap import get_all_players_resource

        # Act
        result = await get_all_players_resource()

        # Assert
        assert "All FPL Players" in result
        assert "GKP" in result or "DEF" in result or "MID" in result or "FWD" in result
        assert "total" in result

    async def test_get_all_teams_resource(self, session_store):
        """Test getting all teams resource."""
        from src.resources.bootstrap import get_all_teams_resource

        # Act
        result = await get_all_teams_resource()

        # Assert
        # Actual output format: "**Premier League Teams:**" (no "All" prefix)
        assert "Premier League Teams" in result
        assert "Arsenal" in result or "Liverpool" in result or "Man City" in result
        assert "Strength" in result or "strength" in result

    async def test_get_all_gameweeks_resource(self, session_store):
        """Test getting all gameweeks resource."""
        from src.resources.bootstrap import get_all_gameweeks_resource

        # Act
        result = await get_all_gameweeks_resource()

        # Assert
        assert "All Gameweeks" in result or "FPL Gameweeks" in result
        assert "Gameweek" in result
        assert "Deadline" in result or "deadline" in result

    async def test_get_current_gameweek_resource(self, session_store):
        """Test getting current gameweek resource."""
        from src.resources.bootstrap import get_current_gameweek_resource

        # Act
        result = await get_current_gameweek_resource()

        # Assert
        assert "Gameweek" in result
        # Should show current/upcoming/finished status
        assert (
            "Current" in result
            or "Upcoming" in result
            or "Finished" in result
            or "current" in result
            or "upcoming" in result
            or "finished" in result
            or "Status" in result
        )

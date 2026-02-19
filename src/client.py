import logging
from typing import TYPE_CHECKING, Any, Optional

import httpx

from .constants import (
    TOP_DEFENDERS_COUNT,
    TOP_FORWARDS_COUNT,
    TOP_GOALKEEPERS_COUNT,
    TOP_MIDFIELDERS_COUNT,
    PlayerPosition,
)
from .models import Player
from .rate_limiter import rate_limiter

if TYPE_CHECKING:
    from .state import SessionStore

logger = logging.getLogger("fpl_client")


class FPLClient:
    BASE_URL = "https://fantasy.premierleague.com/api/"

    def __init__(self, store: Optional["SessionStore"] = None):
        self.session = httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}, timeout=30.0)
        self._store = store

    async def _request(
        self, method: str, endpoint: str, data: dict = None, params: dict = None
    ) -> Any:
        """Make HTTP request to FPL API (public endpoints only)."""
        url = f"{self.BASE_URL}{endpoint}"
        # Acquire rate limit token before making request
        await rate_limiter.acquire()

        if method == "GET":
            response = await self.session.get(url, params=params)
        else:
            response = await self.session.post(url, json=data)

        response.raise_for_status()
        return response.json()

    async def get_bootstrap_data(self) -> dict[str, Any]:
        """Fetch fresh bootstrap data from API"""
        return await self._request("GET", "bootstrap-static/")

    async def get_fixtures(self) -> list[dict[str, Any]]:
        """Fetch fixtures data from API"""
        return await self._request("GET", "fixtures/")

    async def get_element_summary(self, player_id: int) -> dict[str, Any]:
        """
        Fetch detailed player summary including fixtures, history, and past seasons.

        Args:
            player_id: The FPL player ID (element ID)

        Returns:
            Dictionary containing fixtures, history, and history_past
        """
        return await self._request("GET", f"element-summary/{player_id}/")

    async def get_manager_entry(self, team_id: int) -> dict[str, Any]:
        """
        Fetch FPL manager/team entry information.

        Args:
            team_id: The FPL manager's team ID (entry ID)

        Returns:
            Dictionary containing manager details, leagues, and team information
        """
        return await self._request("GET", f"entry/{team_id}/")

    async def get_league_standings(
        self,
        league_id: int,
        page_standings: int = 1,
        page_new_entries: int = 1,
        phase: int = 1,
    ) -> dict[str, Any]:
        """
        Fetch league standings for a classic league.

        Args:
            league_id: The league ID
            page_standings: Page number for standings (default: 1)
            page_new_entries: Page number for new entries (default: 1)
            phase: Phase/season number (default: 1)

        Returns:
            Dictionary containing league info and standings with entries
        """
        params = {
            "page_standings": page_standings,
            "page_new_entries": page_new_entries,
            "phase": phase,
        }
        return await self._request("GET", f"leagues-classic/{league_id}/standings/", params=params)

    async def get_manager_gameweek_picks(self, team_id: int, gameweek: int) -> dict[str, Any]:
        """
        Fetch a manager's team picks for a specific gameweek.

        Args:
            team_id: The FPL manager's team ID (entry ID)
            gameweek: The gameweek number (event ID)

        Returns:
            Dictionary containing picks, automatic subs, and entry history for the gameweek
        """
        return await self._request("GET", f"entry/{team_id}/event/{gameweek}/picks/")

    async def get_manager_transfers(self, team_id: int) -> list[dict[str, Any]]:
        """
        Fetch a manager's complete transfer history.

        Args:
            team_id: The FPL manager's team ID (entry ID)

        Returns:
            List of transfer records, each containing transfer details and timing
        """
        return await self._request("GET", f"entry/{team_id}/transfers/")

    async def get_manager_history(self, team_id: int) -> dict[str, Any]:
        """
        Fetch a manager's history including used chips.

        Args:
            team_id: The FPL manager's team ID (entry ID)

        Returns:
            Dictionary containing current, past, and chips data
        """
        return await self._request("GET", f"entry/{team_id}/history/")

    async def get_fixture_stats(self, fixture_id: int) -> dict[str, Any]:
        """
        Fetch detailed player statistics for a specific fixture.

        Args:
            fixture_id: The fixture ID

        Returns:
            Dictionary containing 'a' (away) and 'h' (home) player stats lists,
            each with detailed metrics including goals, assists, xG, xA, xGI, etc.
        """
        return await self._request("GET", f"fixture/{fixture_id}/stats/")

    async def get_players(self) -> list[Player]:
        """Get all players using in-memory bootstrap data"""
        # Use in-memory data if available
        if self._store and self._store.bootstrap_data:
            data = self._store.bootstrap_data
            teams = {t.id: t.name for t in data.teams}
            types = {t.id: t.singular_name_short for t in data.element_types}

            players = []
            for element in data.elements:
                # Convert ElementData to Player
                player = Player(
                    id=element.id,
                    web_name=element.web_name,
                    first_name=element.first_name,
                    second_name=element.second_name,
                    team=element.team,
                    element_type=element.element_type,
                    now_cost=element.now_cost,
                    form=element.form,
                    points_per_game=element.points_per_game,
                    news=element.news,
                )
                player.team_name = teams.get(player.team, "Unknown")
                player.position = types.get(player.element_type, "Unk")
                players.append(player)
            return players

        # Fallback to API if in-memory data not available
        logger.warning("Bootstrap data not loaded, fetching from API")
        data = await self.get_bootstrap_data()
        teams = {t["id"]: t["name"] for t in data["teams"]}
        types = {t["id"]: t["singular_name_short"] for t in data["element_types"]}

        players = []
        for p in data["elements"]:
            player = Player(**p)
            player.team_name = teams.get(player.team, "Unknown")
            player.position = types.get(player.element_type, "Unk")
            players.append(player)
        return players

    async def get_top_players_by_position(self) -> dict[str, list[dict[str, Any]]]:
        """
        Get top players by position based on points per game.
        Returns: {
            'GKP': [top 5 goalkeepers],
            'DEF': [top 20 defenders],
            'MID': [top 20 midfielders],
            'FWD': [top 20 forwards]
        }
        """
        if not self._store or not self._store.bootstrap_data:
            logger.warning("Bootstrap data not available for top players")
            return {
                PlayerPosition.GOALKEEPER.value: [],
                PlayerPosition.DEFENDER.value: [],
                PlayerPosition.MIDFIELDER.value: [],
                PlayerPosition.FORWARD.value: [],
            }

        data = self._store.bootstrap_data
        teams = {t.id: t.name for t in data.teams}
        types = {t.id: t.singular_name_short for t in data.element_types}

        # Group players by position
        players_by_position = {
            PlayerPosition.GOALKEEPER.value: [],
            PlayerPosition.DEFENDER.value: [],
            PlayerPosition.MIDFIELDER.value: [],
            PlayerPosition.FORWARD.value: [],
        }

        for element in data.elements:
            # Only include available players
            # if element.status != 'a':
            #    continue

            position = types.get(element.element_type, "UNK")
            if position not in players_by_position:
                continue

            # Convert to float for sorting, handle 0.0 as string
            try:
                ppg = float(element.points_per_game) if element.points_per_game else 0.0
            except ValueError:
                ppg = 0.0

            player_data = {
                "id": element.id,
                "name": element.web_name,
                "full_name": f"{element.first_name} {element.second_name}",
                "team": teams.get(element.team, "Unknown"),
                "price": element.now_cost / 10,
                "points_per_game": ppg,
                "total_points": getattr(element, "total_points", 0),
                "form": element.form,
                "status": element.status,
                "news": element.news if element.news else "",
            }
            players_by_position[position].append(player_data)

        # Sort by points_per_game and take top N
        result = {
            PlayerPosition.GOALKEEPER.value: sorted(
                players_by_position[PlayerPosition.GOALKEEPER.value],
                key=lambda x: x["points_per_game"],
                reverse=True,
            )[:TOP_GOALKEEPERS_COUNT],
            PlayerPosition.DEFENDER.value: sorted(
                players_by_position[PlayerPosition.DEFENDER.value],
                key=lambda x: x["points_per_game"],
                reverse=True,
            )[:TOP_DEFENDERS_COUNT],
            PlayerPosition.MIDFIELDER.value: sorted(
                players_by_position[PlayerPosition.MIDFIELDER.value],
                key=lambda x: x["points_per_game"],
                reverse=True,
            )[:TOP_MIDFIELDERS_COUNT],
            PlayerPosition.FORWARD.value: sorted(
                players_by_position[PlayerPosition.FORWARD.value],
                key=lambda x: x["points_per_game"],
                reverse=True,
            )[:TOP_FORWARDS_COUNT],
        }

        return result

    async def get_current_gameweek(self) -> int:
        """Get the current gameweek number."""
        data = await self.get_bootstrap_data()
        for event in data["events"]:
            if event["is_next"]:
                return event["id"]
        return 38

    async def close(self):
        await self.session.aclose()

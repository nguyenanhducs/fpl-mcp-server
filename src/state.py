from difflib import SequenceMatcher
import logging

from .cache import cache_manager
from .client import FPLClient
from .config import settings
from .constants import (
    FUZZY_MATCH_PENALTY,
    FUZZY_MATCH_THRESHOLD,
    PERFECT_MATCH_SCORE,
    SUBSTRING_MATCH_PENALTY,
)
from .models import BootstrapData, ElementData, EventData, FixtureData

logger = logging.getLogger("fpl_state")


class SessionStore:
    def __init__(self):
        # Bootstrap data loaded on-demand from API
        self.bootstrap_data: BootstrapData | None = None

        # Fixtures data loaded on-demand from API
        self.fixtures_data: list[FixtureData] | None = None

        # Player name lookup maps for intelligent searching
        # Maps normalized name -> list of player IDs (handles duplicates)
        self.player_name_map: dict[str, list[int]] = {}
        self.player_id_map: dict[int, ElementData] = {}

    def _normalize_name(self, name: str) -> str:
        """Normalize a name for matching: lowercase, remove extra spaces"""
        return " ".join(name.lower().strip().split())

    async def ensure_bootstrap_data(self, client: FPLClient):
        """Ensure bootstrap data is loaded, fetching from API if needed or expired"""
        # Check cache first
        cached_data = cache_manager.get("bootstrap_data")

        if cached_data is not None:
            self.bootstrap_data = cached_data
            logger.debug("Using cached bootstrap data")
            return

        # Cache miss or expired - fetch from API
        try:
            logger.info("Fetching bootstrap data from API...")
            raw_data = await client.get_bootstrap_data()
            self.bootstrap_data = BootstrapData(**raw_data)

            # Cache with configured TTL
            cache_manager.set("bootstrap_data", self.bootstrap_data, settings.bootstrap_cache_ttl)

            self._build_player_indices()
            logger.info(
                f"Loaded {len(self.bootstrap_data.elements)} players from API "
                f"(cached for {settings.bootstrap_cache_ttl}s)"
            )
        except Exception as e:
            logger.error(f"Failed to load bootstrap data: {e}")
            raise

    async def ensure_fixtures_data(self, client: FPLClient):
        """Ensure fixtures data is loaded, fetching from API if needed or expired"""
        cached_data = cache_manager.get("fixtures_data")

        if cached_data is None:
            try:
                logger.info("Fetching fixtures data from API...")
                raw_data = await client.get_fixtures()
                self.fixtures_data = [FixtureData(**fixture) for fixture in raw_data]

                # Cache with configured TTL
                cache_manager.set("fixtures_data", self.fixtures_data, settings.fixtures_cache_ttl)

                logger.info(f"Loaded {len(self.fixtures_data)} fixtures from API")
            except Exception as e:
                logger.error(f"Failed to load fixtures data: {e}")
                raise

    def _build_player_indices(self):
        """Build player name and ID indices from bootstrap data"""
        bootstrap_data = self.bootstrap_data
        if not bootstrap_data:
            return

        # Enrich elements with team names for faster lookups
        team_map = {t.id: t.name for t in bootstrap_data.teams}
        position_map = {t.id: t.singular_name_short for t in bootstrap_data.element_types}

        # Build player name index and ID map
        self.player_name_map.clear()
        self.player_id_map.clear()

        for element in bootstrap_data.elements:
            # Add team_name and position to each element
            element.team_name = team_map.get(element.team, "Unknown")
            element.position = position_map.get(element.element_type, "UNK")

            # Store in ID map
            self.player_id_map[element.id] = element

            # Build name index with multiple keys for flexible matching
            # 1. Web name (most common)
            web_key = self._normalize_name(element.web_name)
            if web_key not in self.player_name_map:
                self.player_name_map[web_key] = []
            self.player_name_map[web_key].append(element.id)

            # 2. Full name (first + second)
            full_key = self._normalize_name(f"{element.first_name} {element.second_name}")
            if full_key not in self.player_name_map:
                self.player_name_map[full_key] = []
            if element.id not in self.player_name_map[full_key]:
                self.player_name_map[full_key].append(element.id)

            # 3. Second name only (surname)
            surname_key = self._normalize_name(element.second_name)
            if surname_key not in self.player_name_map:
                self.player_name_map[surname_key] = []
            if element.id not in self.player_name_map[surname_key]:
                self.player_name_map[surname_key].append(element.id)

            # 4. First name + web name (for cases like "Mohamed Salah")
            if element.first_name and element.web_name != element.second_name:
                first_web_key = self._normalize_name(f"{element.first_name} {element.web_name}")
                if first_web_key not in self.player_name_map:
                    self.player_name_map[first_web_key] = []
                if element.id not in self.player_name_map[first_web_key]:
                    self.player_name_map[first_web_key].append(element.id)

        if bootstrap_data:
            logger.info(
                f"Built player indices: {len(bootstrap_data.elements)} players, "
                f"{len(bootstrap_data.teams)} teams, "
                f"{len(bootstrap_data.events)} gameweeks. "
                f"Name index has {len(self.player_name_map)} keys."
            )

    def get_team_by_id(self, team_id: int) -> dict | None:
        """Get team information by ID"""
        if not self.bootstrap_data:
            return None

        team = next((t for t in self.bootstrap_data.teams if t.id == team_id), None)
        if not team:
            return None

        return {
            "id": team.id,
            "name": team.name,
            "short_name": team.short_name,
            "strength": getattr(team, "strength", None),
            "strength_overall_home": getattr(team, "strength_overall_home", None),
            "strength_overall_away": getattr(team, "strength_overall_away", None),
            "strength_attack_home": getattr(team, "strength_attack_home", None),
            "strength_attack_away": getattr(team, "strength_attack_away", None),
            "strength_defence_home": getattr(team, "strength_defence_home", None),
            "strength_defence_away": getattr(team, "strength_defence_away", None),
        }

    def get_all_teams(self) -> list:
        """Get all teams with their information"""
        if not self.bootstrap_data:
            return []

        return [
            {
                "id": t.id,
                "name": t.name,
                "short_name": t.short_name,
                "strength": getattr(t, "strength", None),
                "strength_overall_home": getattr(t, "strength_overall_home", None),
                "strength_overall_away": getattr(t, "strength_overall_away", None),
            }
            for t in self.bootstrap_data.teams
        ]

    def find_players_by_name(
        self, name_query: str, fuzzy: bool = True
    ) -> list[tuple[ElementData, float]]:
        """
        Find players by name with intelligent matching.
        Returns list of (player, similarity_score) tuples sorted by relevance.

        Args:
            name_query: The name to search for
            fuzzy: Whether to use fuzzy matching for close matches

        Returns:
            List of (ElementData, similarity_score) tuples, sorted by score descending
        """
        if not self.bootstrap_data:
            return []

        normalized_query = self._normalize_name(name_query)
        results: dict[int, float] = {}  # player_id -> best similarity score

        # 1. Exact match
        if normalized_query in self.player_name_map:
            for player_id in self.player_name_map[normalized_query]:
                results[player_id] = PERFECT_MATCH_SCORE

        # 2. Substring match (contains)
        if not results:
            for name_key, player_ids in self.player_name_map.items():
                if normalized_query in name_key or name_key in normalized_query:
                    # Calculate similarity based on length ratio
                    similarity = min(len(normalized_query), len(name_key)) / max(
                        len(normalized_query), len(name_key)
                    )
                    for player_id in player_ids:
                        if player_id not in results or similarity > results[player_id]:
                            results[player_id] = similarity * SUBSTRING_MATCH_PENALTY

        # 3. Fuzzy matching (if enabled and no good matches yet)
        if fuzzy and (not results or max(results.values()) < 0.7):
            for name_key, player_ids in self.player_name_map.items():
                similarity = SequenceMatcher(None, normalized_query, name_key).ratio()
                if similarity >= FUZZY_MATCH_THRESHOLD:
                    for player_id in player_ids:
                        if player_id not in results or similarity > results[player_id]:
                            results[player_id] = similarity * FUZZY_MATCH_PENALTY

        # Convert to list of tuples and sort by score
        player_matches = [
            (self.player_id_map[player_id], score) for player_id, score in results.items()
        ]
        player_matches.sort(key=lambda x: x[1], reverse=True)

        return player_matches

    def get_player_by_id(self, player_id: int) -> ElementData | None:
        """Get a player by their ID"""
        return self.player_id_map.get(player_id)

    def get_current_gameweek(self) -> EventData | None:
        """Get the current gameweek event"""
        if not self.bootstrap_data or not self.bootstrap_data.events:
            return None

        # First check for is_current flag
        for event in self.bootstrap_data.events:
            if event.is_current:
                return event

        # Fallback to is_next if current deadline has passed
        for event in self.bootstrap_data.events:
            if event.is_next:
                return event

        # Last resort: first unfinished gameweek
        for event in self.bootstrap_data.events:
            if not event.finished:
                return event

        return None

    def rehydrate_player_names(self, element_ids: list[int]) -> dict[int, dict]:
        """
        Rehydrate player element IDs to full player information.

        Args:
            element_ids: List of player element IDs

        Returns:
            Dictionary mapping element_id -> player info dict
        """
        result = {}
        for element_id in element_ids:
            player = self.get_player_by_id(element_id)
            if player:
                result[element_id] = {
                    "id": player.id,
                    "web_name": player.web_name,
                    "full_name": f"{player.first_name} {player.second_name}",
                    "team": player.team_name,
                    "position": player.position,
                    "price": player.now_cost / 10,
                    "form": player.form,
                    "points_per_game": player.points_per_game,
                    "total_points": getattr(player, "total_points", 0),
                    "status": player.status,
                    "news": player.news,
                }
        return result

    def get_player_name(self, element_id: int) -> str:
        """
        Get a player's web name by their element ID.

        Args:
            element_id: The player's element ID

        Returns:
            Player's web name or "Unknown Player (ID: {element_id})"
        """
        player = self.get_player_by_id(element_id)
        if player:
            return player.web_name
        return f"Unknown Player (ID: {element_id})"

    async def find_manager_by_name(
        self, client: FPLClient, league_id: int, manager_name: str
    ) -> dict | None:
        """
        Find a manager by name in a league's standings.

        Args:
            client: The authenticated FPL client
            league_id: The league ID to search in
            manager_name: The manager's name to find

        Returns:
            Manager dict with 'entry', 'entry_name', 'player_name' if found, None otherwise
        """
        try:
            standings_data = await client.get_league_standings(league_id)
            results = standings_data.get("standings", {}).get("results", [])

            # Normalize search name
            normalized_search = self._normalize_name(manager_name)

            # Search through standings
            for result in results:
                # Try matching against player_name (manager name)
                if self._normalize_name(result.get("player_name", "")) == normalized_search:
                    return {
                        "entry": result.get("entry"),
                        "entry_name": result.get("entry_name"),
                        "player_name": result.get("player_name"),
                    }

                # Try matching against entry_name (team name)
                if self._normalize_name(result.get("entry_name", "")) == normalized_search:
                    return {
                        "entry": result.get("entry"),
                        "entry_name": result.get("entry_name"),
                        "player_name": result.get("player_name"),
                    }

            # Try substring matches
            for result in results:
                player_norm = self._normalize_name(result.get("player_name", ""))
                entry_norm = self._normalize_name(result.get("entry_name", ""))

                if (
                    normalized_search in player_norm
                    or player_norm in normalized_search
                    or normalized_search in entry_norm
                    or entry_norm in normalized_search
                ):
                    return {
                        "entry": result.get("entry"),
                        "entry_name": result.get("entry_name"),
                        "player_name": result.get("player_name"),
                    }

            return None

        except Exception as e:
            logger.error(f"Error finding manager by name: {e}")
            return None

    def enrich_gameweek_history(self, history: list[dict]) -> list[dict]:
        """
        Enrich gameweek history data with friendly names for teams.
        Adds 'opponent_team_name' and 'opponent_team_short' fields.

        Args:
            history: List of gameweek history dicts from element-summary

        Returns:
            Enriched history with team names added
        """
        if not self.bootstrap_data:
            return history

        enriched = []
        for gw in history:
            enriched_gw = gw.copy()

            # Add opponent team names
            opponent_id = gw.get("opponent_team")
            if opponent_id:
                opponent = self.get_team_by_id(opponent_id)
                if opponent:
                    enriched_gw["opponent_team_name"] = opponent["name"]
                    enriched_gw["opponent_team_short"] = opponent["short_name"]

            enriched.append(enriched_gw)

        return enriched

    def enrich_fixtures(self, fixtures: list) -> list:
        """
        Enrich fixture data with friendly team names.
        Adds 'team_h_name', 'team_h_short', 'team_a_name', 'team_a_short' fields.

        Args:
            fixtures: List of FixtureData objects or fixture dicts

        Returns:
            List of enriched fixture dicts
        """
        if not self.bootstrap_data:
            return fixtures

        enriched = []
        for fixture in fixtures:
            # Convert to dict if it's a FixtureData object
            if hasattr(fixture, "model_dump"):
                fixture_dict = fixture.model_dump()
            elif hasattr(fixture, "__dict__"):
                fixture_dict = fixture.__dict__.copy()
            else:
                fixture_dict = fixture.copy() if isinstance(fixture, dict) else {}

            # Add home team names
            team_h_id = (
                fixture_dict.get("team_h")
                if isinstance(fixture_dict, dict)
                else getattr(fixture, "team_h", None)
            )
            if team_h_id:
                team_h = self.get_team_by_id(team_h_id)
                if team_h:
                    fixture_dict["team_h_name"] = team_h["name"]
                    fixture_dict["team_h_short"] = team_h["short_name"]

            # Add away team names
            team_a_id = (
                fixture_dict.get("team_a")
                if isinstance(fixture_dict, dict)
                else getattr(fixture, "team_a", None)
            )
            if team_a_id:
                team_a = self.get_team_by_id(team_a_id)
                if team_a:
                    fixture_dict["team_a_name"] = team_a["name"]
                    fixture_dict["team_a_short"] = team_a["short_name"]

            enriched.append(fixture_dict)

        return enriched


# Global Instance
store = SessionStore()

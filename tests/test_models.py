"""
Tests for Pydantic models in src/models.py
"""

import pytest

from src.models import (
    BootstrapData,
    ElementData,
    ElementSummary,
    ElementTypeData,
    EventData,
    FixtureData,
    FixtureStat,
    FixtureStatValue,
    Player,
    PlayerFixture,
    PlayerHistory,
    PlayerHistoryPast,
    TeamData,
    TopElementInfo,
    TransferPayload,
)


@pytest.mark.unit
class TestPlayerModel:
    """Test Player model."""

    def test_player_creation(self):
        """Test creating a Player instance."""
        player = Player(
            id=1,
            web_name="Salah",
            first_name="Mohamed",
            second_name="Salah",
            team=2,
            element_type=3,
            now_cost=130,
            form="8.5",
            points_per_game="7.2",
            news="",
        )

        assert player.id == 1
        assert player.web_name == "Salah"
        assert player.now_cost == 130

    def test_player_price_calculation(self):
        """Test that Player.price is calculated from now_cost."""
        player = Player(
            id=1,
            web_name="Haaland",
            first_name="Erling",
            second_name="Haaland",
            team=3,
            element_type=4,
            now_cost=140,
            form="9.0",
            points_per_game="8.5",
            news="",
        )

        # Price should be now_cost / 10
        assert player.price == 14.0

    def test_player_price_decimal(self):
        """Test price calculation with decimal values."""
        player = Player(
            id=2,
            web_name="Saka",
            first_name="Bukayo",
            second_name="Saka",
            team=1,
            element_type=3,
            now_cost=95,
            form="6.5",
            points_per_game="5.8",
            news="",
        )

        assert player.price == 9.5


@pytest.mark.unit
class TestElementData:
    """Test ElementData model."""

    def test_element_data_creation(self):
        """Test creating an ElementData instance."""
        element = ElementData(
            id=1,
            web_name="Salah",
            first_name="Mohamed",
            second_name="Salah",
            team=2,
            element_type=3,
            now_cost=130,
            form="8.5",
            points_per_game="7.2",
            news="",
            status="a",
        )

        assert element.id == 1
        assert element.web_name == "Salah"
        assert element.status == "a"

    def test_element_data_extra_fields_allowed(self):
        """Test that extra fields are allowed in ElementData."""
        element = ElementData(
            id=1,
            web_name="Salah",
            first_name="Mohamed",
            second_name="Salah",
            team=2,
            element_type=3,
            now_cost=130,
            form="8.5",
            points_per_game="7.2",
            news="",
            status="a",
            # Extra fields
            total_points=200,
            bonus=15,
        )

        # Extra fields should be accessible
        assert hasattr(element, "total_points")
        assert hasattr(element, "bonus")


@pytest.mark.unit
class TestTeamData:
    """Test TeamData model."""

    def test_team_data_creation(self):
        """Test creating a TeamData instance."""
        team = TeamData(id=1, name="Arsenal", short_name="ARS")

        assert team.id == 1
        assert team.name == "Arsenal"
        assert team.short_name == "ARS"

    def test_team_data_extra_fields_allowed(self):
        """Test that extra fields are allowed in TeamData."""
        team = TeamData(
            id=1,
            name="Arsenal",
            short_name="ARS",
            # Extra fields
            strength=4,
            position=1,
        )

        assert hasattr(team, "strength")
        assert hasattr(team, "position")


@pytest.mark.unit
class TestElementTypeData:
    """Test ElementTypeData model."""

    def test_element_type_data_creation(self):
        """Test creating an ElementTypeData instance."""
        element_type = ElementTypeData(
            id=1,
            singular_name_short="GKP",
            plural_name_short="GKPs",
        )

        assert element_type.id == 1
        assert element_type.singular_name_short == "GKP"
        assert element_type.plural_name_short == "GKPs"


@pytest.mark.unit
class TestTopElementInfo:
    """Test TopElementInfo model."""

    def test_top_element_info_creation(self):
        """Test creating a TopElementInfo instance."""
        top_element = TopElementInfo(id=1, points=150)

        assert top_element.id == 1
        assert top_element.points == 150


@pytest.mark.unit
class TestEventData:
    """Test EventData model."""

    def test_event_data_creation(self):
        """Test creating an EventData instance."""
        event = EventData(
            id=1,
            name="Gameweek 1",
            deadline_time="2024-08-16T17:30:00Z",
            finished=True,
            data_checked=True,
            deadline_time_epoch=1692203400,
            is_previous=False,
            is_current=True,
            is_next=False,
            can_enter=True,
            released=True,
        )

        assert event.id == 1
        assert event.name == "Gameweek 1"
        assert event.is_current is True

    def test_event_data_optional_fields(self):
        """Test EventData with optional fields."""
        event = EventData(
            id=2,
            name="Gameweek 2",
            deadline_time="2024-08-23T17:30:00Z",
            average_entry_score=50,
            finished=False,
            data_checked=False,
            highest_scoring_entry=12345,
            deadline_time_epoch=1692808200,
            highest_score=120,
            is_previous=False,
            is_current=False,
            is_next=True,
            can_enter=True,
            released=True,
        )

        assert event.average_entry_score == 50
        assert event.highest_scoring_entry == 12345
        assert event.highest_score == 120


@pytest.mark.unit
class TestBootstrapData:
    """Test BootstrapData model."""

    def test_bootstrap_data_creation(
        self, mock_players, mock_teams, mock_element_types, mock_events
    ):
        """Test creating a BootstrapData instance."""
        bootstrap = BootstrapData(
            elements=mock_players,
            teams=mock_teams,
            element_types=mock_element_types,
            events=mock_events,
        )

        assert len(bootstrap.elements) == 3
        assert len(bootstrap.teams) == 3
        assert len(bootstrap.element_types) == 4
        assert len(bootstrap.events) == 2


@pytest.mark.unit
class TestTransferPayload:
    """Test TransferPayload model."""

    def test_transfer_payload_creation(self):
        """Test creating a TransferPayload instance."""
        payload = TransferPayload(
            entry=12345,
            event=10,
            transfers=[{"element_in": 100, "element_out": 200}],
        )

        assert payload.entry == 12345
        assert payload.event == 10
        assert len(payload.transfers) == 1

    def test_transfer_payload_with_chip(self):
        """Test TransferPayload with chip."""
        payload = TransferPayload(
            chip="wildcard",
            entry=12345,
            event=10,
            transfers=[],
            wildcard=True,
        )

        assert payload.chip == "wildcard"
        assert payload.wildcard is True


@pytest.mark.unit
class TestFixtureModels:
    """Test fixture-related models."""

    def test_fixture_stat_value(self):
        """Test FixtureStatValue model."""
        stat_value = FixtureStatValue(value=2, element=123)

        assert stat_value.value == 2
        assert stat_value.element == 123

    def test_fixture_stat(self):
        """Test FixtureStat model."""
        stat = FixtureStat(
            identifier="goals_scored",
            a=[FixtureStatValue(value=1, element=100)],
            h=[FixtureStatValue(value=2, element=200)],
        )

        assert stat.identifier == "goals_scored"
        assert len(stat.a) == 1
        assert len(stat.h) == 1

    def test_fixture_data(self):
        """Test FixtureData model."""
        fixture = FixtureData(
            code=12345,
            finished=False,
            finished_provisional=False,
            id=1,
            minutes=0,
            started=False,
            provisional_start_time=False,
            team_a=1,
            team_h=2,
            stats=[],
            team_h_difficulty=3,
            team_a_difficulty=2,
            pulse_id=1,
        )

        assert fixture.id == 1
        assert fixture.team_a == 1
        assert fixture.team_h == 2
        assert fixture.finished is False


@pytest.mark.unit
class TestPlayerModels:
    """Test player-related models."""

    def test_player_fixture(self):
        """Test PlayerFixture model."""
        fixture = PlayerFixture(
            id=1,
            code=12345,
            team_h=1,
            team_a=2,
            event=10,
            finished=False,
            minutes=0,
            provisional_start_time=False,
            event_name="Gameweek 10",
            is_home=True,
            difficulty=3,
        )

        assert fixture.id == 1
        assert fixture.is_home is True
        assert fixture.difficulty == 3

    def test_player_history(self):
        """Test PlayerHistory model."""
        history = PlayerHistory(
            element=123,
            fixture=1,
            opponent_team=2,
            total_points=10,
            was_home=True,
            kickoff_time="2024-08-16T17:30:00Z",
            round=1,
            modified=False,
            minutes=90,
            goals_scored=1,
            assists=0,
            clean_sheets=0,
            goals_conceded=1,
            own_goals=0,
            penalties_saved=0,
            penalties_missed=0,
            yellow_cards=0,
            red_cards=0,
            saves=0,
            bonus=3,
            bps=30,
            influence="50.0",
            creativity="30.0",
            threat="40.0",
            ict_index="12.0",
            starts=1,
            value=100,
            transfers_balance=0,
            selected=1000000,
            transfers_in=50000,
            transfers_out=30000,
            expected_goals="0.5",
            expected_assists="0.2",
            expected_goal_involvements="0.7",
            expected_goals_conceded="1.0",
        )

        assert history.element == 123
        assert history.total_points == 10
        assert history.goals_scored == 1

    def test_player_history_past(self):
        """Test PlayerHistoryPast model."""
        past = PlayerHistoryPast(
            season_name="2023/24",
            element_code=12345,
            start_cost=100,
            end_cost=110,
            total_points=200,
            minutes=3000,
            goals_scored=20,
            assists=10,
            clean_sheets=15,
            goals_conceded=30,
            own_goals=0,
            penalties_saved=0,
            penalties_missed=0,
            yellow_cards=5,
            red_cards=0,
            saves=0,
            bonus=25,
            bps=800,
            influence="1000.0",
            creativity="800.0",
            threat="900.0",
            ict_index="270.0",
            starts=38,
            expected_goals="18.5",
            expected_assists="9.2",
            expected_goal_involvements="27.7",
            expected_goals_conceded="28.5",
        )

        assert past.season_name == "2023/24"
        assert past.total_points == 200
        assert past.goals_scored == 20

    def test_element_summary(self):
        """Test ElementSummary model."""
        summary = ElementSummary(
            fixtures=[],
            history=[],
            history_past=[],
        )

        assert summary.fixtures == []
        assert summary.history == []
        assert summary.history_past == []

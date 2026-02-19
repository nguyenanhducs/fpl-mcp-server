from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Player(BaseModel):
    id: int
    web_name: str
    first_name: str
    second_name: str
    team: int
    element_type: int
    now_cost: int
    form: str
    points_per_game: str
    news: str

    # Computed fields
    team_name: str | None = None
    position: str | None = None
    price: float = Field(default=0.0)

    def __init__(self, **data):
        super().__init__(**data)
        self.price = self.now_cost / 10


class ElementData(BaseModel):
    """Player element from bootstrap data"""

    id: int
    web_name: str
    first_name: str
    second_name: str
    team: int
    element_type: int
    now_cost: int
    form: str
    points_per_game: str
    news: str
    status: str

    # Enriched fields (added during bootstrap loading)
    team_name: str | None = None
    position: str | None = None

    # Allow extra fields from the API that we don't need to validate
    model_config = ConfigDict(extra="allow")


class TeamData(BaseModel):
    """Team data from bootstrap"""

    id: int
    name: str
    short_name: str

    model_config = ConfigDict(extra="allow")


class ElementTypeData(BaseModel):
    """Position type data from bootstrap"""

    id: int
    singular_name_short: str
    plural_name_short: str

    model_config = ConfigDict(extra="allow")


class TopElementInfo(BaseModel):
    """Top scoring player info for an event"""

    id: int
    points: int


class EventData(BaseModel):
    """Gameweek event data from bootstrap"""

    id: int
    name: str
    deadline_time: str
    average_entry_score: int | None = None
    finished: bool
    data_checked: bool
    highest_scoring_entry: int | None = None
    deadline_time_epoch: int
    highest_score: int | None = None
    is_previous: bool
    is_current: bool
    is_next: bool
    can_enter: bool
    released: bool
    top_element: int | None = None
    top_element_info: TopElementInfo | None = None
    most_selected: int | None = None
    most_transferred_in: int | None = None
    most_captained: int | None = None
    most_vice_captained: int | None = None

    model_config = ConfigDict(extra="allow")


class BootstrapData(BaseModel):
    """Bootstrap static data structure"""

    elements: list[ElementData]
    teams: list[TeamData]
    element_types: list[ElementTypeData]
    events: list[EventData]

    model_config = ConfigDict(extra="allow")


class TransferPayload(BaseModel):
    chip: str | None = None
    entry: int
    event: int
    transfers: list[dict[str, int]]
    wildcard: bool = False
    freehit: bool = False


class FixtureStatValue(BaseModel):
    """Individual stat value in a fixture"""

    value: int
    element: int


class FixtureStat(BaseModel):
    """Stat category in a fixture"""

    identifier: str
    a: list[FixtureStatValue]
    h: list[FixtureStatValue]


class FixtureData(BaseModel):
    """Fixture data from the fixtures endpoint"""

    code: int
    event: int | None = None
    finished: bool
    finished_provisional: bool
    id: int
    kickoff_time: str | None = None
    minutes: int
    provisional_start_time: bool
    started: bool | None = None
    team_a: int
    team_a_score: int | None = None
    team_h: int
    team_h_score: int | None = None
    stats: list[FixtureStat]
    team_h_difficulty: int
    team_a_difficulty: int
    pulse_id: int

    model_config = ConfigDict(extra="allow")


class PlayerFixture(BaseModel):
    """Fixture information for a player"""

    id: int
    code: int
    team_h: int
    team_h_score: int | None = None
    team_a: int
    team_a_score: int | None = None
    event: int | None = None
    finished: bool
    minutes: int
    provisional_start_time: bool
    kickoff_time: str | None = None
    event_name: str
    is_home: bool
    difficulty: int


class PlayerHistory(BaseModel):
    """Historical performance data for a player in a gameweek"""

    element: int
    fixture: int
    opponent_team: int
    total_points: int
    was_home: bool
    kickoff_time: str
    team_h_score: int | None = None
    team_a_score: int | None = None
    round: int
    modified: bool
    minutes: int
    goals_scored: int
    assists: int
    clean_sheets: int
    goals_conceded: int
    own_goals: int
    penalties_saved: int
    penalties_missed: int
    yellow_cards: int
    red_cards: int
    saves: int
    bonus: int
    bps: int
    influence: str
    creativity: str
    threat: str
    ict_index: str
    starts: int
    expected_goals: str
    expected_assists: str
    expected_goal_involvements: str
    expected_goals_conceded: str
    value: int
    transfers_balance: int
    selected: int
    transfers_in: int
    transfers_out: int

    model_config = ConfigDict(extra="allow")


class PlayerHistoryPast(BaseModel):
    """Historical season data for a player"""

    season_name: str
    element_code: int
    start_cost: int
    end_cost: int
    total_points: int
    minutes: int
    goals_scored: int
    assists: int
    clean_sheets: int
    goals_conceded: int
    own_goals: int
    penalties_saved: int
    penalties_missed: int
    yellow_cards: int
    red_cards: int
    saves: int
    bonus: int
    bps: int
    influence: str
    creativity: str
    threat: str
    ict_index: str
    starts: int
    expected_goals: str
    expected_assists: str
    expected_goal_involvements: str
    expected_goals_conceded: str

    model_config = ConfigDict(extra="allow")


class ElementSummary(BaseModel):
    """Complete player summary from element-summary endpoint"""

    fixtures: list[PlayerFixture]
    history: list[PlayerHistory]
    history_past: list[PlayerHistoryPast]


class LeaguePhase(BaseModel):
    """Phase information within a league"""

    phase: int
    rank: int
    last_rank: int
    rank_sort: int
    total: int
    league_id: int
    rank_count: int | None = None
    entry_percentile_rank: int | None = None


class ClassicLeague(BaseModel):
    """Classic league information for a manager"""

    id: int
    name: str
    short_name: str | None = None
    created: str
    closed: bool
    rank: int | None = None
    max_entries: int | None = None
    league_type: str
    scoring: str
    admin_entry: int | None = None
    start_event: int
    entry_can_leave: bool
    entry_can_admin: bool
    entry_can_invite: bool
    has_cup: bool
    cup_league: int | None = None
    cup_qualified: bool | None = None
    rank_count: int | None = None
    entry_percentile_rank: int | None = None
    active_phases: list[LeaguePhase]
    entry_rank: int
    entry_last_rank: int


class CupStatus(BaseModel):
    """Cup qualification status"""

    qualification_event: int | None = None
    qualification_numbers: int | None = None
    qualification_rank: int | None = None
    qualification_state: str | None = None


class Cup(BaseModel):
    """Cup information for a manager"""

    matches: list[Any]
    status: CupStatus
    cup_league: int | None = None


class Leagues(BaseModel):
    """All leagues information for a manager"""

    classic: list[ClassicLeague]
    h2h: list[Any]
    cup: Cup
    cup_matches: list[Any]


class ManagerEntry(BaseModel):
    """FPL manager/team entry information"""

    id: int
    joined_time: str
    started_event: int
    favourite_team: int | None = None
    player_first_name: str
    player_last_name: str
    player_region_id: int
    player_region_name: str
    player_region_iso_code_short: str
    player_region_iso_code_long: str
    years_active: int
    summary_overall_points: int
    summary_overall_rank: int
    summary_event_points: int
    summary_event_rank: int
    current_event: int
    leagues: Leagues
    name: str
    name_change_blocked: bool
    entered_events: list[int]
    kit: str | None = None
    last_deadline_bank: int
    last_deadline_value: int
    last_deadline_total_transfers: int
    club_badge_src: str | None = None

    model_config = ConfigDict(extra="allow")


class LeagueStandingEntry(BaseModel):
    """Individual entry in league standings"""

    id: int
    event_total: int
    player_name: str
    rank: int
    last_rank: int
    rank_sort: int
    total: int
    entry: int
    entry_name: str

    model_config = ConfigDict(extra="allow")


class LeagueStandings(BaseModel):
    """League standings response"""

    has_next: bool
    page: int
    results: list[LeagueStandingEntry]

    model_config = ConfigDict(extra="allow")


class LeagueStandingsResponse(BaseModel):
    """Complete league standings response with league info"""

    league: ClassicLeague
    standings: LeagueStandings

    model_config = ConfigDict(extra="allow")


class AutomaticSub(BaseModel):
    """Automatic substitution made during a gameweek"""

    entry: int
    element_in: int
    element_out: int
    event: int


class PickElement(BaseModel):
    """Individual player pick in a gameweek team"""

    element: int
    position: int
    multiplier: int
    is_captain: bool
    is_vice_captain: bool

    model_config = ConfigDict(extra="allow")


class UserPlayer(BaseModel):
    """Current user's player information from /me endpoint"""

    first_name: str
    last_name: str
    email: str
    entry: int
    region: int
    id: int

    model_config = ConfigDict(extra="allow")


class MeResponse(BaseModel):
    """Response from /me endpoint"""

    player: UserPlayer
    watched: list[Any]


class EntryHistory(BaseModel):
    """Manager's performance for a specific gameweek"""

    event: int
    points: int
    total_points: int
    rank: int | None = None
    rank_sort: int | None = None
    overall_rank: int
    bank: int
    value: int
    event_transfers: int
    event_transfers_cost: int
    points_on_bench: int

    model_config = ConfigDict(extra="allow")


class GameweekPicks(BaseModel):
    """Manager's team picks for a specific gameweek"""

    active_chip: str | None = None
    automatic_subs: list[AutomaticSub]
    entry_history: EntryHistory
    picks: list[PickElement]

    model_config = ConfigDict(extra="allow")


class ChipData(BaseModel):
    """Chip information from my-team endpoint"""

    id: int
    status_for_entry: str
    played_by_entry: list[int]
    name: str
    number: int
    start_event: int
    stop_event: int
    chip_type: str
    is_pending: bool

    model_config = ConfigDict(extra="allow")


class TransfersData(BaseModel):
    """Transfer information from my-team endpoint"""

    cost: int
    status: str
    limit: int
    made: int
    bank: int
    value: int

    model_config = ConfigDict(extra="allow")


class MyTeamResponse(BaseModel):
    """Complete response from my-team endpoint"""

    picks: list[PickElement]
    chips: list[ChipData]
    transfers: TransfersData

    model_config = ConfigDict(extra="allow")

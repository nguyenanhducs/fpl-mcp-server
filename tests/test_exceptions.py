"""
Tests for custom exceptions in src/exceptions.py
"""

import pytest

from src.exceptions import (
    AuthenticationError,
    CacheError,
    DataFetchError,
    FPLMCPError,
    GameweekNotFoundError,
    LeagueNotFoundError,
    ManagerNotFoundError,
    PlayerNotFoundError,
    RateLimitError,
    ScraperError,
    TeamNotFoundError,
    TransferError,
    ValidationError,
)


@pytest.mark.unit
class TestBaseException:
    """Test base FPLMCPError exception."""

    def test_base_exception_inheritance(self):
        """Test that FPLMCPError inherits from Exception."""
        assert issubclass(FPLMCPError, Exception)

    def test_base_exception_raise(self):
        """Test raising base exception."""
        with pytest.raises(FPLMCPError) as exc_info:
            raise FPLMCPError("Test error")

        assert "Test error" in str(exc_info.value)


@pytest.mark.unit
class TestAuthenticationError:
    """Test AuthenticationError exception."""

    def test_authentication_error_inheritance(self):
        """Test that AuthenticationError inherits from FPLMCPError."""
        assert issubclass(AuthenticationError, FPLMCPError)

    def test_authentication_error_raise(self):
        """Test raising authentication error."""
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError("Auth failed")

        assert "Auth failed" in str(exc_info.value)


@pytest.mark.unit
class TestDataFetchError:
    """Test DataFetchError exception."""

    def test_data_fetch_error_inheritance(self):
        """Test that DataFetchError inherits from FPLMCPError."""
        assert issubclass(DataFetchError, FPLMCPError)

    def test_data_fetch_error_raise(self):
        """Test raising data fetch error."""
        with pytest.raises(DataFetchError):
            raise DataFetchError("Failed to fetch data")


@pytest.mark.unit
class TestCacheError:
    """Test CacheError exception."""

    def test_cache_error_inheritance(self):
        """Test that CacheError inherits from FPLMCPError."""
        assert issubclass(CacheError, FPLMCPError)

    def test_cache_error_raise(self):
        """Test raising cache error."""
        with pytest.raises(CacheError):
            raise CacheError("Cache operation failed")


@pytest.mark.unit
class TestPlayerNotFoundError:
    """Test PlayerNotFoundError exception."""

    def test_player_not_found_error_inheritance(self):
        """Test that PlayerNotFoundError inherits from FPLMCPError."""
        assert issubclass(PlayerNotFoundError, FPLMCPError)

    def test_player_not_found_without_suggestions(self):
        """Test PlayerNotFoundError without suggestions."""
        error = PlayerNotFoundError("Ronaldo")

        assert error.player_name == "Ronaldo"
        assert error.suggestions == []
        assert "No player found matching 'Ronaldo'" in str(error)

    def test_player_not_found_with_suggestions(self):
        """Test PlayerNotFoundError with suggestions."""
        suggestions = ["Salah", "Saka", "Son"]
        error = PlayerNotFoundError("Sala", suggestions)

        assert error.player_name == "Sala"
        assert error.suggestions == suggestions
        assert "No player found matching 'Sala'" in str(error)
        assert "Did you mean: Salah, Saka, Son?" in str(error)

    def test_player_not_found_truncates_suggestions(self):
        """Test that PlayerNotFoundError shows only first 3 suggestions."""
        suggestions = ["Player1", "Player2", "Player3", "Player4", "Player5"]
        error = PlayerNotFoundError("Test", suggestions)

        error_msg = str(error)
        assert "Player1" in error_msg
        assert "Player2" in error_msg
        assert "Player3" in error_msg
        assert "Player4" not in error_msg

    def test_player_not_found_raise(self):
        """Test raising PlayerNotFoundError."""
        with pytest.raises(PlayerNotFoundError) as exc_info:
            raise PlayerNotFoundError("Kane", ["Haaland"])

        assert exc_info.value.player_name == "Kane"


@pytest.mark.unit
class TestTeamNotFoundError:
    """Test TeamNotFoundError exception."""

    def test_team_not_found_error_inheritance(self):
        """Test that TeamNotFoundError inherits from FPLMCPError."""
        assert issubclass(TeamNotFoundError, FPLMCPError)

    def test_team_not_found_without_suggestions(self):
        """Test TeamNotFoundError without suggestions."""
        error = TeamNotFoundError("Real Madrid")

        assert error.team_name == "Real Madrid"
        assert error.suggestions == []
        assert "No team found matching 'Real Madrid'" in str(error)

    def test_team_not_found_with_suggestions(self):
        """Test TeamNotFoundError with suggestions."""
        suggestions = ["Arsenal", "Aston Villa"]
        error = TeamNotFoundError("Arsen", suggestions)

        assert error.team_name == "Arsen"
        assert error.suggestions == suggestions
        assert "Did you mean: Arsenal, Aston Villa?" in str(error)

    def test_team_not_found_raise(self):
        """Test raising TeamNotFoundError."""
        with pytest.raises(TeamNotFoundError) as exc_info:
            raise TeamNotFoundError("Liverpool FC", ["Liverpool"])

        assert exc_info.value.team_name == "Liverpool FC"


@pytest.mark.unit
class TestLeagueNotFoundError:
    """Test LeagueNotFoundError exception."""

    def test_league_not_found_error_inheritance(self):
        """Test that LeagueNotFoundError inherits from FPLMCPError."""
        assert issubclass(LeagueNotFoundError, FPLMCPError)

    def test_league_not_found(self):
        """Test LeagueNotFoundError message formatting."""
        error = LeagueNotFoundError("My League")

        assert error.league_name == "My League"
        assert "League 'My League' not found in your leagues" in str(error)

    def test_league_not_found_raise(self):
        """Test raising LeagueNotFoundError."""
        with pytest.raises(LeagueNotFoundError) as exc_info:
            raise LeagueNotFoundError("Test League")

        assert exc_info.value.league_name == "Test League"


@pytest.mark.unit
class TestManagerNotFoundError:
    """Test ManagerNotFoundError exception."""

    def test_manager_not_found_error_inheritance(self):
        """Test that ManagerNotFoundError inherits from FPLMCPError."""
        assert issubclass(ManagerNotFoundError, FPLMCPError)

    def test_manager_not_found(self):
        """Test ManagerNotFoundError message formatting."""
        error = ManagerNotFoundError("John Doe", "Premier League")

        assert error.manager_name == "John Doe"
        assert error.league_name == "Premier League"
        assert "Manager 'John Doe' not found in league 'Premier League'" in str(error)

    def test_manager_not_found_raise(self):
        """Test raising ManagerNotFoundError."""
        with pytest.raises(ManagerNotFoundError) as exc_info:
            raise ManagerNotFoundError("Jane Smith", "Champions League")

        assert exc_info.value.manager_name == "Jane Smith"
        assert exc_info.value.league_name == "Champions League"


@pytest.mark.unit
class TestGameweekNotFoundError:
    """Test GameweekNotFoundError exception."""

    def test_gameweek_not_found_error_inheritance(self):
        """Test that GameweekNotFoundError inherits from FPLMCPError."""
        assert issubclass(GameweekNotFoundError, FPLMCPError)

    def test_gameweek_not_found(self):
        """Test GameweekNotFoundError message formatting."""
        error = GameweekNotFoundError(99)

        assert error.gameweek == 99
        assert "Gameweek 99 not found or not valid" in str(error)

    def test_gameweek_not_found_raise(self):
        """Test raising GameweekNotFoundError."""
        with pytest.raises(GameweekNotFoundError) as exc_info:
            raise GameweekNotFoundError(42)

        assert exc_info.value.gameweek == 42


@pytest.mark.unit
class TestTransferError:
    """Test TransferError exception."""

    def test_transfer_error_inheritance(self):
        """Test that TransferError inherits from FPLMCPError."""
        assert issubclass(TransferError, FPLMCPError)

    def test_transfer_error_without_details(self):
        """Test TransferError without details."""
        error = TransferError("Transfer failed")

        assert error.details == {}
        assert "Transfer failed" in str(error)

    def test_transfer_error_with_details(self):
        """Test TransferError with details dictionary."""
        details = {"reason": "insufficient funds", "cost": 10.5}
        error = TransferError("Cannot complete transfer", details)

        assert error.details == details
        assert error.details["reason"] == "insufficient funds"
        assert "Cannot complete transfer" in str(error)

    def test_transfer_error_raise(self):
        """Test raising TransferError."""
        with pytest.raises(TransferError) as exc_info:
            raise TransferError("Invalid transfer", {"player_in": 123, "player_out": 456})

        assert exc_info.value.details["player_in"] == 123


@pytest.mark.unit
class TestRateLimitError:
    """Test RateLimitError exception."""

    def test_rate_limit_error_inheritance(self):
        """Test that RateLimitError inherits from FPLMCPError."""
        assert issubclass(RateLimitError, FPLMCPError)

    def test_rate_limit_error_without_retry_after(self):
        """Test RateLimitError without retry_after."""
        error = RateLimitError()

        assert error.retry_after is None
        assert "Rate limit exceeded" in str(error)
        assert "Please try again" not in str(error)

    def test_rate_limit_error_with_retry_after(self):
        """Test RateLimitError with retry_after parameter."""
        error = RateLimitError(retry_after=60)

        assert error.retry_after == 60
        assert "Rate limit exceeded" in str(error)
        assert "Please try again in 60 seconds" in str(error)

    def test_rate_limit_error_raise(self):
        """Test raising RateLimitError."""
        with pytest.raises(RateLimitError) as exc_info:
            raise RateLimitError(retry_after=30)

        assert exc_info.value.retry_after == 30


@pytest.mark.unit
class TestValidationError:
    """Test ValidationError exception."""

    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from FPLMCPError."""
        assert issubclass(ValidationError, FPLMCPError)

    def test_validation_error_raise(self):
        """Test raising ValidationError."""
        with pytest.raises(ValidationError):
            raise ValidationError("Invalid input")


@pytest.mark.unit
class TestScraperError:
    """Test ScraperError exception."""

    def test_scraper_error_inheritance(self):
        """Test that ScraperError inherits from FPLMCPError."""
        assert issubclass(ScraperError, FPLMCPError)

    def test_scraper_error_raise(self):
        """Test raising ScraperError."""
        with pytest.raises(ScraperError):
            raise ScraperError("Scraping failed")

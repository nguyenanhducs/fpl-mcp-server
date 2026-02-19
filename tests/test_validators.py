"""Tests for input validators."""

import pytest

from src.exceptions import ValidationError
from src.validators import (
    sanitize_string,
    validate_boolean,
    validate_gameweek,
    validate_league_id,
    validate_manager_id,
    validate_page_number,
    validate_page_size,
    validate_player_id,
    validate_player_name,
    validate_positive_int,
    validate_team_id,
    validate_team_name,
)


@pytest.mark.unit
class TestSanitizeString:
    def test_sanitize_valid_string(self):
        """Test sanitizing a valid string."""
        result = sanitize_string("Hello World", "test")
        assert result == "Hello World"

    def test_sanitize_with_whitespace(self):
        """Test sanitizing string with extra whitespace."""
        result = sanitize_string("  Hello World  ", "test")
        assert result == "Hello World"

    def test_sanitize_removes_null_bytes(self):
        """Test that null bytes are removed."""
        result = sanitize_string("Hello\0World", "test")
        assert result == "HelloWorld"

    def test_sanitize_max_length(self):
        """Test maximum length validation."""
        long_string = "a" * 1001
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            sanitize_string(long_string, "test")

    def test_sanitize_empty_after_strip(self):
        """Test that empty string after stripping raises error."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            sanitize_string("   ", "test")

    def test_sanitize_non_string(self):
        """Test that non-string input raises error."""
        with pytest.raises(ValidationError, match="must be a string"):
            sanitize_string(123, "test")


@pytest.mark.unit
class TestValidatePlayerName:
    def test_valid_player_name(self):
        """Test validating a normal player name."""
        assert validate_player_name("Mohamed Salah") == "Mohamed Salah"

    def test_player_name_with_apostrophe(self):
        """Test player name with apostrophe."""
        assert validate_player_name("N'Golo Kante") == "N'Golo Kante"

    def test_player_name_with_hyphen(self):
        """Test player name with hyphen."""
        assert validate_player_name("Trent Alexander-Arnold") == "Trent Alexander-Arnold"

    def test_player_name_with_dot(self):
        """Test player name with dot."""
        assert validate_player_name("K. De Bruyne") == "K. De Bruyne"

    def test_invalid_characters(self):
        """Test that invalid characters are rejected."""
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_player_name("Player<script>alert(1)</script>")


@pytest.mark.unit
class TestValidateTeamName:
    def test_valid_team_name(self):
        """Test validating team name."""
        assert validate_team_name("Manchester United") == "Manchester United"

    def test_team_name_with_numbers(self):
        """Test team name with numbers."""
        assert validate_team_name("Brighton & Hove Albion") == "Brighton & Hove Albion"

    def test_invalid_characters(self):
        """Test that invalid characters are rejected."""
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_team_name("Team<>")


@pytest.mark.unit
class TestValidatePositiveInt:
    def test_valid_integer(self):
        """Test validating a valid integer."""
        assert validate_positive_int(5, "test", 1, 10) == 5

    def test_string_to_integer(self):
        """Test converting string to integer."""
        assert validate_positive_int("5", "test", 1, 10) == 5

    def test_below_minimum(self):
        """Test that value below minimum is rejected."""
        with pytest.raises(ValidationError, match="must be at least"):
            validate_positive_int(0, "test", 1, 10)

    def test_above_maximum(self):
        """Test that value above maximum is rejected."""
        with pytest.raises(ValidationError, match="must be at most"):
            validate_positive_int(11, "test", 1, 10)

    def test_invalid_type(self):
        """Test that invalid type raises error."""
        with pytest.raises(ValidationError, match="must be an integer"):
            validate_positive_int("invalid", "test", 1, 10)


@pytest.mark.unit
class TestValidateIDs:
    def test_validate_player_id(self):
        """Test player ID validation."""
        assert validate_player_id(1) == 1
        assert validate_player_id("123") == 123

    def test_validate_team_id(self):
        """Test team ID validation."""
        assert validate_team_id(1) == 1
        assert validate_team_id(20) == 20
        with pytest.raises(ValidationError):
            validate_team_id(21)

    def test_validate_gameweek(self):
        """Test gameweek validation."""
        assert validate_gameweek(1) == 1
        assert validate_gameweek(38) == 38
        with pytest.raises(ValidationError):
            validate_gameweek(0)
        with pytest.raises(ValidationError):
            validate_gameweek(39)

    def test_validate_manager_id(self):
        """Test manager ID validation."""
        assert validate_manager_id(12345) == 12345

    def test_validate_league_id(self):
        """Test league ID validation."""
        assert validate_league_id(54321) == 54321


@pytest.mark.unit
class TestValidatePagination:
    def test_validate_page_number(self):
        """Test page number validation."""
        assert validate_page_number(1) == 1
        assert validate_page_number("5") == 5

    def test_validate_page_size(self):
        """Test page size validation."""
        assert validate_page_size(10) == 10
        assert validate_page_size(50) == 50
        with pytest.raises(ValidationError):
            validate_page_size(0)
        with pytest.raises(ValidationError):
            validate_page_size(101)


@pytest.mark.unit
class TestValidateBoolean:
    def test_validate_true_bool(self):
        """Test validating true boolean."""
        assert validate_boolean(True) is True

    def test_validate_false_bool(self):
        """Test validating false boolean."""
        assert validate_boolean(False) is False

    def test_validate_string_true(self):
        """Test converting string to true."""
        assert validate_boolean("true") is True
        assert validate_boolean("True") is True
        assert validate_boolean("1") is True
        assert validate_boolean("yes") is True

    def test_validate_string_false(self):
        """Test converting string to false."""
        assert validate_boolean("false") is False
        assert validate_boolean("False") is False
        assert validate_boolean("0") is False
        assert validate_boolean("no") is False

    def test_validate_invalid_value(self):
        """Test that invalid value raises error."""
        with pytest.raises(ValidationError, match="must be a boolean"):
            validate_boolean("invalid")
        with pytest.raises(ValidationError):
            validate_boolean(123)

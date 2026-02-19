"""
Input validation and sanitization for FPL MCP Server.

Provides validators to prevent injection attacks and ensure data integrity.
"""

import logging
import re
from typing import Any

from .exceptions import ValidationError

logger = logging.getLogger("fpl_validators")

# Constants for validation
MAX_STRING_LENGTH = 1000
MAX_NAME_LENGTH = 200
MIN_ID = 1
MAX_ID = 999999
MAX_GAMEWEEK = 38
MIN_GAMEWEEK = 1
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1


def sanitize_string(
    value: str, field_name: str = "input", max_length: int = MAX_STRING_LENGTH
) -> str:
    """
    Sanitize string input to prevent injection attacks.

    Args:
        value: String to sanitize
        field_name: Name of the field for error messages
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        ValidationError: If input is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string, got {type(value).__name__}")

    # Remove null bytes and control characters
    sanitized = value.replace("\0", "").strip()

    # Check length
    if len(sanitized) > max_length:
        raise ValidationError(
            f"{field_name} exceeds maximum length of {max_length} characters (got {len(sanitized)})"
        )

    if not sanitized:
        raise ValidationError(f"{field_name} cannot be empty after sanitization")

    # Log suspicious patterns
    if re.search(r"[<>]|script|javascript|onclick|onerror", sanitized, re.IGNORECASE):
        logger.warning(f"Suspicious pattern detected in {field_name}: {sanitized[:50]}")

    return sanitized


def validate_player_name(name: str) -> str:
    """
    Validate and sanitize player name.

    Args:
        name: Player name to validate

    Returns:
        Sanitized player name

    Raises:
        ValidationError: If name is invalid
    """
    sanitized = sanitize_string(name, "player_name", MAX_NAME_LENGTH)

    # Player names should only contain letters, spaces, hyphens, apostrophes, and dots
    if not re.match(r"^[A-Za-z\s\-'.]+$", sanitized):
        raise ValidationError(
            "Player name contains invalid characters. "
            "Only letters, spaces, hyphens, apostrophes, and dots are allowed"
        )

    return sanitized


def validate_team_name(name: str) -> str:
    """
    Validate and sanitize team name.

    Args:
        name: Team name to validate

    Returns:
        Sanitized team name

    Raises:
        ValidationError: If name is invalid
    """
    sanitized = sanitize_string(name, "team_name", MAX_NAME_LENGTH)

    # Team names can contain letters, spaces, numbers, and common punctuation
    if not re.match(r"^[A-Za-z0-9\s\-'&.]+$", sanitized):
        raise ValidationError(
            "Team name contains invalid characters. "
            "Only letters, numbers, spaces, hyphens, apostrophes, ampersands, and dots are allowed"
        )

    return sanitized


def validate_positive_int(
    value: Any,
    field_name: str = "value",
    min_value: int = MIN_ID,
    max_value: int = MAX_ID,
) -> int:
    """
    Validate that value is a positive integer within range.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        Validated integer

    Raises:
        ValidationError: If value is invalid
    """
    if not isinstance(value, int):
        try:
            value = int(value)
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"{field_name} must be an integer, got {type(value).__name__}"
            ) from e

    if value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}, got {value}")

    if value > max_value:
        raise ValidationError(f"{field_name} must be at most {max_value}, got {value}")

    return value


def validate_player_id(player_id: Any) -> int:
    """
    Validate player ID.

    Args:
        player_id: Player ID to validate

    Returns:
        Validated player ID

    Raises:
        ValidationError: If ID is invalid
    """
    return validate_positive_int(player_id, "player_id", MIN_ID, MAX_ID)


def validate_team_id(team_id: Any) -> int:
    """
    Validate team ID.

    Args:
        team_id: Team ID to validate

    Returns:
        Validated team ID

    Raises:
        ValidationError: If ID is invalid
    """
    # FPL has 20 teams
    return validate_positive_int(team_id, "team_id", MIN_ID, 20)


def validate_gameweek(gameweek: Any) -> int:
    """
    Validate gameweek number.

    Args:
        gameweek: Gameweek number to validate

    Returns:
        Validated gameweek

    Raises:
        ValidationError: If gameweek is invalid
    """
    return validate_positive_int(gameweek, "gameweek", MIN_GAMEWEEK, MAX_GAMEWEEK)


def validate_manager_id(manager_id: Any) -> int:
    """
    Validate manager ID.

    Args:
        manager_id: Manager ID to validate

    Returns:
        Validated manager ID

    Raises:
        ValidationError: If ID is invalid
    """
    return validate_positive_int(manager_id, "manager_id", MIN_ID, MAX_ID * 10)


def validate_league_id(league_id: Any) -> int:
    """
    Validate league ID.

    Args:
        league_id: League ID to validate

    Returns:
        Validated league ID

    Raises:
        ValidationError: If ID is invalid
    """
    return validate_positive_int(league_id, "league_id", MIN_ID, MAX_ID * 10)


def validate_page_number(page: Any) -> int:
    """
    Validate page number for pagination.

    Args:
        page: Page number to validate

    Returns:
        Validated page number

    Raises:
        ValidationError: If page is invalid
    """
    return validate_positive_int(page, "page", 1, 10000)


def validate_page_size(page_size: Any) -> int:
    """
    Validate page size for pagination.

    Args:
        page_size: Page size to validate

    Returns:
        Validated page size

    Raises:
        ValidationError: If page size is invalid
    """
    return validate_positive_int(page_size, "page_size", MIN_PAGE_SIZE, MAX_PAGE_SIZE)


def validate_boolean(value: Any, field_name: str = "value") -> bool:
    """
    Validate and convert to boolean.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages

    Returns:
        Boolean value

    Raises:
        ValidationError: If value cannot be converted to boolean
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        lower = value.lower()
        if lower in ("true", "1", "yes"):
            return True
        if lower in ("false", "0", "no"):
            return False

    raise ValidationError(f"{field_name} must be a boolean value, got {value}")

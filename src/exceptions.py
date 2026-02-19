"""
Custom exceptions for the FPL MCP Server.
"""


class FPLMCPError(Exception):
    """Base exception for FPL MCP Server."""

    pass


class AuthenticationError(FPLMCPError):
    """Raised when authentication fails or is required."""

    pass


class DataFetchError(FPLMCPError):
    """Raised when data cannot be fetched from the FPL API."""

    pass


class CacheError(FPLMCPError):
    """Raised when cache operations fail."""

    pass


class PlayerNotFoundError(FPLMCPError):
    """Raised when a player cannot be found."""

    def __init__(self, player_name: str, suggestions: list[str] = None):
        self.player_name = player_name
        self.suggestions = suggestions or []

        message = f"No player found matching '{player_name}'."
        if suggestions:
            message += f" Did you mean: {', '.join(suggestions[:3])}?"

        super().__init__(message)


class TeamNotFoundError(FPLMCPError):
    """Raised when a team cannot be found."""

    def __init__(self, team_name: str, suggestions: list[str] = None):
        self.team_name = team_name
        self.suggestions = suggestions or []

        message = f"No team found matching '{team_name}'."
        if suggestions:
            message += f" Did you mean: {', '.join(suggestions[:3])}?"

        super().__init__(message)


class LeagueNotFoundError(FPLMCPError):
    """Raised when a league cannot be found."""

    def __init__(self, league_name: str):
        self.league_name = league_name
        message = f"League '{league_name}' not found in your leagues."
        super().__init__(message)


class ManagerNotFoundError(FPLMCPError):
    """Raised when a manager cannot be found in a league."""

    def __init__(self, manager_name: str, league_name: str):
        self.manager_name = manager_name
        self.league_name = league_name
        message = f"Manager '{manager_name}' not found in league '{league_name}'."
        super().__init__(message)


class GameweekNotFoundError(FPLMCPError):
    """Raised when a gameweek cannot be found."""

    def __init__(self, gameweek: int):
        self.gameweek = gameweek
        message = f"Gameweek {gameweek} not found or not valid."
        super().__init__(message)


class TransferError(FPLMCPError):
    """Raised when a transfer operation fails."""

    def __init__(self, message: str, details: dict = None):
        self.details = details or {}
        super().__init__(message)


class RateLimitError(FPLMCPError):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int = None):
        self.retry_after = retry_after
        message = "Rate limit exceeded."
        if retry_after:
            message += f" Please try again in {retry_after} seconds."
        super().__init__(message)


class ValidationError(FPLMCPError):
    """Raised when input validation fails."""

    pass


class ScraperError(FPLMCPError):
    """Raised when web scraping operations fail."""

    pass

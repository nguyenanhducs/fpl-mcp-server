"""
Tests for utility functions in src/utils.py
"""

import httpx
import pytest

from src.formatting import (
    format_difficulty_indicator,
    format_markdown_table_row,
)
from src.utils import (
    ResponseFormat,
    check_and_truncate,
    create_pagination_metadata,
    format_json_response,
    format_player_price,
    format_player_status,
    format_status_indicator,
    handle_api_error,
    pluralize,
)


@pytest.mark.unit
class TestResponseFormat:
    """Test ResponseFormat enum."""

    def test_response_format_values(self):
        """Test that ResponseFormat has correct values."""
        assert ResponseFormat.MARKDOWN == "markdown"
        assert ResponseFormat.JSON == "json"


@pytest.mark.unit
class TestHandleApiError:
    """Test handle_api_error function."""

    def test_404_error(self):
        """Test handling of 404 Not Found errors."""
        response = httpx.Response(status_code=404, request=httpx.Request("GET", "http://test.com"))
        error = httpx.HTTPStatusError("Not Found", request=response.request, response=response)

        result = handle_api_error(error)
        assert "Error: Resource not found" in result
        assert "fpl_search_players" in result
        assert "fpl_list_all_teams" in result

    def test_403_error(self):
        """Test handling of 403 Forbidden errors."""
        response = httpx.Response(status_code=403, request=httpx.Request("GET", "http://test.com"))
        error = httpx.HTTPStatusError("Forbidden", request=response.request, response=response)

        result = handle_api_error(error)
        assert "Error: Access denied" in result
        assert "private" in result

    def test_429_error(self):
        """Test handling of 429 Rate Limit errors."""
        response = httpx.Response(status_code=429, request=httpx.Request("GET", "http://test.com"))
        error = httpx.HTTPStatusError(
            "Too Many Requests", request=response.request, response=response
        )

        result = handle_api_error(error)
        assert "Error: Rate limit exceeded" in result
        assert "60 seconds" in result

    def test_500_error(self):
        """Test handling of 500 Server errors."""
        response = httpx.Response(status_code=500, request=httpx.Request("GET", "http://test.com"))
        error = httpx.HTTPStatusError("Server Error", request=response.request, response=response)

        result = handle_api_error(error)
        assert "Error: FPL API server error" in result
        assert "fantasy.premierleague.com" in result

    def test_generic_http_error(self):
        """Test handling of other HTTP errors."""
        response = httpx.Response(status_code=400, request=httpx.Request("GET", "http://test.com"))
        error = httpx.HTTPStatusError("Bad Request", request=response.request, response=response)

        result = handle_api_error(error)
        assert "Error: API request failed with status 400" in result

    def test_timeout_error(self):
        """Test handling of timeout errors."""
        error = httpx.TimeoutException("Request timed out")

        result = handle_api_error(error)
        assert "Error: Request timed out" in result
        assert "API may be under heavy load" in result

    def test_connect_error(self):
        """Test handling of connection errors."""
        error = httpx.ConnectError("Connection failed")

        result = handle_api_error(error)
        assert "Error: Cannot connect to FPL API" in result
        assert "internet connection" in result

    def test_generic_error(self):
        """Test handling of generic exceptions."""
        error = ValueError("Some error")

        result = handle_api_error(error)
        assert "Error: ValueError: Some error" in result


@pytest.mark.unit
class TestCheckAndTruncate:
    """Test check_and_truncate function."""

    def test_content_within_limit(self):
        """Test that content within limit is not truncated."""
        content = "Short content"
        result, was_truncated = check_and_truncate(content, 100)

        assert result == content
        assert was_truncated is False

    def test_content_exactly_at_limit(self):
        """Test that content exactly at limit is not truncated."""
        content = "x" * 100
        result, was_truncated = check_and_truncate(content, 100)

        assert result == content
        assert was_truncated is False

    def test_content_exceeds_limit(self):
        """Test that content exceeding limit is truncated."""
        content = "x" * 1000
        result, was_truncated = check_and_truncate(content, 100)

        assert len(result) < len(content)
        assert was_truncated is True
        assert "Response truncated" in result
        assert "exceeded 100 character limit" in result

    def test_truncation_with_custom_message(self):
        """Test truncation with custom additional message."""
        content = "x" * 1000
        custom_msg = "Try using filters"
        result, was_truncated = check_and_truncate(content, 100, custom_msg)

        assert was_truncated is True
        assert custom_msg in result


@pytest.mark.unit
class TestCreatePaginationMetadata:
    """Test create_pagination_metadata function."""

    def test_first_page_with_more(self):
        """Test pagination metadata for first page with more results."""
        metadata = create_pagination_metadata(total=100, count=20, limit=20, offset=0)

        assert metadata["total"] == 100
        assert metadata["count"] == 20
        assert metadata["limit"] == 20
        assert metadata["offset"] == 0
        assert metadata["has_more"] is True
        assert metadata["next_offset"] == 20

    def test_middle_page(self):
        """Test pagination metadata for middle page."""
        metadata = create_pagination_metadata(total=100, count=20, limit=20, offset=40)

        assert metadata["total"] == 100
        assert metadata["count"] == 20
        assert metadata["offset"] == 40
        assert metadata["has_more"] is True
        assert metadata["next_offset"] == 60

    def test_last_page(self):
        """Test pagination metadata for last page."""
        metadata = create_pagination_metadata(total=100, count=20, limit=20, offset=80)

        assert metadata["total"] == 100
        assert metadata["count"] == 20
        assert metadata["offset"] == 80
        assert metadata["has_more"] is False
        assert metadata["next_offset"] is None

    def test_single_page(self):
        """Test pagination metadata when all results fit on one page."""
        metadata = create_pagination_metadata(total=10, count=10, limit=20, offset=0)

        assert metadata["total"] == 10
        assert metadata["count"] == 10
        assert metadata["has_more"] is False
        assert metadata["next_offset"] is None


@pytest.mark.unit
class TestFormatPlayerPrice:
    """Test format_player_price function."""

    def test_whole_number_price(self):
        """Test formatting whole number prices."""
        assert format_player_price(100) == "£10.0m"
        assert format_player_price(50) == "£5.0m"

    def test_decimal_price(self):
        """Test formatting prices with decimals."""
        assert format_player_price(125) == "£12.5m"
        assert format_player_price(95) == "£9.5m"

    def test_expensive_player(self):
        """Test formatting expensive player prices."""
        assert format_player_price(140) == "£14.0m"

    def test_cheap_player(self):
        """Test formatting cheap player prices."""
        assert format_player_price(40) == "£4.0m"


@pytest.mark.unit
class TestFormatStatusIndicator:
    """Test format_status_indicator function."""

    def test_available_status(self):
        """Test available status returns empty string."""
        assert format_status_indicator("a") == ""

    def test_injured_status(self):
        """Test injured status."""
        assert format_status_indicator("i") == " [Injured]"

    def test_doubtful_status(self):
        """Test doubtful status."""
        assert format_status_indicator("d") == " [Doubtful]"

    def test_unavailable_status(self):
        """Test unavailable status."""
        assert format_status_indicator("u") == " [Unavailable]"

    def test_suspended_status(self):
        """Test suspended status."""
        assert format_status_indicator("s") == " [Suspended]"

    def test_not_in_squad_status(self):
        """Test not in squad status."""
        assert format_status_indicator("n") == " [Not in squad]"

    def test_status_with_news(self):
        """Test status with news adds warning emoji."""
        result = format_status_indicator("a", "Some news")
        assert "⚠️" in result

    def test_injured_with_news(self):
        """Test injured status with news."""
        result = format_status_indicator("i", "Ankle injury")
        assert "[Injured]" in result
        assert "⚠️" in result


@pytest.mark.unit
class TestFormatPlayerStatus:
    """Test format_player_status function."""

    def test_available_status(self):
        """Test available status returns 'Available'."""
        assert format_player_status("a") == "Available"

    def test_injured_status(self):
        """Test injured status returns 'Injured'."""
        assert format_player_status("i") == "Injured"

    def test_doubtful_status(self):
        """Test doubtful status returns 'Doubtful'."""
        assert format_player_status("d") == "Doubtful"

    def test_unavailable_status(self):
        """Test unavailable status returns 'Unavailable'."""
        assert format_player_status("u") == "Unavailable"

    def test_suspended_status(self):
        """Test suspended status returns 'Suspended'."""
        assert format_player_status("s") == "Suspended"

    def test_not_in_squad_status(self):
        """Test not in squad status returns 'Not in squad'."""
        assert format_player_status("n") == "Not in squad"

    def test_unknown_status(self):
        """Test unknown status code returns the code itself."""
        assert format_player_status("x") == "x"
        assert format_player_status("unknown") == "unknown"


@pytest.mark.unit
class TestFormatMarkdownTableRow:
    """Test format_markdown_table_row function."""

    def test_simple_row(self):
        """Test formatting simple row without widths."""
        items = ["Player", "Team", "Points"]
        result = format_markdown_table_row(items)

        assert result == "| Player | Team | Points |"

    def test_row_with_widths(self):
        """Test formatting row with specified widths."""
        items = ["Salah", "LIV", "200"]
        widths = [15, 8, 5]
        result = format_markdown_table_row(items, widths)

        assert "Salah" in result
        assert "LIV" in result
        assert "200" in result
        assert result.startswith("| ")
        assert result.endswith(" |")

    def test_row_with_numbers(self):
        """Test formatting row with numeric values."""
        items = [1, 2, 3]
        result = format_markdown_table_row(items)

        assert result == "| 1 | 2 | 3 |"


@pytest.mark.unit
class TestFormatJsonResponse:
    """Test format_json_response function."""

    def test_simple_dict(self):
        """Test formatting simple dictionary."""
        data = {"name": "Salah", "team": "Liverpool"}
        result = format_json_response(data)

        assert "name" in result
        assert "Salah" in result
        assert "Liverpool" in result

    def test_nested_structure(self):
        """Test formatting nested structure."""
        data = {"player": {"name": "Salah", "stats": {"goals": 20}}}
        result = format_json_response(data)

        assert "player" in result
        assert "stats" in result
        assert "20" in result

    def test_list(self):
        """Test formatting list."""
        data = [1, 2, 3]
        result = format_json_response(data)

        assert "[" in result
        assert "]" in result

    def test_custom_indent(self):
        """Test formatting with custom indentation."""
        data = {"key": "value"}
        result = format_json_response(data, indent=4)

        assert "    " in result  # 4 spaces


@pytest.mark.unit
class TestFormatDifficultyIndicator:
    """Test format_difficulty_indicator function."""

    def test_difficulty_1(self):
        """Test difficulty rating 1 (easiest)."""
        result = format_difficulty_indicator(1)
        assert result == "●○○○○"

    def test_difficulty_2(self):
        """Test difficulty rating 2."""
        result = format_difficulty_indicator(2)
        assert result == "●●○○○"

    def test_difficulty_3(self):
        """Test difficulty rating 3 (medium)."""
        result = format_difficulty_indicator(3)
        assert result == "●●●○○"

    def test_difficulty_4(self):
        """Test difficulty rating 4."""
        result = format_difficulty_indicator(4)
        assert result == "●●●●○"

    def test_difficulty_5(self):
        """Test difficulty rating 5 (hardest)."""
        result = format_difficulty_indicator(5)
        assert result == "●●●●●"


@pytest.mark.unit
class TestPluralize:
    """Test pluralize function."""

    def test_singular_one(self):
        """Test singular form for count of 1."""
        assert pluralize(1, "player") == "1 player"

    def test_plural_zero(self):
        """Test plural form for count of 0."""
        assert pluralize(0, "player") == "0 players"

    def test_plural_multiple(self):
        """Test plural form for multiple items."""
        assert pluralize(5, "player") == "5 players"

    def test_custom_plural(self):
        """Test with custom plural form."""
        assert pluralize(2, "match", "matches") == "2 matches"

    def test_custom_plural_singular(self):
        """Test custom plural with singular count."""
        assert pluralize(1, "match", "matches") == "1 match"

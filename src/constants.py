"""
Constants and enums for the FPL MCP Server.
"""

from enum import Enum

# Fuzzy Matching Constants
FUZZY_MATCH_THRESHOLD = 0.6  # Minimum similarity for fuzzy matches
SUBSTRING_MATCH_PENALTY = 0.9  # Score multiplier for substring matches
FUZZY_MATCH_PENALTY = 0.8  # Score multiplier for fuzzy matches
PERFECT_MATCH_SCORE = 1.0  # Score for exact matches


# Player Positions
class PlayerPosition(Enum):
    """FPL player positions"""

    GOALKEEPER = "GKP"
    DEFENDER = "DEF"
    MIDFIELDER = "MID"
    FORWARD = "FWD"


# Top Players Count
TOP_GOALKEEPERS_COUNT = 5
TOP_DEFENDERS_COUNT = 20
TOP_MIDFIELDERS_COUNT = 20
TOP_FORWARDS_COUNT = 20

# Pagination
MAX_PAGINATION_LIMIT = 100  # MCP recommended maximum limit

# MCP Response Configuration
CHARACTER_LIMIT = 25000  # Maximum response size in characters (MCP best practice)

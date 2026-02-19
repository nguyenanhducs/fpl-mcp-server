"""Configuration management for FPL MCP Server."""


class Settings:
    """Application settings (hardcoded)."""

    # Cache Configuration (in seconds)
    bootstrap_cache_ttl: int = 14400  # 4 hours
    fixtures_cache_ttl: int = 14400  # 4 hours


# Global settings instance
settings = Settings()

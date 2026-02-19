# ============================================
# Builder Stage: Install dependencies with uv
# ============================================
FROM ghcr.io/astral-sh/uv:python3.13-alpine AS builder
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev
COPY src ./src

# ============================================
# Runtime Stage: Minimal Python runtime
# ============================================
FROM python:3.13-alpine AS runtime
LABEL maintainer="nguyenanhducs"
LABEL description="Fantasy Premier League MCP Server"
LABEL org.opencontainers.image.source="https://github.com/nguyenanhducs/fpl-mcp-server"
LABEL org.opencontainers.image.title="FPL MCP Server"
LABEL org.opencontainers.image.description="A comprehensive Model Context Protocol (MCP) server for Fantasy Premier League analysis and strategy. Provides AI assistants with powerful tools, resources, and prompts for data-driven FPL insights."
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app
RUN addgroup -g 1000 fplmcp && \
    adduser -D -u 1000 -G fplmcp fplmcp
COPY --from=builder --chown=fplmcp:fplmcp /app/.venv /app/.venv
COPY --from=builder --chown=fplmcp:fplmcp /app/src /app/src
USER fplmcp
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "src.main"]

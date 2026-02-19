# Installation

Multiple installation methods are available for FPL MCP Server. Choose the one that best fits your needs.

## uvx (Recommended)

[uvx](https://docs.astral.sh/uv/guides/tools/) provides the simplest installation experience. It automatically downloads and caches the package on first use.

```bash
# Run directly (downloads on first use, cached for subsequent run
uvx fpl-mcp-server
```

Or install it globally:

```bash
uv tool install fpl-mcp-server
```

Use the following configuration:

```json
{
  "mcpServers": {
    "fpl": {
      "command": "uvx",
      "args": ["fpl-mcp-server"]
    }
  }
}
```

---

## Docker

Use the pre-built Docker image from GitHub Container Registry for isolated, reproducible environments.

```bash
# Pull the latest image
docker pull ghcr.io/nguyenanhducs/fpl-mcp-server:latest

# Run the server
docker run --rm -i ghcr.io/nguyenanhducs/fpl-mcp-server:latest
```

Use the following configuration:

```json
{
  "mcpServers": {
    "fpl": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "ghcr.io/nguyenanhducs/fpl-mcp-server:latest"]
    }
  }
}
```

---

## From Source

For development or contributing:

```bash
git clone https://github.com/nguyenanhducs/fpl-mcp-server.git
cd fpl-mcp-server
uv sync
uv run python -m src.main
```

Use the following configuration:

```json
{
  "mcpServers": {
    "fpl": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/fpl-mcp-server",
        "run",
        "python",
        "-m",
        "src.main"
      ]
    }
  }
}
```

Replace `/absolute/path/to/fpl-mcp-server` with your actual installation path.

---

## Verification

To verify your installation, ask your AI assistant:

```
List available FPL tools
```

You should see all FPL tools, including player search, fixture analysis, and transfer tracking capabilities.

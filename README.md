# Fantasy Premier League MCP Server

A comprehensive **Model Context Protocol (MCP)** server for Fantasy Premier League analysis and strategy. This server provides AI assistants with powerful tools, resources, and prompts to help you dominate your FPL mini-leagues with data-driven insights.

[![PyPI](https://img.shields.io/pypi/v/fpl-mcp-server.svg)](https://pypi.org/project/fpl-mcp-server/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)
[![Document](https://img.shields.io/badge/docs-mintlify-blue)](https://nad-aae8058d.mintlify.app/)

## Features

This MCP server provides comprehensive FPL analysis capabilities through:

- **19 Interactive Tools** - Search players, analyze fixtures, compare managers, track transfers, and more
- **4 Data Resources** - access to players, teams, gameweeks, and current gameweek bootstrap data
- **10 Strategy Prompts** - Structured templates for gameweek analysis, squad analysis, transfer planning, chip strategy, lineup selection, and captain selection
- **Smart Caching** - 4-hour cache for bootstrap data to minimize API calls while keeping data fresh
- **Fuzzy Matching** - Find players even with spelling variations or nicknames
- **Live Transfer Trends** - Track the most transferred in/out players for current gameweek
- **Manager Insights** - Analyze squads, transfers, and chip usage
- **Fixture Analysis** - Assess team fixtures and plan transfers around favorable runs

## Quick Start

### Option 1: uvx (Recommended)

The fastest way to get started - no installation required:

```json
{
  "mcpServers": {
    "fpl": {
      "command": "uvx",
      "args": ["fpl-mcp-server"],
      "type": "stdio"
    }
  }
}
```

### Option 2: Docker

Use the official Docker image from GitHub Container Registry:

```json
{
  "mcpServers": {
    "fpl": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "ghcr.io/nguyenanhducs/fpl-mcp-server:latest"
      ],
      "type": "stdio"
    }
  }
}
```

For detailed installation instructions and more options, see **[Installation Guide](./docs/installation.md)**.

## Usage & Documentation

Once configured, you can interact with the FPL MCP server through Claude Desktop using natural language.

For detailed guidance, see:

- **[Tool Selection Guide](./docs/tool-selection-guide.md)** - Choose the right tool for your analysis task

## Data Sources

This server uses the official **Fantasy Premier League API**, see [here](./docs/fpl-api.md) for more details.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

<!-- mcp-name: io.github.nguyenanhducs/fpl-mcp-server -->

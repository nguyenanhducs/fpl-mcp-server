"""FPL MCP Server - Main Entry Point"""

import sys
import traceback

sys.stderr.write("Starting FPL MCP Server...\n")
sys.stderr.flush()

try:
    from .tools import mcp

    sys.stderr.write("Imports successful. Initializing MCP server...\n")
    sys.stderr.flush()
except Exception as e:
    sys.stderr.write(f"CRITICAL IMPORT ERROR: {e}\n")
    traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()
    sys.exit(1)


def main():
    """Run the MCP server on stdio transport."""
    try:
        sys.stderr.write("Starting MCP Server (Stdio)...\n")
        sys.stderr.flush()

        mcp.run(transport="stdio")

        sys.stderr.write("MCP Server stopped.\n")
        sys.stderr.flush()

    except Exception as e:
        sys.stderr.write(f"RUNTIME ERROR: {e}\n")
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()

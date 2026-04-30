"""
Data resources — expose static content or dynamic data via MCP resources.
"""


def register(mcp):

    @mcp.resource("whisper://info")
    def server_info() -> str:
        """Returns basic info about this MCP server."""
        return (
            "Whisper MCP Server\n"
            "A multi-device AI assistant.\n"
            "Built with FastMCP."
        )

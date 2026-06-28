from fastmcp.server.auth import StaticTokenVerifier

from src.core.config import settings


def build_mcp_auth() -> StaticTokenVerifier | None:
    # Returns None when MCP_API_KEY is empty → auth disabled (local dev only).
    if not settings.mcp_api_key:
        return None
    return StaticTokenVerifier(
        tokens={settings.mcp_api_key: {'sub': 'mcp-client', 'client_id': 'dis-mcp'}},
    )


__all__ = ['build_mcp_auth']

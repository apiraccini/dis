from fastmcp import FastMCP

from src.core.security import build_mcp_auth

mcp = FastMCP('DIS Knowledge Base', auth=build_mcp_auth())

# path="/" → endpoint is exactly /mcp when mounted at /mcp (default /mcp yields /mcp/mcp).
# stateless_http + json_response go on http_app(), NOT the FastMCP constructor
# (PrefectHQ/fastmcp#3618).
mcp_app = mcp.http_app(
    path='/',
    stateless_http=True,
    json_response=True,
)


@mcp.tool
def ping() -> str:
    # Smoke test — remove once real tools are registered.
    return 'pong'


__all__ = ['mcp', 'mcp_app']

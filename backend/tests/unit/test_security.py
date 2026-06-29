from __future__ import annotations

from unittest.mock import patch

from src.core.security import build_mcp_auth


def test_build_mcp_auth_returns_verifier_when_key_set() -> None:
    with patch('src.core.security.settings') as mock_settings:
        mock_settings.mcp_api_key = 'my-secret-key'

        verifier = build_mcp_auth()

    assert verifier is not None
    assert isinstance(verifier.tokens, dict)
    assert 'my-secret-key' in verifier.tokens
    token_data = verifier.tokens['my-secret-key']
    assert token_data['sub'] == 'mcp-client'
    assert token_data['client_id'] == 'dis-mcp'


def test_build_mcp_auth_returns_none_when_key_empty() -> None:
    with patch('src.core.security.settings') as mock_settings:
        mock_settings.mcp_api_key = ''

        verifier = build_mcp_auth()

    assert verifier is None


def test_build_mcp_auth_returns_none_when_key_none() -> None:
    with patch('src.core.security.settings') as mock_settings:
        mock_settings.mcp_api_key = None

        verifier = build_mcp_auth()

    assert verifier is None

"""
Tests for lti1p3platform.registration to increase coverage.

Covers getters/setters not exercised by other test files, plus
encode_and_sign, decode_and_verify, and platform_encode_and_sign.
"""
import time

import pytest

from lti1p3platform.registration import Registration

from .platform_config import (
    RSA_PUBLIC_KEY_PEM,
    RSA_PRIVATE_KEY_PEM,
    TOOL_KEY_SET,
)


def _make_registration():
    return (
        Registration()
        .set_iss("https://platform.example.com")
        .set_client_id("client-123")
        .set_deployment_id("deploy-1")
        .set_oidc_login_url("https://tool.example.com/oidc_login")
        .set_access_token_url("https://platform.example.com/token")
        .set_launch_url("https://tool.example.com/launch")
        .set_platform_public_key(RSA_PUBLIC_KEY_PEM)
        .set_platform_private_key(RSA_PRIVATE_KEY_PEM)
        .set_tool_key_set(TOOL_KEY_SET)
    )


def test_get_iss():
    reg = _make_registration()
    assert reg.get_iss() == "https://platform.example.com"


def test_get_client_id():
    reg = _make_registration()
    assert reg.get_client_id() == "client-123"


def test_get_deployment_id():
    reg = _make_registration()
    assert reg.get_deployment_id() == "deploy-1"


def test_get_oidc_login_url():
    reg = _make_registration()
    assert reg.get_oidc_login_url() == "https://tool.example.com/oidc_login"


def test_get_access_token_url():
    reg = _make_registration()
    assert reg.get_access_token_url() == "https://platform.example.com/token"


def test_get_launch_url():
    reg = _make_registration()
    assert reg.get_launch_url() == "https://tool.example.com/launch"


def test_get_platform_public_key():
    reg = _make_registration()
    assert "PUBLIC KEY" in reg.get_platform_public_key()


def test_get_platform_private_key():
    reg = _make_registration()
    assert "PRIVATE KEY" in reg.get_platform_private_key()


def test_set_and_get_deeplink_launch_url():
    reg = _make_registration()
    reg.set_deeplink_launch_url("https://tool.example.com/deeplink")
    assert reg.get_deeplink_launch_url() == "https://tool.example.com/deeplink"


def test_get_deeplink_launch_url_default_none():
    reg = Registration()
    assert reg.get_deeplink_launch_url() is None


def test_get_jwk_returns_dict_with_kid():
    jwk = Registration.get_jwk(RSA_PUBLIC_KEY_PEM)
    assert "kid" in jwk
    assert jwk.get("alg") == "RS256"
    assert jwk.get("use") == "sig"
    assert jwk.get("kty") == "RSA"


def test_get_kid_returns_string():
    reg = _make_registration()
    kid = reg.get_kid()
    assert kid is not None
    assert isinstance(kid, str)


def test_get_tool_key_set():
    reg = _make_registration()
    assert reg.get_tool_key_set() == TOOL_KEY_SET


def test_set_and_get_tool_key_set_url():
    reg = _make_registration()
    reg.set_tool_key_set_url("https://tool.example.com/jwks")
    assert reg.get_tool_key_set_url() == "https://tool.example.com/jwks"


def test_get_tool_key_set_url_default_none():
    reg = Registration()
    assert reg.get_tool_key_set_url() is None


def test_set_and_get_tool_redirect_uris():
    reg = _make_registration()
    uris = ["https://tool.example.com/launch", "https://tool.example.com/deeplink"]
    reg.set_tool_redirect_uris(uris)
    assert reg.get_tool_redirect_uris() == uris


def test_get_tool_redirect_uris_default_none():
    reg = Registration()
    assert reg.get_tool_redirect_uris() is None


def test_encode_and_sign_without_expiration():
    """encode_and_sign without expiration should not add iat/exp."""
    payload = {"sub": "user-1", "iss": "https://platform.example.com"}
    token = Registration.encode_and_sign(payload, RSA_PRIVATE_KEY_PEM)
    decoded = Registration.decode_and_verify(
        token, RSA_PUBLIC_KEY_PEM, audience=None
    )
    assert decoded["sub"] == "user-1"
    assert "exp" not in decoded


def test_encode_and_sign_with_expiration():
    payload = {"sub": "user-1", "iss": "https://platform.example.com"}
    token = Registration.encode_and_sign(payload, RSA_PRIVATE_KEY_PEM, expiration=3600)
    decoded = Registration.decode_and_verify(
        token, RSA_PUBLIC_KEY_PEM, audience=None
    )
    assert decoded["sub"] == "user-1"
    assert "exp" in decoded
    assert decoded["exp"] > int(time.time())


def test_decode_and_verify_without_audience():
    payload = {"sub": "user-1", "iss": "https://platform.example.com"}
    token = Registration.encode_and_sign(payload, RSA_PRIVATE_KEY_PEM, expiration=60)
    decoded = Registration.decode_and_verify(token, RSA_PUBLIC_KEY_PEM)
    assert decoded["sub"] == "user-1"


def test_platform_encode_and_sign():
    reg = _make_registration()
    token = reg.platform_encode_and_sign({"custom": "value"}, expiration=60)
    decoded = Registration.decode_and_verify(token, RSA_PUBLIC_KEY_PEM)
    assert decoded["custom"] == "value"


def test_get_jwks_returns_list_with_key():
    reg = _make_registration()
    jwks = reg.get_jwks()
    assert isinstance(jwks, list)
    assert len(jwks) == 1
    assert jwks[0].get("kty") == "RSA"

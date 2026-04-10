"""
Tests for lti1p3platform.ltiplatform to increase coverage.

Covers:
- set_accepted_deeplinking_types
- fetch_public_key (security validations)
- get_tool_key_set (URL path)
- validate_jwt_format (invalid input)
- get_tool_public_key (error paths)
- _is_token_replay / _is_nonce_replay
- _validate_tool_access_token_assertion (all error paths)
- get_access_token (error paths)
- validate_deeplinking_resp (all paths)
- validate_token
"""
# pylint: disable=protected-access
import time
import typing as t
import uuid
from unittest.mock import patch, MagicMock

import pytest
import requests

from lti1p3platform.jwt_helper import jwt_encode
from lti1p3platform.ltiplatform import LTI1P3PlatformConfAbstract
from lti1p3platform.registration import Registration as _Registration
from lti1p3platform.exceptions import (
    InvalidClientAssertion,
    InvalidJwtToken,
    InvalidKeySetUrl,
    LtiException,
    PlatformNotReadyException,
    MissingRequiredClaim,
    UnsupportedGrantType,
    LtiDeepLinkingResponseException,
)

from .platform_config import (
    PlatformConf,
    TOOL_PRIVATE_KEY_PEM,
    TOOL_KEY_SET,
    PLATFORM_CONFIG,
    RSA_PRIVATE_KEY_PEM,
    RSA_PUBLIC_KEY_PEM,
)

# ---------------------------------------------------------------------------
# Minimal platform variant helpers for edge-case coverage
# ---------------------------------------------------------------------------


class _NullRegistrationPlatform(LTI1P3PlatformConfAbstract):
    """Platform whose _registration is initially None."""

    def __init__(self) -> None:
        self._cache: t.Dict[str, int] = {}
        super().__init__()

    def cache_get(self, key: str) -> t.Optional[int]:
        return self._cache.get(key)

    def cache_set(self, key: str, exp: int) -> None:
        self._cache[key] = exp

    def init_platform_config(self, **kwargs: t.Any) -> None:
        pass  # _registration stays None

    def get_registration_by_params(self, **kwargs: t.Any) -> _Registration:
        return (
            _Registration()
            .set_iss(PLATFORM_CONFIG["iss"])
            .set_client_id(PLATFORM_CONFIG["client_id"])
            .set_access_token_url(PLATFORM_CONFIG["access_token_url"])
            .set_platform_public_key(RSA_PUBLIC_KEY_PEM)
            .set_platform_private_key(RSA_PRIVATE_KEY_PEM)
            .set_tool_key_set(TOOL_KEY_SET)
        )


class _NoClientIdPlatform(PlatformConf):
    """Platform with no client_id (exercises line 537)."""

    def init_platform_config(self, **kwargs: t.Any) -> None:
        super().init_platform_config(**kwargs)
        self._registration.set_client_id(None)  # type: ignore[arg-type]


class _NoAudiencePlatform(PlatformConf):
    """Platform with no access_token_url (exercises line 658)."""

    def init_platform_config(self, **kwargs: t.Any) -> None:
        super().init_platform_config(**kwargs)
        self._registration.set_access_token_url(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tool_jwt(claims, private_key=None, headers=None):
    """Return a JWT signed with the tool's private key."""
    if private_key is None:
        private_key = TOOL_PRIVATE_KEY_PEM
    if headers is None:
        jwk = _Registration.get_jwk(TOOL_PRIVATE_KEY_PEM)
        headers = {"kid": jwk.get("kid")}
    return jwt_encode(claims, private_key, algorithm="RS256", headers=headers)


def _make_valid_assertion(jti=None, extra=None):
    """Return a signed JWT suitable for a client_credentials assertion."""
    claims = {
        "iss": PLATFORM_CONFIG["client_id"],
        "sub": PLATFORM_CONFIG["client_id"],
        "aud": [PLATFORM_CONFIG["access_token_url"]],
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 60,
        "jti": jti or ("token-" + str(uuid.uuid4())),
    }
    if extra:
        claims.update(extra)
    return _make_tool_jwt(claims)


def _make_deeplink_jwt(extra_claims=None, nonce=None):
    """Return a valid deep-link response JWT signed by the tool."""
    claims = {
        "iss": "https://tool.example.com",
        "sub": PLATFORM_CONFIG["client_id"],
        "aud": PLATFORM_CONFIG["iss"],
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 60,
        "nonce": nonce if nonce is not None else str(uuid.uuid4()),
        "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiDeepLinkingResponse",
        "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": [],
    }
    if extra_claims:
        claims.update(extra_claims)
    return _make_tool_jwt(claims)


# ---------------------------------------------------------------------------
# set_accepted_deeplinking_types
# ---------------------------------------------------------------------------


def test_set_accepted_types_filters_valid():
    platform = PlatformConf()
    platform.set_accepted_deeplinking_types(["ltiResourceLink", "link"])
    assert "ltiResourceLink" in platform._accepted_deeplinking_types
    assert "link" in platform._accepted_deeplinking_types


def test_set_accepted_types_excludes_invalid():
    platform = PlatformConf()
    platform.set_accepted_deeplinking_types(["ltiResourceLink", "bogusType"])
    assert "ltiResourceLink" in platform._accepted_deeplinking_types
    assert "bogusType" not in platform._accepted_deeplinking_types


def test_set_accepted_types_empty_list():
    platform = PlatformConf()
    platform.set_accepted_deeplinking_types([])
    assert len(platform._accepted_deeplinking_types) == 0


# ---------------------------------------------------------------------------
# fetch_public_key – security validation
# ---------------------------------------------------------------------------


def test_fetch_public_key_http_raises():
    platform = PlatformConf()
    with pytest.raises(InvalidKeySetUrl):
        platform.fetch_public_key("http://example.com/jwks")


def test_fetch_public_key_localhost_raises():
    platform = PlatformConf()
    with pytest.raises(InvalidKeySetUrl):
        platform.fetch_public_key("https://localhost/jwks")


def test_fetch_public_key_loopback_ip_raises():
    platform = PlatformConf()
    with pytest.raises(InvalidKeySetUrl):
        platform.fetch_public_key("https://127.0.0.1/jwks")


def test_fetch_public_key_private_10_raises():
    platform = PlatformConf()
    with pytest.raises(InvalidKeySetUrl):
        platform.fetch_public_key("https://10.0.0.1/jwks")


def test_fetch_public_key_private_192_raises():
    platform = PlatformConf()
    with pytest.raises(InvalidKeySetUrl):
        platform.fetch_public_key("https://192.168.1.1/jwks")


def test_fetch_public_key_private_172_raises():
    platform = PlatformConf()
    with pytest.raises(InvalidKeySetUrl):
        platform.fetch_public_key("https://172.16.0.1/jwks")


def test_fetch_public_key_valid_url_returns_jwks():
    platform = PlatformConf()
    mock_response = MagicMock()
    mock_response.json.return_value = TOOL_KEY_SET
    with patch("lti1p3platform.ltiplatform.requests.get", return_value=mock_response):
        result = platform.fetch_public_key("https://example.com/jwks")
    assert result == TOOL_KEY_SET


def test_fetch_public_key_request_error_raises():
    platform = PlatformConf()
    with patch(
        "lti1p3platform.ltiplatform.requests.get",
        side_effect=requests.exceptions.ConnectionError("network failure"),
    ):
        with pytest.raises(LtiException):
            platform.fetch_public_key("https://example.com/jwks")


def test_fetch_public_key_invalid_json_raises():
    platform = PlatformConf()
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("not json")
    mock_response.text = "not json"
    with patch("lti1p3platform.ltiplatform.requests.get", return_value=mock_response):
        with pytest.raises(LtiException):
            platform.fetch_public_key("https://example.com/jwks")


# ---------------------------------------------------------------------------
# get_tool_key_set – non-HTTPS URL
# ---------------------------------------------------------------------------


def test_get_tool_key_set_non_https_url_raises():
    platform = PlatformConf()
    # Replace key set with None, set an HTTP URL
    platform._registration.set_tool_key_set(None)
    platform._registration.set_tool_key_set_url("http://example.com/jwks")
    with pytest.raises(InvalidKeySetUrl):
        platform.get_tool_key_set()


def test_get_tool_key_set_https_url_returns_and_caches():
    platform = PlatformConf()
    platform._registration.set_tool_key_set(None)
    platform._registration.set_tool_key_set_url("https://example.com/jwks")
    mock_response = MagicMock()
    mock_response.json.return_value = TOOL_KEY_SET
    with patch("lti1p3platform.ltiplatform.requests.get", return_value=mock_response):
        result = platform.get_tool_key_set()
    assert result == TOOL_KEY_SET
    # Subsequent call uses cache (no extra HTTP calls)
    result2 = platform.get_tool_key_set()
    assert result2 == TOOL_KEY_SET


# ---------------------------------------------------------------------------
# validate_jwt_format – error paths
# ---------------------------------------------------------------------------


def test_validate_jwt_format_wrong_parts():
    platform = PlatformConf()
    with pytest.raises(InvalidJwtToken, match="JWT must contain 3 parts"):
        platform.validate_jwt_format("only.two")


def test_validate_jwt_format_invalid_base64():
    platform = PlatformConf()
    with pytest.raises(InvalidJwtToken, match="can't be decoded"):
        platform.validate_jwt_format("!@#$.!@#$.!@#$")


# ---------------------------------------------------------------------------
# get_tool_public_key – error paths
# ---------------------------------------------------------------------------


def test_get_tool_public_key_no_kid_raises():
    platform = PlatformConf()
    claims = {
        "iss": "tool",
        "aud": "platform",
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 60,
    }
    token = jwt_encode(claims, TOOL_PRIVATE_KEY_PEM, algorithm="RS256")
    platform.validate_jwt_format(token)
    platform._jwt["header"].pop("kid", None)
    with pytest.raises(InvalidJwtToken, match="KID not found"):
        platform.get_tool_public_key()


def test_get_tool_public_key_no_alg_raises():
    platform = PlatformConf()
    jwk = _Registration.get_jwk(TOOL_PRIVATE_KEY_PEM)
    claims = {
        "iss": "tool",
        "aud": "platform",
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 60,
    }
    token = jwt_encode(
        claims, TOOL_PRIVATE_KEY_PEM, algorithm="RS256", headers={"kid": jwk.get("kid")}
    )
    platform.validate_jwt_format(token)
    platform._jwt["header"].pop("alg", None)
    with pytest.raises(InvalidJwtToken, match="ALG not found"):
        platform.get_tool_public_key()


def test_get_tool_public_key_kid_not_found_raises():
    platform = PlatformConf()
    jwk = _Registration.get_jwk(TOOL_PRIVATE_KEY_PEM)
    claims = {
        "iss": "tool",
        "aud": "platform",
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 60,
    }
    token = jwt_encode(
        claims, TOOL_PRIVATE_KEY_PEM, algorithm="RS256", headers={"kid": jwk.get("kid")}
    )
    platform.validate_jwt_format(token)
    platform._jwt["header"]["kid"] = "nonexistent-kid"
    with pytest.raises(InvalidJwtToken, match="Unable to find public key"):
        platform.get_tool_public_key()


# ---------------------------------------------------------------------------
# _is_token_replay / _is_nonce_replay
# ---------------------------------------------------------------------------


def test_token_replay_first_use_returns_false():
    platform = PlatformConf()
    assert platform._is_token_replay(str(uuid.uuid4()), int(time.time()) + 60) is False


def test_token_replay_second_use_returns_true():
    platform = PlatformConf()
    jti = str(uuid.uuid4())
    exp = int(time.time()) + 60
    platform._is_token_replay(jti, exp)
    assert platform._is_token_replay(jti, exp) is True


def test_nonce_replay_first_use_returns_false():
    platform = PlatformConf()
    assert platform._is_nonce_replay(str(uuid.uuid4()), int(time.time()) + 60) is False


def test_nonce_replay_second_use_returns_true():
    platform = PlatformConf()
    nonce = str(uuid.uuid4())
    exp = int(time.time()) + 60
    platform._is_nonce_replay(nonce, exp)
    assert platform._is_nonce_replay(nonce, exp) is True


# ---------------------------------------------------------------------------
# _validate_tool_access_token_assertion – error paths
# ---------------------------------------------------------------------------


def test_assertion_missing_jti_raises():
    platform = PlatformConf()
    decoded = {
        "iss": PLATFORM_CONFIG["client_id"],
        "sub": PLATFORM_CONFIG["client_id"],
        "aud": [PLATFORM_CONFIG["access_token_url"]],
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 60,
        # Missing "jti"
    }
    with pytest.raises(MissingRequiredClaim):
        platform._validate_tool_access_token_assertion(
            decoded, PLATFORM_CONFIG["access_token_url"]
        )


def test_assertion_invalid_iss_raises():
    platform = PlatformConf()
    decoded = {
        "iss": "wrong-client-id",
        "sub": PLATFORM_CONFIG["client_id"],
        "aud": [PLATFORM_CONFIG["access_token_url"]],
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 60,
        "jti": str(uuid.uuid4()),
    }
    with pytest.raises(InvalidClientAssertion, match="Invalid client_assertion iss"):
        platform._validate_tool_access_token_assertion(
            decoded, PLATFORM_CONFIG["access_token_url"]
        )


def test_assertion_invalid_sub_raises():
    platform = PlatformConf()
    decoded = {
        "iss": PLATFORM_CONFIG["client_id"],
        "sub": "wrong-sub",
        "aud": [PLATFORM_CONFIG["access_token_url"]],
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 60,
        "jti": str(uuid.uuid4()),
    }
    with pytest.raises(InvalidClientAssertion, match="Invalid client_assertion sub"):
        platform._validate_tool_access_token_assertion(
            decoded, PLATFORM_CONFIG["access_token_url"]
        )


def test_assertion_aud_string_wrong_raises():
    platform = PlatformConf()
    decoded = {
        "iss": PLATFORM_CONFIG["client_id"],
        "sub": PLATFORM_CONFIG["client_id"],
        "aud": "https://wrong-audience.example/token",
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 60,
        "jti": str(uuid.uuid4()),
    }
    with pytest.raises(
        InvalidClientAssertion, match="Invalid client_assertion audience"
    ):
        platform._validate_tool_access_token_assertion(
            decoded, PLATFORM_CONFIG["access_token_url"]
        )


def test_assertion_aud_string_correct_succeeds():
    platform = PlatformConf()
    decoded = {
        "iss": PLATFORM_CONFIG["client_id"],
        "sub": PLATFORM_CONFIG["client_id"],
        "aud": PLATFORM_CONFIG["access_token_url"],
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 60,
        "jti": str(uuid.uuid4()),
    }
    # Should not raise
    platform._validate_tool_access_token_assertion(
        decoded, PLATFORM_CONFIG["access_token_url"]
    )


def test_assertion_aud_invalid_type_raises():
    platform = PlatformConf()
    decoded = {
        "iss": PLATFORM_CONFIG["client_id"],
        "sub": PLATFORM_CONFIG["client_id"],
        "aud": 99999,  # Not a str or list
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 60,
        "jti": str(uuid.uuid4()),
    }
    with pytest.raises(InvalidClientAssertion, match="Invalid client_assertion aud"):
        platform._validate_tool_access_token_assertion(
            decoded, PLATFORM_CONFIG["access_token_url"]
        )


def test_assertion_iat_far_future_raises():
    platform = PlatformConf()
    decoded = {
        "iss": PLATFORM_CONFIG["client_id"],
        "sub": PLATFORM_CONFIG["client_id"],
        "aud": [PLATFORM_CONFIG["access_token_url"]],
        "iat": int(time.time()) + 300,  # 5 min into future (> 60s tolerance)
        "exp": int(time.time()) + 600,
        "jti": str(uuid.uuid4()),
    }
    with pytest.raises(InvalidClientAssertion, match="Invalid client_assertion iat"):
        platform._validate_tool_access_token_assertion(
            decoded, PLATFORM_CONFIG["access_token_url"]
        )


def test_assertion_exp_in_past_raises():
    platform = PlatformConf()
    decoded = {
        "iss": PLATFORM_CONFIG["client_id"],
        "sub": PLATFORM_CONFIG["client_id"],
        "aud": [PLATFORM_CONFIG["access_token_url"]],
        "iat": int(time.time()) - 120,
        "exp": int(time.time()) - 60,  # Already expired
        "jti": str(uuid.uuid4()),
    }
    with pytest.raises(InvalidClientAssertion, match="Invalid client_assertion exp"):
        platform._validate_tool_access_token_assertion(
            decoded, PLATFORM_CONFIG["access_token_url"]
        )


def test_assertion_jti_replay_raises():
    platform = PlatformConf()
    jti = str(uuid.uuid4())
    decoded = {
        "iss": PLATFORM_CONFIG["client_id"],
        "sub": PLATFORM_CONFIG["client_id"],
        "aud": [PLATFORM_CONFIG["access_token_url"]],
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 60,
        "jti": jti,
    }
    # First call succeeds
    platform._validate_tool_access_token_assertion(
        decoded, PLATFORM_CONFIG["access_token_url"]
    )
    # Second call with same JTI must fail
    decoded2 = dict(decoded)
    with pytest.raises(InvalidClientAssertion, match="Replay detected"):
        platform._validate_tool_access_token_assertion(
            decoded2, PLATFORM_CONFIG["access_token_url"]
        )


# ---------------------------------------------------------------------------
# get_access_token – error paths
# ---------------------------------------------------------------------------


def test_get_access_token_missing_claim_raises():
    platform = PlatformConf()
    with pytest.raises(MissingRequiredClaim):
        platform.get_access_token(
            {
                "grant_type": "client_credentials",
                "client_assertion": "xxx",
                "scope": "",
                # Missing "client_assertion_type"
            }
        )


def test_get_access_token_wrong_grant_type_raises():
    platform = PlatformConf()
    with pytest.raises(UnsupportedGrantType):
        platform.get_access_token(
            {
                "grant_type": "implicit",
                "client_assertion_type": (
                    "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
                ),
                "client_assertion": "xxx",
                "scope": "",
            }
        )


def test_get_access_token_wrong_assertion_type_raises():
    platform = PlatformConf()
    with pytest.raises(InvalidClientAssertion, match="Invalid client_assertion_type"):
        platform.get_access_token(
            {
                "grant_type": "client_credentials",
                "client_assertion_type": "wrong-type",
                "client_assertion": "xxx",
                "scope": "",
            }
        )


def test_get_access_token_unsupported_scope_returns_empty():
    platform = PlatformConf()
    encoded_jwt = _make_valid_assertion()
    result = platform.get_access_token(
        {
            "grant_type": "client_credentials",
            "client_assertion_type": (
                "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
            ),
            "client_assertion": encoded_jwt,
            "scope": "https://not.a.valid/scope",
        }
    )
    assert result["scope"] == ""
    assert result["token_type"] == "bearer"
    assert result["expires_in"] == 3600


# ---------------------------------------------------------------------------
# validate_deeplinking_resp
# ---------------------------------------------------------------------------


def test_validate_deeplinking_resp_empty_content_items():
    platform = PlatformConf()
    nonce = str(uuid.uuid4())
    token = _make_deeplink_jwt(nonce=nonce)
    result = platform.validate_deeplinking_resp({"JWT": token})
    assert result == []


def test_validate_deeplinking_resp_with_link_items():
    platform = PlatformConf()
    nonce = str(uuid.uuid4())
    items = [{"type": "ltiResourceLink", "url": "https://tool.example.com/resource"}]
    token = _make_deeplink_jwt(
        nonce=nonce,
        extra_claims={
            "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": items
        },
    )
    result = platform.validate_deeplinking_resp({"JWT": token})
    assert len(result) == 1
    assert result[0]["type"] == "ltiResourceLink"


def test_validate_deeplinking_resp_missing_nonce_raises():
    platform = PlatformConf()
    jwk = _Registration.get_jwk(TOOL_PRIVATE_KEY_PEM)
    claims = {
        "iss": "https://tool.example.com",
        "sub": PLATFORM_CONFIG["client_id"],
        "aud": PLATFORM_CONFIG["iss"],
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 60,
        # No nonce
        "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiDeepLinkingResponse",
        "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": [],
    }
    token = jwt_encode(
        claims, TOOL_PRIVATE_KEY_PEM, algorithm="RS256", headers={"kid": jwk.get("kid")}
    )
    with pytest.raises(LtiDeepLinkingResponseException, match="nonce is missing"):
        platform.validate_deeplinking_resp({"JWT": token})


def test_validate_deeplinking_resp_missing_exp_raises():
    """Token without exp claim should raise LtiDeepLinkingResponseException."""
    platform = PlatformConf()
    nonce = str(uuid.uuid4())
    jwk = _Registration.get_jwk(TOOL_PRIVATE_KEY_PEM)
    claims = {
        "iss": "https://tool.example.com",
        "sub": PLATFORM_CONFIG["client_id"],
        "aud": PLATFORM_CONFIG["iss"],
        "iat": int(time.time()) - 5,
        # No "exp" claim
        "nonce": nonce,
        "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiDeepLinkingResponse",
        "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": [],
    }
    token = jwt_encode(
        claims, TOOL_PRIVATE_KEY_PEM, algorithm="RS256", headers={"kid": jwk.get("kid")}
    )
    with pytest.raises(LtiDeepLinkingResponseException, match="exp is missing"):
        platform.validate_deeplinking_resp({"JWT": token})


def test_validate_deeplinking_resp_nonce_replay_raises():
    platform = PlatformConf()
    nonce = str(uuid.uuid4())
    # First request succeeds
    token1 = _make_deeplink_jwt(nonce=nonce)
    platform.validate_deeplinking_resp({"JWT": token1})
    # Second request with same nonce must be rejected
    token2 = _make_deeplink_jwt(nonce=nonce)
    with pytest.raises(LtiDeepLinkingResponseException, match="Replay detected"):
        platform.validate_deeplinking_resp({"JWT": token2})


def test_validate_deeplinking_resp_wrong_message_type_raises():
    platform = PlatformConf()
    nonce = str(uuid.uuid4())
    token = _make_deeplink_jwt(
        nonce=nonce,
        extra_claims={
            "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest"
        },
    )
    with pytest.raises(LtiDeepLinkingResponseException, match="Deep Linking Response"):
        platform.validate_deeplinking_resp({"JWT": token})


def test_validate_deeplinking_resp_unsupported_content_type_raises():
    platform = PlatformConf()
    nonce = str(uuid.uuid4())
    token = _make_deeplink_jwt(
        nonce=nonce,
        extra_claims={
            "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": [
                {"type": "unsupported_content_type"}
            ]
        },
    )
    with pytest.raises(LtiDeepLinkingResponseException, match="not supported"):
        platform.validate_deeplinking_resp({"JWT": token})


def test_validate_deeplinking_resp_fresh_tool_nonce_is_accepted():
    """Deep Linking responses accept fresh tool-generated nonces."""
    platform = PlatformConf()
    token = _make_deeplink_jwt()
    result = platform.validate_deeplinking_resp({"JWT": token})
    assert result == []


# ---------------------------------------------------------------------------
# validate_token
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# get_registration – _registration initially None path (lines 178-181)
# ---------------------------------------------------------------------------


def test_get_registration_lazy_loads_when_none():
    platform = _NullRegistrationPlatform()
    # _registration is None initially
    assert platform._registration is None
    reg = platform.get_registration()
    assert reg is not None
    # Second call returns cached instance
    assert platform.get_registration() is reg


# ---------------------------------------------------------------------------
# _validate_tool_access_token_assertion – no client_id (line 537)
# ---------------------------------------------------------------------------


def test_assertion_no_client_id_raises():
    platform = _NoClientIdPlatform()
    decoded = {
        "iss": PLATFORM_CONFIG["client_id"],
        "sub": PLATFORM_CONFIG["client_id"],
        "aud": [PLATFORM_CONFIG["access_token_url"]],
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 60,
        "jti": str(uuid.uuid4()),
    }
    with pytest.raises(PlatformNotReadyException, match="Client ID is not set"):
        platform._validate_tool_access_token_assertion(
            decoded, PLATFORM_CONFIG["access_token_url"]
        )


# ---------------------------------------------------------------------------
# get_access_token – no expected audience (line 658)
# ---------------------------------------------------------------------------


def test_get_access_token_no_audience_raises():
    platform = _NoAudiencePlatform()
    encoded_jwt = _make_valid_assertion()
    with pytest.raises(PlatformNotReadyException, match="Access token URL"):
        platform.get_access_token(
            {
                "grant_type": "client_credentials",
                "client_assertion_type": (
                    "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
                ),
                "client_assertion": encoded_jwt,
                "scope": "",
            }
        )


def _make_platform_token(extra_claims=None):
    """Return a JWT signed by the platform's private key."""
    platform = PlatformConf()
    claims = {
        "sub": PLATFORM_CONFIG["client_id"],
        "iss": PLATFORM_CONFIG["iss"],
        "scopes": "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
    }
    if extra_claims:
        claims.update(extra_claims)
    return platform._registration.platform_encode_and_sign(claims, expiration=3600)


def test_validate_token_valid_returns_true():
    platform = PlatformConf()
    token = _make_platform_token()
    assert platform.validate_token(token) is True


def test_validate_token_matching_scope_returns_true():
    platform = PlatformConf()
    token = _make_platform_token()
    assert (
        platform.validate_token(
            token,
            allowed_scopes=["https://purl.imsglobal.org/spec/lti-ags/scope/lineitem"],
        )
        is True
    )


def test_validate_token_non_matching_scope_returns_false():
    platform = PlatformConf()
    token = _make_platform_token()
    assert (
        platform.validate_token(
            token,
            allowed_scopes=["https://purl.imsglobal.org/spec/lti-ags/scope/score"],
        )
        is False
    )


def test_validate_token_invalid_iss_raises():
    """Token signed by platform key but with wrong iss should raise."""
    platform = PlatformConf()
    token = _Registration.encode_and_sign(
        {
            "sub": PLATFORM_CONFIG["client_id"],
            "iss": "https://wrong-issuer.example/",
            "scopes": "",
        },
        RSA_PRIVATE_KEY_PEM,
        expiration=3600,
    )
    with pytest.raises(InvalidJwtToken, match="Invalid issuer"):
        platform.validate_token(token)

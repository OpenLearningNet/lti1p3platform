import time
import uuid

from lti1p3platform.registration import Registration
from lti1p3platform.jwt_helper import jwt_encode

from .platform_config import TestPlatform, TOOL_PRIVATE_KEY_PEM, PLATFORM_CONFIG


def test_get_jwks():
    """
    Test get jwks
    """
    test_platform = TestPlatform()
    jwks = test_platform.get_jwks()

    expected_jwks = {
        "keys": [
            {
                "kty": "RSA",
                "e": "AQAB",
                "n": "1du-3Vg1huBld4X7y8FSy7bOFbEje00BJlpzCGYLAhKQL-kV4eeu6fQRJJ8rvknlElXUHs99_jTHAe0em0krUvkw-Q0Yiy1AAdhz6TNjoFPmD7NIhru0Qshm1LzQ1av5P_nbPDW5h9HgPXnxsBJ_Kzpeqx80WqUJ7GYvEbdVr76xxRebhI2iZN6YXLm0xoz0EUrN6FRPB2sdsMG1rhfY-g6t9QvjW1aByiG0SQviRyTD8iQKV1QcwMC13pPYmXapzxrJ-QvFogzjXyKMQeRmfony3AP5P5Tha4j5E_jDlWIkEkb66Hzl9bjdJCADXH4vINVPxR6WhDsAUVgO4dI4oQ",  # pylint: disable=line-too-long
                "kid": "JbXB1vA8IYHGMIX74Flshn2Z2Y91t94hBrKq2pM5HTc",
                "alg": "RS256",
                "use": "sig",
            }
        ]
    }

    assert jwks == expected_jwks


def test_get_access_tokens():
    """
    test get access token
    """
    test_platform = TestPlatform()

    jwt_claims = {
        "iss": PLATFORM_CONFIG["client_id"],
        "sub": PLATFORM_CONFIG["client_id"],
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 60,
        "jti": "lti-service-token-" + str(uuid.uuid4()),
    }
    jwk = Registration.get_jwk(TOOL_PRIVATE_KEY_PEM)
    encoded_jwt = jwt_encode(
        jwt_claims,
        TOOL_PRIVATE_KEY_PEM,
        algorithm="RS256",
        headers={"kid": jwk.get("kid")},
    )  # pylint: disable=line-too-long

    scopes = ["https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly"]
    token_request_data = {
        "grant_type": "client_credentials",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": encoded_jwt,
        "scope": " ".join(scopes),
    }

    access_token = test_platform.get_access_token(token_request_data)
    assert access_token.get("scope") == " ".join(scopes)

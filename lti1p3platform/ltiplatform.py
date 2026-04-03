from __future__ import annotations
from abc import ABC, abstractmethod
import time
import typing as t
import base64
import json
import ipaddress
from urllib.parse import urlparse
from typing_extensions import TypedDict
import requests

import jwt
from jwcrypto.jwk import JWK  # type: ignore

from .registration import Registration
from .constants import (
    LTI_1P3_ACCESS_TOKEN_SCOPES,
    LTI_1P3_ACCESS_TOKEN_REQUIRED_CLAIMS,
    LTI_DEEP_LINKING_ACCEPTED_TYPES,
)
from .exceptions import (
    MissingRequiredClaim,
    UnsupportedGrantType,
    InvalidKeySetUrl,
    LtiException,
    LtiDeepLinkingResponseException,
)


class JWKS(TypedDict):
    keys: t.List[t.Dict[str, t.Any]]


class JWT(TypedDict):
    header: t.Optional[t.Dict[str, t.Any]]
    body: t.Optional[t.Dict[str, t.Any]]


class AccessTokenResponse(TypedDict):
    access_token: str
    expires_in: int
    token_type: str
    scope: str


class LTI1P3PlatformConfAbstract(ABC):
    """
    LTI 1.3 Platform Data storage abstract class

    This class implements the Learning Tools Interoperability (LTI) 1.3 specification,
    which defines a standards-based approach for educational tools to integrate with
    learning platforms (e.g., LMS systems).

    LTI 1.3 Key Concepts:
    - Uses OAuth 2.0 authorization framework combined with OpenID Connect (OIDC)
    - Platform acts as the OAuth Authorization Server and OpenID Provider
    - Tool acts as the OAuth Client/Relying Party
    - Communication is secured via HTTPS and JWT (JSON Web Tokens)

    Security Architecture:
    - Platform and Tool exchange cryptographic keys via JWK Sets (JSON Web Key Sets)
    - All messages are signed JWTs using RS256 (RSA with SHA-256)
    - Audience ('aud') claim validates the token is intended for specific recipient
    - Nonce and JTI (JWT ID) claims prevent token replay attacks
    - All URLs must use HTTPS for production (except localhost for development)

    Key Flows:
    1. OIDC Login Initiation: Platform redirects user to tool's OIDC login endpoint
    2. Authorization: Tool routes back through platform's OIDC authorization endpoint
    3. Token Validation: Platform validates signed ID token from tool
    4. Message Launch: Platform sends signed LTI message with user/context claims
    5. Service Calls: Tool calls platform APIs (AGS, NRPS) with signed access tokens

    References:
    - IMS LTI 1.3 Core: https://www.imsglobal.org/spec/lti/v1p3/
    - IMS Security Framework: https://www.imsglobal.org/spec/security/v1p0/
    - OpenID Connect Core: https://openid.net/specs/openid-connect-core-1_0.html
    """

    _registration = None
    _accepted_deeplinking_types = LTI_DEEP_LINKING_ACCEPTED_TYPES

    def __init__(self, **kwargs: t.Any) -> None:
        self._jwt: t.Dict[str, t.Any] = {}

        self.init_platform_config(**kwargs)

    @abstractmethod
    def init_platform_config(self, **kwargs: t.Any) -> t.Any:
        pass

    @abstractmethod
    def cache_get(self, key: str) -> t.Optional[int]:
        """
        Retrieve a replay-detection entry from the cache.

        Keying convention:
        - JTI replay checks use key  ``"jti:<jti_value>"``
        - Nonce replay checks use key ``"nonce:<nonce_value>"``

        Returns:
            The stored expiration timestamp (UNIX seconds) if the entry
            exists and has not yet expired, or ``None`` otherwise.

        Production implementations:

        **Redis**::

            def cache_get(self, key):
                val = redis_client.get(key)
                return int(val) if val is not None else None

        **Django cache**::

            def cache_get(self, key):
                return cache.get(key)

        **Memcached**::

            def cache_get(self, key):
                return mc.get(key)
        """
        raise NotImplementedError()

    @abstractmethod
    def cache_set(self, key: str, exp: int) -> None:
        """
        Store a replay-detection entry in the cache.

        Parameters:
            key: Namespaced cache key (e.g. ``"jti:abc123"`` or ``"nonce:xyz789"``).
            exp: UNIX timestamp at which the associated token/nonce expires.
                 Implementations should derive the TTL from this value so
                 entries are evicted automatically.

        Production implementations:

        **Redis**::

            def cache_set(self, key, exp):
                ttl = max(1, exp - int(time.time()))
                redis_client.set(key, exp, ex=ttl)

        **Django cache**::

            def cache_set(self, key, exp):
                ttl = max(1, exp - int(time.time()))
                cache.set(key, exp, timeout=ttl)

        **Memcached**::

            def cache_set(self, key, exp):
                ttl = max(1, exp - int(time.time()))
                mc.set(key, exp, time=ttl)
        """
        raise NotImplementedError()

    @abstractmethod
    def get_registration_by_params(
        self,
        **kwargs: t.Any,
    ) -> Registration:
        raise NotImplementedError()

    def set_accepted_deeplinking_types(
        self, types: t.List[str]
    ) -> LTI1P3PlatformConfAbstract:
        accepted_deeplinking_types = set()
        for _type in types:
            if _type in LTI_DEEP_LINKING_ACCEPTED_TYPES:
                accepted_deeplinking_types.add(_type)

        self._accepted_deeplinking_types = accepted_deeplinking_types

        return self

    def get_registration(self, **kwargs: t.Any) -> Registration:
        if not self._registration:
            self._registration = self.get_registration_by_params(**kwargs)

        return self._registration

    def get_jwks(self) -> JWKS:
        """
        Get JWKS (JSON Web Key Set) from the platform

        The platform exposes its public keys via a JWK Set endpoint.
        Tools fetch these keys to validate signatures on messages from the platform.

        LTI 1.3 Spec Reference: https://www.imsglobal.org/spec/lti/v1p3/#platform-jwks

        Returns:
            JWKS: Dictionary with 'keys' list containing JWK objects
        """
        assert self._registration is not None, "Registration not yet set"

        return {"keys": self._registration.get_jwks()}

    def fetch_public_key(self, key_set_url: str) -> JWKS:
        """
        Fetch tool's public key set from the provided URL

        Security Requirements (LTI 1.3 Spec & 1EdTech Security Framework):
        1. URL MUST use HTTPS (https:// scheme required)
           - Prevents man-in-the-middle attacks
           - TLS 1.2+ provides encryption and authentication

        2. No Private IP Addresses:
           - Reject private/RFC 1918 IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
           - Prevents Server-Side Request Forgery (SSRF) attacks on internal infrastructure
           - Reject loopback/localhost addresses (127.0.0.1, ::1)
           - Reject link-local addresses (169.254.x.x)
           - Reject reserved/multicast addresses

        3. Hostname Validation:
           - Reject literal hostname 'localhost' (bypass check)
           - Accept only fully-qualified domain names in production

        These restrictions prevent:
        - Attacks on internal services (databases, admin panels, cloud metadata endpoints)
        - Bypassing network security controls

        LTI 1.3 References:
        - Transport security: https://www.imsglobal.org/spec/lti/v1p3/#securing_web_services
        - 1EdTech Security Framework: https://www.imsglobal.org/spec/security/v1p0/

        Raises:
            InvalidKeySetUrl: If URL doesn't meet security requirements
            LtiException: If network request fails or response is invalid JSON

        Returns:
            JWKS: The fetched JSON Web Key Set
        """
        parsed_url = urlparse(key_set_url)
        if parsed_url.scheme != "https":
            raise InvalidKeySetUrl

        hostname = parsed_url.hostname or ""
        if hostname in {"localhost"}:
            raise InvalidKeySetUrl

        try:
            host_ip = ipaddress.ip_address(hostname)
            if (
                host_ip.is_private
                or host_ip.is_loopback
                or host_ip.is_link_local
                or host_ip.is_reserved
                or host_ip.is_multicast
            ):
                raise InvalidKeySetUrl
        except ValueError:
            # Hostname is not an IP literal. Continue.
            pass

        try:
            resp = requests.get(key_set_url, timeout=5)
        except requests.exceptions.RequestException as exc:
            raise LtiException(
                "Error during fetch URL " + key_set_url + ": " + str(exc)
            ) from exc
        try:
            public_key = resp.json()

            return public_key  # type: ignore
        except ValueError as exc:
            raise LtiException(
                "Invalid response from " + key_set_url + ". Must be JSON: " + resp.text
            ) from exc

    def get_tool_key_set(self) -> JWKS:
        """
        Get tool public key
        """
        assert self._registration is not None, "Registration not yet set"

        tool_key_set = self._registration.get_tool_key_set()
        tool_key_set_url = self._registration.get_tool_key_set_url()

        if not tool_key_set:
            assert (
                tool_key_set_url is not None
            ), "If public_key_set is not set, public_set_url should be set"
            if tool_key_set_url.startswith("https://"):
                tool_key_set = self.fetch_public_key(tool_key_set_url)
                self._registration.set_tool_key_set(tool_key_set)
            else:
                raise InvalidKeySetUrl

        return tool_key_set

    def urlsafe_b64decode(self, val):
        # type: (str) -> str
        remainder = len(val) % 4
        if remainder > 0:
            padlen = 4 - remainder
            val = val + ("=" * padlen)

        tmp = val.translate(str.maketrans("-_", "+/"))
        return base64.b64decode(tmp).decode("utf-8")

    def validate_jwt_format(self, jwt_token_string: str) -> None:
        jwt_parts = jwt_token_string.split(".")

        if len(jwt_parts) != 3:
            # Invalid number of parts in JWT.
            raise LtiException("Invalid id_token, JWT must contain 3 parts")

        try:
            # Decode JWT headers.
            header = self.urlsafe_b64decode(jwt_parts[0])
            self._jwt["header"] = json.loads(header)

            # Decode JWT body.
            body = self.urlsafe_b64decode(jwt_parts[1])
            self._jwt["body"] = json.loads(body)
        except Exception as exc:
            raise LtiException("Invalid JWT format, can't be decoded") from exc

    def get_tool_public_key(self) -> bytes:
        tool_key_set = self.get_tool_key_set()

        # Find key used to sign the JWT (matches the KID in the header)
        kid = self._jwt.get("header", {}).get("kid", None)
        alg = self._jwt.get("header", {}).get("alg", None)

        if not kid:
            raise LtiException("JWT KID not found")
        if not alg:
            raise LtiException("JWT ALG not found")

        for key in tool_key_set["keys"]:
            key_kid = key.get("kid")
            key_alg = key.get("alg", "RS256")
            if key_kid and key_kid == kid and key_alg == alg:
                try:
                    key_json = json.dumps(key)
                    jwk_obj = JWK.from_json(key_json)
                    return jwk_obj.export_to_pem()  # type: ignore
                except (ValueError, TypeError) as error:
                    raise LtiException("Can't convert JWT key to PEM format") from error

        # Could not find public key with a matching kid and alg.
        raise LtiException("Unable to find public key")

    def tool_validate_and_decode(
        self, jwt_token_string: str, audience: str
    ) -> t.Dict[str, t.Any]:
        """
        Validate and decode a JWT token from the tool

        LTI 1.3 JWT Validation Process:
        1. Format Validation: JWT must have 3 parts separated by dots (header.payload.signature)
        2. Signature Verification: Use tool's public key to validate the signature (RS256)
        3. Audience Validation: Verify the 'aud' claim matches the expected platform
           - Ensures tool created this token specifically for us
           - Prevents token confusion attacks
        4. Additional claims verified by PyJWT:
           - 'exp' (expiration): Token must not be expired
           - 'iat' (issued at): Token must not be issued in the future (clock skew tolerance)

        Why Audience Verification is Critical:
        - Without audience verification, tokens created for one recipient could be misused
        - Example attack: Token meant for Platform A used to access Platform B
        - Audience claim ties the token to a specific platform instance

        OpenID Connect Spec Reference:
                - ID Token validation:
                    https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation

        Parameters:
            jwt_token_string: The JWT token to validate (format: header.payload.signature)
            audience: The expected audience value from 'aud' claim

        Returns:
            dict: Decoded JWT payload (claims)

        Raises:
            LtiException: If JWT format is invalid
            jwt.InvalidAudienceError: If audience doesn't match
            jwt.ExpiredSignatureError: If token is expired
        """
        self.validate_jwt_format(jwt_token_string)

        public_key = self.get_tool_public_key()

        return jwt.decode(
            jwt_token_string,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": True},
            audience=audience,
        )

    def _is_token_replay(self, jti: str, exp: int) -> bool:
        """
        Detect and prevent JWT token replay attacks using JTI (JWT ID)

        Replay Attack Prevention Strategy:
        - Each JWT must include a 'jti' (JWT ID) claim - a unique identifier per token
        - Platform maintains an in-memory cache of all seen JTIs
        - If same JTI appears twice, it's a replay attack
        - Cache is cleaned of expired JTIs to prevent unbounded memory growth

        Why JTI is Required (LTI 1.3 Spec):
        - Prevents attacker from replaying intercepted tokens
        - Example: Attacker intercepts token with jti='abc123', tries to replay it
        - Platform recognizes jti='abc123' already used, rejects the replay

        Implementation Notes:
        - Expiration timestamp used for cache cleanup (best-effort)
        - Expired JTIs can be safely removed since they can't be valid anyway
        - Token signature validation + JTI check provides defense-in-depth

        1EdTech Security Framework Reference:
                - JWT Bearer Assertions:
                    https://www.imsglobal.org/spec/security/v1p0/#making_authenticated_requests

        Parameters:
            jti: The JWT ID claim value from the token
            exp: The expiration timestamp of the token (UNIX timestamp)

        Returns:
            bool: True if this is a replay (JTI previously seen), False if unique (first time)
        """
        cache_key = f"jti:{jti}"
        if self.cache_get(cache_key) is not None:
            return True
        self.cache_set(cache_key, exp)
        return False

    def _is_nonce_replay(self, nonce: str, exp: int) -> bool:
        """
        Detect and prevent nonce replay attacks in deep linking responses

        Nonce (Number Used Once) Security:
        - Platform generates a random nonce for each deep linking request
        - Tool includes this nonce in the deep linking response
        - Platform validates that the received nonce matches what it sent
        - This is a Cross-Site Request Forgery (CSRF) protection mechanism

        Replay Attack Prevention:
        - Platform caches all nonces received from tools
        - If same nonce appears twice, it indicates a replay/reuse attempt
        - Cache is cleaned of expired nonces to prevent unbounded memory growth
        - Prevents attacker from reusing old deep linking messages

        Flow Example:
        1. Platform generates nonce='xyz789' and sends to tool
        2. Tool includes nonce='xyz789' in deep linking response
        3. Platform caches nonce='xyz789' with expiration time
        4. If nonce='xyz789' appears again, it's rejected as replay

        OpenID Connect Specification:
        - Nonce validation prevents authorization code/token replay attacks
        - See: https://openid.net/specs/openid-connect-core-1_0.html#NonceNotes

        LTI Deep Linking Spec Reference:
        - Deep linking request/response: https://www.imsglobal.org/spec/lti-dl/v2p0/

        Parameters:
            nonce: The nonce value from the deep linking response
            exp: The expiration timestamp of the response (UNIX timestamp)

        Returns:
            bool: True if this is a replay (nonce previously seen), False if unique
        """
        cache_key = f"nonce:{nonce}"
        if self.cache_get(cache_key) is not None:
            return True
        self.cache_set(cache_key, exp)
        return False

    def _validate_tool_access_token_assertion(
        self, decoded_assertion: t.Dict[str, t.Any], expected_audience: str
    ) -> None:
        """
        Validate semantic correctness of tool's access token assertion (client credentials JWT)

        LTI 1.3 Tool Access Token Request Flow (OAuth 2.0 Client Credentials Grant):
        1. Tool wants to call platform APIs (e.g., Grade Passback via AGS)
        2. Tool creates a JWT assertion signed with its private key
        3. Tool sends this assertion to platform's token endpoint
        4. Platform validates the assertion and returns an access_token
        5. Tool uses access_token to call platform APIs

        JWT Assertion Requirements (1EdTech Security Framework):
        - client_assertion_type: Must be "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
        - Claims that must be present:
          * iss (issuer): Client ID - identifies the tool making the request
          * sub (subject): Client ID - same as iss (tool is resource owner)
                    * aud (audience): Token endpoint URL - tool asserts this token is for
                        platform's token endpoint
          * iat (issued at): Timestamp when token was created
          * exp (expiration): Timestamp when token expires
          * jti (JWT ID): Random unique identifier, prevents token replay attacks

        Semantic Validation Rules:
        1. Required Claims Check: All 6 required claims must be present
        2. iss Must Equal Client ID: Ensures tool is who they claim to be
        3. sub Must Equal Client ID: OAuth 2.0 convention (resource owner is the tool)
        4. aud Must Include Token Endpoint: Prevents token confusion attacks
           - Token created for token endpoint can't be misused for other endpoints
        5. Timing Validation:
           - iat must not be in future (within 60 second clock skew tolerance)
           - exp must not be in past (token must not be expired)
        6. JTI Uniqueness: No replay of same jti value (prevents token reuse)

        Security Implications:
        - These checks ensure tool authentication, token intent, and prevent replay attacks
        - Without these, unauthorized tools could impersonate real tools
        - Without audience validation, tokens could be misused at wrong endpoints

        1EdTech Security Framework Reference:
        - https://www.imsglobal.org/spec/security/v1p0/#securing_web_services
        - https://www.imsglobal.org/spec/security/v1p0/#token_request

        Parameters:
            decoded_assertion: The decoded JWT payload with all claims
            expected_audience: The platform's token endpoint URL (should match aud claim)

        Raises:
            MissingRequiredClaim: If required header/claim is missing
            LtiException: If any semantic validation fails (iss, sub, aud, timing, jti)
        """
        assert self._registration is not None, "Registration not yet set"

        required_claims = ["iss", "sub", "aud", "iat", "exp", "jti"]
        for required_claim in required_claims:
            if required_claim not in decoded_assertion:
                raise MissingRequiredClaim(
                    f"The required claim {required_claim} is missing from client_assertion JWT."
                )

        client_id = self._registration.get_client_id()
        if not client_id:
            raise LtiException("Client ID is not set")

        print(decoded_assertion)
        if decoded_assertion["iss"] != client_id:
            raise LtiException("Invalid client_assertion iss")

        if decoded_assertion["sub"] != client_id:
            raise LtiException("Invalid client_assertion sub")

        aud_claim = decoded_assertion.get("aud")
        if isinstance(aud_claim, str):
            aud_values = [aud_claim]
        elif isinstance(aud_claim, list):
            aud_values = aud_claim
        else:
            raise LtiException("Invalid client_assertion aud")

        if expected_audience not in aud_values:
            raise LtiException("Invalid client_assertion audience")

        now = int(time.time())
        iat = int(decoded_assertion["iat"])
        exp = int(decoded_assertion["exp"])
        if iat > now + 60:
            raise LtiException("Invalid client_assertion iat")
        if exp <= now:
            raise LtiException("Invalid client_assertion exp")

        jti = str(decoded_assertion["jti"])
        if self._is_token_replay(jti, exp):
            raise LtiException("Replay detected for client_assertion jti")

    def get_access_token(
        self, token_request_data: t.Dict[str, t.Any]
    ) -> AccessTokenResponse:
        """
        Validate tool's token request and return JWT access token

        OAuth 2.0 Client Credentials Grant with JWT Bearer Assertion:
        This endpoint implements the OAuth 2.0 Client Credentials Grant Type using
        JWT Bearer Assertions as per the 1EdTech Security Framework.

        Request Flow:
        1. Tool sends POST to /token with:
           - grant_type = "client_credentials"
           - client_assertion = signed JWT (tool's credentials)
           - client_assertion_type = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
                     - scope = requested platform capabilities
                         (e.g., "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly")

        2. Platform validates:
           - client_assertion_type is exactly the specified Bearer assertion type
           - client_assertion JWT has valid signature (signed by tool's private key)
           - JWT contains required claims (iss, sub, aud, iat, exp, jti)
           - JWT claims are semantically correct (iss==client_id, aud includes token endpoint)
           - JWT hasn't been used before (jti not in cache)
           - JWT is not expired and not issued in future

        3. Platform returns:
           - access_token: Signed JWT containing scope and other claims
           - token_type: "Bearer"
           - expires_in: seconds until token expires
           - scope: list of granted capabilities

        Token Usage:
        - Tool includes access_token in Authorization header when calling platform APIs
        - Example: "Authorization: Bearer <access_token>"
        - Platform validates token signature and verifies requested scopes

        Security Benefits:
        - JWT Bearer Assertions: No shared secrets, only public/private key pairs
        - Prevents unauthorized tools from requesting tokens
        - Nonce-like mechanism (jti) prevents token reuse/replay attacks
        - Signed tokens can be verified offline without hitting a database

        Reference:
                - 1EdTech Security Framework:
                    https://www.imsglobal.org/spec/security/v1p0/#securing_web_services
        - LTI Advantage Services (AGS spec): https://www.imsglobal.org/spec/lti-ags/v2p0/

        Parameters:
            token_request_data: Dict of form parameters:
                - grant_type: Must be "client_credentials"
                - client_assertion: Signed JWT from tool
                                - client_assertion_type: Must be
                                    "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
                - scope: Space-separated list of requested scopes

        Returns:
            AccessTokenResponse: Dictionary with 'access_token', 'expires_in', 'token_type', 'scope'

        Raises:
            UnsupportedGrantType: If grant_type is not client_credentials
            LtiException: Various validation failures (see _validate_tool_access_token_assertion)
        """
        assert self._registration is not None, "Registration not yet set"

        private_key = self._registration.get_platform_private_key()
        assert private_key is not None, (
            "Platform private key not yet set. "
            "Please set it with set_platform_private_key()"
        )

        # Check if all required claims are present
        for required_claim in LTI_1P3_ACCESS_TOKEN_REQUIRED_CLAIMS:
            if required_claim not in token_request_data.keys():
                raise MissingRequiredClaim(
                    f"The required claim {required_claim} is missing from the JWT."
                )

        # Check that grant type is `client_credentials`
        if token_request_data["grant_type"] != "client_credentials":
            raise UnsupportedGrantType()

        if token_request_data["client_assertion_type"] != (
            "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
        ):
            raise LtiException("Invalid client_assertion_type")

        expected_audience = self._registration.get_access_token_url()
        if not expected_audience:
            raise LtiException("No expected audience configured")

        # Validate JWT token
        decoded_assertion = self.tool_validate_and_decode(
            token_request_data["client_assertion"], audience=expected_audience
        )
        self._validate_tool_access_token_assertion(decoded_assertion, expected_audience)

        # Check scopes and only return valid and supported ones
        valid_scopes = []
        requested_scopes = token_request_data["scope"].split(" ")

        for scope in requested_scopes:
            # TODO: Add additional checks for permitted scopes
            # Currently there are no scopes, because there is no use for
            # these access tokens until a tool needs to access the LMS.
            # LTI Advantage extensions make use of this.
            if scope in LTI_1P3_ACCESS_TOKEN_SCOPES:
                valid_scopes.append(scope)

        # Scopes are space separated as described in
        # https://tools.ietf.org/html/rfc6749
        scopes_str = " ".join(valid_scopes)

        # This response is compliant with RFC 6749
        # https://tools.ietf.org/html/rfc6749#section-4.4.3
        return {
            "access_token": self._registration.encode_and_sign(
                {
                    "sub": self._registration.get_client_id(),
                    "iss": self._registration.get_iss(),
                    "scopes": scopes_str,
                },
                private_key,
                # Create token valid for 3600 seconds (1h) as per specification
                # https://www.imsglobal.org/spec/security/v1p0/#expires_in-values-and-renewing-the-access-token
                expiration=3600,
            ),
            "token_type": "bearer",
            "expires_in": 3600,
            "scope": scopes_str,
        }

    def validate_deeplinking_resp(
        self, token_request_data: t.Dict[str, t.Any]
    ) -> t.List[t.Dict[str, t.Any]]:
        jwt_token_string = token_request_data["JWT"]
        assert self._registration is not None, "Registration not yet set"

        expected_audience = self._registration.get_iss()
        assert expected_audience is not None

        deep_link_response = self.tool_validate_and_decode(
            jwt_token_string, audience=expected_audience
        )

        nonce = deep_link_response.get("nonce")
        if not nonce:
            raise LtiDeepLinkingResponseException("Token nonce is missing")

        exp = deep_link_response.get("exp")
        if not exp:
            raise LtiDeepLinkingResponseException("Token exp is missing")

        if self._is_nonce_replay(str(nonce), int(exp)):
            raise LtiDeepLinkingResponseException("Replay detected for token nonce")

        # Check the response is a Deep Linking response type
        message_type = deep_link_response.get(
            "https://purl.imsglobal.org/spec/lti/claim/message_type"
        )
        if not message_type == "LtiDeepLinkingResponse":
            raise LtiDeepLinkingResponseException(
                "Token isn't a Deep Linking Response message."
            )

        # Check if supported contentitems were returned
        content_items = deep_link_response.get(
            "https://purl.imsglobal.org/spec/lti-dl/claim/content_items",
            # If not found, return empty list
            [],
        )
        if self._accepted_deeplinking_types and any(
            item["type"] not in self._accepted_deeplinking_types
            for item in content_items
        ):
            raise LtiDeepLinkingResponseException("Content item type is not supported")

        # Return contentitems
        return content_items  # type: ignore

    def validate_token(
        self,
        token: str,
        allowed_scopes: t.Optional[t.List[str]] = None,
        audience: t.Optional[str] = None,
    ) -> bool:
        """
        Validate token.

        Parameters:
            token: Token to validate

        Returns:
            is_valid: True if token is valid, False otherwise
        """
        assert self._registration is not None, "Registration not yet set"

        public_key = self._registration.get_platform_public_key()
        assert public_key is not None

        token_contents = Registration.decode_and_verify(
            token, public_key, audience=audience
        )

        if token_contents.get("iss") != self._registration.get_iss():
            raise LtiException("Invalid issuer")

        if "exp" in token_contents and token_contents["exp"] < time.time():
            raise LtiException("Token expired")

        token_scopes = token_contents.get("scopes", "").split(" ")

        if allowed_scopes:
            return any(scope in token_scopes for scope in allowed_scopes)

        return True

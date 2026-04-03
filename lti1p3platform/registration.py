from __future__ import annotations

import typing as t
import time
import json
from jwcrypto.jwk import JWK  # type: ignore

import jwt


from .jwt_helper import jwt_encode

if t.TYPE_CHECKING:
    from .ltiplatform import JWKS


# pylint: disable=too-many-instance-attributes, too-many-public-methods
class Registration:
    """
    Platform registration data storage class
    
    LTI 1.3 Registration Data Model:
    This class stores the configuration needed for secure OAuth 2.0 / OIDC communication
    between a learning platform and an external tool/service.
    
    Key Concepts:
    - Issuer (iss): Unique identifier for the learning platform
    - Client ID: Platform's identifier issued by the tool (used in OAuth 2.0 flows)
    - Deployment ID: Organization or account identifier; allows multiple deployments per issuer
    
    Public Key Exchange:
    - Platform Public Key: Used by tool to verify platform-signed messages
    - Tool Public Key Set URL: Tool's JWKS endpoint; platform fetches these to verify tool's signatures
    
    OAuth 2.0 / OIDC Endpoints:
    - OIDC Login URL: Tool's endpoint for initiating OIDC Login (3rd-party-initiated)
    - Access Token URL: Platform's token endpoint where tool requests access tokens
      * Used in OAuth 2.0 Client Credentials grant
      * Tool sends JWT assertion signed with its private key
      * Platform returns access_token used for AGS/NRPS API calls
    
    Launch URLs:
    - Launch URL: Endpoint where platform sends LTI resource link messages
    - Deep Link Launch URL: Endpoint where platform sends deep linking requests
    
    Security: All data should be stored securely; private keys must be protected.
    Reference: https://www.imsglobal.org/spec/lti/v1p3/
    """

    _iss = None
    _launch_url = None
    _client_id = None
    _deployment_id = None
    _oidc_login_url = None
    _access_token_url = None
    _tool_keyset_url = None
    _tool_keyset = None
    _tool_redirect_uris = None
    _platform_public_key = None
    _platform_private_key = None
    _deeplink_launch_url = None

    def get_iss(self) -> t.Optional[str]:
        """
        Get issuer (Identifier for the platform)
        
        In LTI 1.3 / OIDC terminology:
        - 'iss' is the issuer claim in JWT tokens
        - Uniquely identifies the learning platform instance
        - Example: "https://platform.example.com"
        - Used in token audience validation and claims
        """
        return self._iss

    def get_launch_url(self) -> t.Optional[str]:
        """
        Get tool provider launch url (Resource Link Launch Request endpoint)
        
        LTI 1.3 Launch Flow:
        1. Platform user clicks "launch tool" link on platform
        2. Platform sends signed LTI Message JWT to this URL
        3. Tool receives message, validates signature/claims, renders tool interface
        
        Message Contents (JWT claims):
        - https://purl.imsglobal.org/spec/lti/claim/resource_link (resource context)
        - https://purl.imsglobal.org/spec/lti/claim/roles (user roles)
        - https://purl.imsglobal.org/spec/lti/claim/user_id (user identifier)
        - And many other context claims
        
        Reference: https://www.imsglobal.org/spec/lti/v1p3/#resource-link-request
        """
        return self._launch_url

    def get_client_id(self) -> t.Optional[str]:
        """
        Get platform client id (OAuth 2.0 Client Identifier)
        
        The client_id is assigned by the tool to the platform during registration.
        It identifies the platform in OAuth 2.0 / OIDC flows:
        
        Usage sites:
        1. Tool's OIDC Login endpoint:
           - User redirects to tool /login?iss=&client_id=<platform-client-id>&...
           - Client ID tells tool "this is from the platform I spoke to"
        
        2. Platform's Token endpoint:
           - Tool sends JWT assertion with claim: iss=<platform-client-id>
           - Platform verifies this matches registered client_id
        
        3. OAuth 2.0 JWT Bearer Assertion:
           - Both 'iss' and 'sub' claim must equal client_id
           - This ties the assertion to the specific platform
        
        Reference (OAuth 2.0 Client Credentials): https://tools.ietf.org/html/rfc6749#section-4.4
        """
        return self._client_id

    def get_deployment_id(self) -> t.Optional[str]:
        """
        Get deployment id (Organization / Tenant Identifier)
        
        The deployment_id allows a single issuer (learning platform instance)
        to support multiple organizations/institutions/accounts.
        
        Examples:
        - SaaS platform with multiple school districts: each has its own deployment_id
        - University system with multiple campuses: each campus has deployment_id
        
        Usage:
        - Included in LTI launch message as claim:
          'https://purl.imsglobal.org/spec/lti/claim/deployment_id'
        - Tool can use this to determine which customer sent the message
        - Enables multi-tenant tool deployments
        
        Reference: https://www.imsglobal.org/spec/lti/v1p3/#tool-and-platform-identifiers
        """
        return self._deployment_id

    def get_oidc_login_url(self) -> t.Optional[str]:
        """
        Get OIDC login url (Tool's OIDC Login Initiation Endpoint)
        
        OIDC 3rd-Party-Initiated Login Flow (OpenID Connect):
        This is how the LTI launch begins - tool initiates OIDC login.
        
        Flow:
        1. Platform URL called: /oidc_login?iss=<platform-iss>&...
        2. Platform responds with redirect to this URL:
           /tool_login_endpoint?iss=<iss>&client_id=<client_id>&...
        3. Tool's OIDC Login endpoint:
           - Validates parameters
           - Checks if platform (iss) is registered
           - Generates state/nonce for CSRF protection
           - Redirects user to platform authorization endpoint
        
        This URL is called by the platform during OIDC login initiation.
        Platform calls this endpoint as part of OAuth 2.0 + OIDC integration.
        
        Reference (3rd-Party-Initiated Login):
        - https://openid.net/specs/openid-connect-core-1_0.html#ThirdPartyInitiatedLogin
        - https://www.imsglobal.org/spec/lti/v1p3/#step-1-third-party-initiated-login
        """
        return self._oidc_login_url

    def get_platform_public_key(self) -> t.Optional[str]:
        """
        Get Platform public key in PEM format (RS256 public key)
        
        Key Exchange in LTI 1.3:
        - Platform has an RSA key pair (public + private)
        - Platform shares its PUBLIC key with tool during registration
        - Tool stores platform's public key
        - When platform sends messages/tokens, it signs with PRIVATE key
        - Tool verifies signature with platform's PUBLIC key
        
        This public key is used by the tool to verify:
        1. ID Tokens (OIDC messages) from platform
        2. JWT assertions in authorization server requests
        3. Any messages signed by the platform
        
        Security: Only the public key is shared. Private key never leaves platform.
        
        Format: PEM-encoded RSA public key (typically 2048 or 4096 bit)
        Algorithm: RS256 (RSA with SHA-256)
        
        Reference: https://www.imsglobal.org/spec/lti/v1p3/#platform-keyset
        """
        return self._platform_public_key

    def get_access_token_url(self) -> t.Optional[str]:
        """
        Get OAuth 2 access token URL (Token Endpoint / Authorization Server Endpoint)
        
        This is the platform's token endpoint where tool requests access tokens.
        
        OAuth 2.0 Client Credentials Grant with JWT Bearer Assertion:
        1. Tool wants to call platform APIs (e.g., submit grades via AGS)
        2. Tool creates JWT assertion signed with its private key
        3. Tool sends: POST /token
           - grant_type=client_credentials
           - client_assertion=<signed-jwt>
           - client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer
        4. Platform validates JWT, returns access_token
        5. Tool uses access_token to call platform APIs
        
        Audience Validation:
        - The JWT assertion must include 'aud' claim = this access_token_url
        - Prevents assertionintended for endpoint A from being misused at endpoint B
        - Security mechanism: "this token was created specifically for this endpoint"
        
        Format: Full HTTPS URL to platform's token endpoint
        Example: "https://platform.example.com/lti/token"
        
        Reference:
        - Token endpoint: https://www.imsglobal.org/spec/lti/v1p3/#access-token-endpoint
        - 1EdTech Security Framework: https://www.imsglobal.org/spec/security/v1p0/#token_request
        """
        return self._access_token_url

    def get_platform_private_key(self) -> t.Optional[str]:
        """
        Get Platform private key in PEM format
        """
        return self._platform_private_key

    def get_deeplink_launch_url(self) -> t.Optional[str]:
        """
        Get deep link launch url
        A url used by the platform to initiate LTI deep link
        launch, sometimes it's the same as launch url
        """
        return self._deeplink_launch_url

    def set_iss(self, iss: str) -> Registration:
        """
        Set issuer
        """
        self._iss = iss

        return self

    def set_launch_url(self, launch_url: str) -> Registration:
        """
        Set tool provider launch url
        """
        self._launch_url = launch_url

        return self

    def set_client_id(self, client_id: str) -> Registration:
        """
        Set platform client id
        """
        self._client_id = client_id

        return self

    def set_deployment_id(self, deployment_id: str) -> Registration:
        """
        Set deployment id
        """
        self._deployment_id = deployment_id

        return self

    def set_oidc_login_url(self, oidc_login_url: str) -> Registration:
        """
        Set OIDC login url
        """
        self._oidc_login_url = oidc_login_url

        return self

    def set_access_token_url(self, access_token_url: str) -> Registration:
        """
        Set OAuth 2 access token URL (authorization server audience)
        """
        self._access_token_url = access_token_url

        return self

    def set_platform_public_key(self, platform_public_key: str) -> Registration:
        """
        Set Platform public key in PEM format
        """
        self._platform_public_key = platform_public_key

        return self

    def set_platform_private_key(self, platform_private_key: str) -> Registration:
        """
        Set Platform private key in PEM format
        """
        self._platform_private_key = platform_private_key

        return self

    def set_deeplink_launch_url(self, deeplink_launch_url: str) -> Registration:
        """
        Set deep linking launch url
        """
        self._deeplink_launch_url = deeplink_launch_url

        return self

    @classmethod
    def get_jwk(cls, public_key: str) -> t.Dict[str, t.Any]:
        """
        Get JWK from public key
        """
        jwk_obj = JWK.from_pem(public_key.encode("utf-8"))
        public_jwk: t.Dict[str, t.Any] = json.loads(jwk_obj.export_public())
        public_jwk["alg"] = "RS256"
        public_jwk["use"] = "sig"

        return public_jwk

    def get_jwks(self) -> t.List[t.Dict[str, t.Any]]:
        """
        Get platform JWKS
        """
        keys = []
        public_key = self.get_platform_public_key()

        if public_key:
            keys.append(Registration.get_jwk(public_key))
        return keys

    def get_kid(self) -> t.Optional[str]:
        key = self.get_platform_private_key()
        if key:
            jwk = Registration.get_jwk(key)
            return jwk.get("kid") if jwk else None
        return None

    def get_tool_key_set_url(self) -> t.Optional[str]:
        return self._tool_keyset_url

    def set_tool_key_set_url(self, key_set_url: str) -> Registration:
        self._tool_keyset_url = key_set_url
        return self

    def get_tool_key_set(self) -> t.Optional[JWKS]:
        return self._tool_keyset

    def set_tool_key_set(self, key_set: JWKS) -> Registration:
        self._tool_keyset = key_set
        return self

    def get_tool_redirect_uris(self) -> t.Optional[t.List[str]]:
        return self._tool_redirect_uris
    
    def set_tool_redirect_uris(self, redirect_uris: t.List[str]) -> Registration:
        self._tool_redirect_uris = redirect_uris
        return self

    @staticmethod
    def encode_and_sign(
        payload: t.Dict[str, t.Any],
        private_key: str,
        headers: t.Optional[t.Any] = None,
        expiration: t.Optional[int] = None,
    ) -> str:
        if expiration:
            payload.update(
                {"iat": int(time.time()), "exp": int(time.time()) + expiration}
            )

        encoded_jwt = jwt_encode(
            payload, private_key, algorithm="RS256", headers=headers
        )

        return encoded_jwt

    @staticmethod
    def decode_and_verify(
        encoded_jwt: str,
        public_key: str,
        audience: t.Optional[str] = None,
    ) -> t.Dict[str, t.Any]:
        decode_kwargs: t.Dict[str, t.Any] = {
            "algorithms": ["RS256"],
            "options": {"verify_aud": bool(audience)},
        }

        if audience:
            decode_kwargs["audience"] = audience

        return jwt.decode(encoded_jwt, public_key, **decode_kwargs)

    def platform_encode_and_sign(
        self, payload: t.Dict[str, t.Any], expiration: t.Optional[int] = None
    ) -> str:
        platform_private_key = self.get_platform_private_key()

        assert platform_private_key is not None, "Platform private key is not set"

        headers = None
        kid = self.get_kid()

        if kid:
            headers = {"kid": kid}

        return Registration.encode_and_sign(
            payload, platform_private_key, headers, expiration=expiration
        )

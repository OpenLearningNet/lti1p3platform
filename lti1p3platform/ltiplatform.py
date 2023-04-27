from __future__ import annotations
from abc import ABC, abstractmethod
import time
import typing as t
import base64
import json
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
    _registration = None
    _accepted_deeplinking_types = LTI_DEEP_LINKING_ACCEPTED_TYPES

    """
    LTI 1.3 Platform Data storage abstract class
    """

    def __init__(self, **kwargs: t.Any) -> None:
        self._jwt: t.Dict[str, t.Any] = {}
        self._jwt_verify_options: t.Dict[str, t.Any] = {"verify_aud": False}

        self.init_platform_config(**kwargs)

    @abstractmethod
    def init_platform_config(self, **kwargs: t.Any) -> t.Any:
        pass

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
        Get JWKS
        """
        assert self._registration is not None, "Registration not yet set"

        return {"keys": self._registration.get_jwks()}

    def fetch_public_key(self, key_set_url: str) -> JWKS:
        """
        Fetch public key from url
        """
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
            if tool_key_set_url.startswith(("http://", "https://")):
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

    def tool_validate_and_decode(self, jwt_token_string: str) -> t.Dict[str, t.Any]:
        self.validate_jwt_format(jwt_token_string)

        public_key = self.get_tool_public_key()

        return jwt.decode(
            jwt_token_string,
            public_key,
            algorithms=["RS256"],
            options=self._jwt_verify_options,
        )

    def get_access_token(
        self, token_request_data: t.Dict[str, t.Any]
    ) -> AccessTokenResponse:
        """
        Validate request and return JWT access token.

        This complies to IMS Security Framework and accepts a JWT
        as a secret for the client credentials grant.
        See this section:
        https://www.imsglobal.org/spec/security/v1p0/#securing_web_services

        Full spec reference:
        https://www.imsglobal.org/spec/security/v1p0/

        Parameters:
            token_request_data: Dict of parameters sent by LTI tool as form_data.

        Returns:
            A dict containing the JSON response containing a JWT and some extra
            parameters required by LTI tools. This token gives access to all
            supported LTI Scopes from this tool.
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

        # Validate JWT token
        self.tool_validate_and_decode(token_request_data["client_assertion"])

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

        deep_link_response = self.tool_validate_and_decode(jwt_token_string)

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

        token_contents = Registration.decode_and_verify(token, public_key)

        if token_contents.get("iss") != self._registration.get_iss():
            raise LtiException("Invalid issuer")

        if "exp" in token_contents and token_contents["exp"] < time.time():
            raise LtiException("Token expired")

        if audience and token_contents.get("aud") != audience:
            raise LtiException("Invalid audience")

        token_scopes = token_contents.get("scopes", "").split(" ")

        if allowed_scopes:
            return any(scope in token_scopes for scope in allowed_scopes)

        return True

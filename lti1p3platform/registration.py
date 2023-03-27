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
    """

    _iss = None
    _launch_url = None
    _client_id = None
    _deployment_id = None
    _oidc_login_url = None
    _tool_keyset_url = None
    _tool_keyset = None
    _platform_public_key = None
    _platform_private_key = None
    _deeplink_launch_url = None

    def get_iss(self) -> t.Optional[str]:
        """
        Get issuer
        """
        return self._iss

    def get_launch_url(self) -> t.Optional[str]:
        """
        Get tool provider launch url
        """
        return self._launch_url

    def get_client_id(self) -> t.Optional[str]:
        """
        Get platform client id
        The client_id is created by the platform and used to identify itself to the tool provider
        """
        return self._client_id

    def get_deployment_id(self) -> t.Optional[str]:
        """
        Get deployment id
        The deployment id is created by the platform and used as an account identifier
        """
        return self._deployment_id

    def get_oidc_login_url(self) -> t.Optional[str]:
        """
        Get OIDC login url
        A url used by the platform to initiate LTI launch
        """
        return self._oidc_login_url

    def get_platform_public_key(self) -> t.Optional[str]:
        """
        Get Platform public key in PEM format
        """
        return self._platform_public_key

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
    def decode_and_verify(encoded_jwt: str, public_key: str) -> t.Dict[str, t.Any]:
        return jwt.decode(encoded_jwt, public_key, algorithms=["RS256"])

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

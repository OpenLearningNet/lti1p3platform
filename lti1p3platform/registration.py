from __future__ import annotations

import typing as t
from jwcrypto.jwk import JWK

import time
import jwt
import json

from .jwt_helper import jwt_encode

class Registration:
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

    def get_iss(self) -> t.Optional(str):
        return self._iss
    
    def get_launch_url(self) -> t.Optional(str):
        return self._launch_url
    
    def get_client_id(self) -> t.Optional(str):
        return self._client_id
    
    def get_deployment_id(self) -> t.Optional(str):
        return self._deployment_id
    
    def get_oidc_login_url(self) -> t.Optional(str):
        return self._oidc_login_url
    
    def get_platform_public_key(self) -> t.Optional(str):
        return self._platform_public_key
    
    def get_platform_private_key(self) -> t.Optional(str):
        return self._platform_private_key
    
    def get_deeplink_launch_url(self) -> t.Optional(str):
        return self._deeplink_launch_url
    
    def set_iss(self, iss) -> Registration:
        self._iss = iss
        
        return self
    
    def set_launch_url(self, launch_url) -> Registration:
        self._launch_url = launch_url
        
        return self
    
    def set_client_id(self, client_id) -> Registration:
        self._client_id = client_id
        
        return self
    
    def set_deployment_id(self, deployment_id) -> Registration:
        self._deployment_id = deployment_id
        
        return self

    def set_oidc_login_url(self, oidc_login_url) -> Registration:
        self._oidc_login_url = oidc_login_url
        
        return self
    
    def set_platform_public_key(self, platform_public_key) -> Registration:
        self._platform_public_key = platform_public_key
        
        return self

    def set_platform_private_key(self, platform_private_key) -> Registration:
        self._platform_private_key = platform_private_key
        
        return self

    def set_deeplink_launch_url(self, deeplink_launch_url) -> Registration:
        self._deeplink_launch_url = deeplink_launch_url
        
        return self

    @classmethod
    def get_jwk(cls, public_key) -> t.Mapping[str, t.Any]:
        jwk_obj = JWK.from_pem(public_key.encode('utf-8'))
        public_jwk = json.loads(jwk_obj.export_public())
        public_jwk['alg'] = 'RS256'
        public_jwk['use'] = 'sig'
        return public_jwk

    def get_jwks(self) -> t.List[t.Mapping[str, t.Any]]:
        keys = []
        public_key = self.get_platform_public_key()
        
        if public_key:
            keys.append(Registration.get_jwk(public_key))
        return keys

    def get_kid(self) -> t.Optional(str):
        key = self.get_platform_private_key()
        if key:
            jwk = Registration.get_jwk(key)
            return jwk.get('kid') if jwk else None
        return None

    def get_tool_key_set_url(self) -> t.Optional(str):
        return self._tool_keyset_url

    def set_tool_key_set_url(self, key_set_url) -> Registration:
        self._tool_keyset_url = key_set_url
        return self
    
    def get_tool_key_set(self) -> t.Optional(t.Mapping(t.List(t.Mapping(str, t.Any)))):
        return self._tool_keyset

    def set_tool_key_set(self, key_set) -> Registration:
        self._tool_keyset = key_set
        return self

    @staticmethod
    def encode_and_sign(payload, private_key, headers=None, expiration=None) -> str:
        if expiration:
            payload.update({
                "iat": int(time.time()),
                "exp": int(time.time()) + expiration
            })
            
        encoded_jwt = jwt_encode(payload, private_key, algorithm='RS256', headers=headers)
        
        return encoded_jwt

    @staticmethod
    def decode_and_verify(encoded_jwt, public_key) -> t.Mapping[str, t.Any]:
        return jwt.decode(encoded_jwt, public_key, algorithms=['RS256'])
    
    def platform_encode_and_sign(self, payload, expiration=None) -> str:
        headers = None
        kid = self.get_kid()
        
        if kid:
            headers = {'kid': kid}

        return Registration.encode_and_sign(payload, self.get_platform_private_key(), headers, expiration=expiration)
    
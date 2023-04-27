from __future__ import annotations

import typing as t

from urllib.parse import urlencode, urlparse, parse_qsl
from abc import ABC, abstractmethod

from . import exceptions

if t.TYPE_CHECKING:
    from .registration import Registration
    from .ltiplatform import LTI1P3PlatformConfAbstract


class OIDCLoginAbstract(ABC):
    _request = None
    _platform_config = None
    _registration = None  # type: Registration
    _launch_url = None
    _lti_message_hint = None

    def __init__(
        self, request: t.Any, platform_config: LTI1P3PlatformConfAbstract
    ) -> None:
        self._request = request
        self._platform_config = platform_config
        self._registration = self._platform_config.get_registration()

    @abstractmethod
    def set_lti_message_hint(self, **kwargs: t.Any) -> None:
        raise NotImplementedError

    def get_lti_message_hint(self) -> t.Optional[str]:
        return getattr(self, "_lti_message_hint", None)

    def set_launch_url(self, launch_url: str) -> OIDCLoginAbstract:
        self._launch_url = launch_url

        return self

    def set_deeplinking_launch_url(self) -> OIDCLoginAbstract:
        launch_url = self._registration.get_deeplink_launch_url()

        if launch_url:
            self.set_launch_url(launch_url)

        return self

    def get_launch_url(self) -> t.Optional[str]:
        if not self._launch_url:
            launch_url = self._registration.get_launch_url()

            assert launch_url, "Launch url is not set"
            self.set_launch_url(launch_url)

        return self._launch_url

    def prepare_preflight_url(self, user_id: str) -> str:
        """
        Prepare OIDC preflight url

        - iss: required, the issuer identifier identifying the learning platform
        - target_link_uri: required, the actual end point that should be
        executed at the end of the OIDC authentication flow
        - lti_message_hint: required, this is an LTI specific parameter identifying
        the actual message to be executed. For example it may be the resource link id
        when the message is a resource link request.
        - login_hint: required, a platform opaque identifier identifying the user to login
        - client_id: optional, specifies the client id for the authorization server that
        should be used to authorize the subsequent LTI message request. This allows for
        a platform to support multiple registrations from a single issuer,
        without relying on the initiate_login_uri as a key
        - lti_deployment_id: optional, if included, MUST contain the same deployment id
        that would be passed in the https://purl.imsglobal.org/spec/lti/claim/deployment_id
        claim for the subsequent LTI message launch
        """
        launch_url = self.get_launch_url()
        try:
            assert self._registration.get_iss()
            assert launch_url
            assert self.get_lti_message_hint()
            assert user_id
        except AssertionError as err:
            raise exceptions.PreflightRequestValidationException from err

        params = {
            "iss": self._registration.get_iss(),
            "target_link_uri": launch_url,
            "login_hint": user_id,
            "lti_message_hint": self.get_lti_message_hint(),
        }

        client_id = self._registration.get_client_id()
        if client_id:
            params["client_id"] = client_id

        deployment_id = self._registration.get_deployment_id()
        if deployment_id:
            params["lti_deployment_id"] = deployment_id

        # Encode the new query parameters
        encoded_params = urlencode(params)

        oidc_login_url = self._registration.get_oidc_login_url()
        parsed_url = urlparse(oidc_login_url)
        query = parsed_url.query

        if isinstance(query, bytes):
            query = query.decode("utf-8")

        query_dict = dict(parse_qsl(query))
        if parsed_url.query and not query_dict:
            # handle some weird cases when query is not empty but parse_qsl returns empty dict
            return f"{oidc_login_url}&{encoded_params}"

        return f"{oidc_login_url}?{encoded_params}"

    @abstractmethod
    def get_redirect(self, url: str) -> t.Any:
        raise NotImplementedError

    def initiate_login(self, user_id: str) -> t.Any:
        """
        Initiate OIDC login
        """
        # prepare preflight url
        preflight_url = self.prepare_preflight_url(user_id)

        # redirect to preflight url
        return self.get_redirect(preflight_url)

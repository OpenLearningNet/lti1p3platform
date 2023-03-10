import typing 

from urllib.parse import urlencode
from abc import ABC, abstractmethod

from .constants import LTI_BASE_MESSAGE
from . import exceptions

if typing.TYPE_CHECKING:
    from .registration import Registration

class OIDCLoginAbstract(ABC):
    _request = None
    _platform_config = None
    _request_link_id = None
    _registration = None  # type: Registration
    
    def __init__(self, request, platform_config) -> None:
        self._request = request
        self._platform_config = platform_config
    
    @abstractmethod
    def set_lti_message_hint(self, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def get_lti_message_hint(self):
        raise NotImplementedError

    def prepare_preflight_url(self, user_id):
        """
        Prepare OIDC preflight url
        
        - iss: required, the issuer identifier identifying the learning platform
        - target_link_uri: required, the actual end point that should be executed at the end of the OIDC authentication flow
        - lti_message_hint: required, this is an LTI specific parameter identifying the actual message to be executed. For example it may be the resource link id when the message is a resource link request.
        - login_hint: required, a platform opaque identifier identifying the user to login
        - client_id: optional, specifies the client id for the authorization server that should be used to authorize the subsequent LTI message request. This allows for a platform to support multiple registrations from a single issuer, without relying on the initiate_login_uri as a key
        - lti_deployment_id: optional, if included, MUST contain the same deployment id that would be passed in the https://purl.imsglobal.org/spec/lti/claim/deployment_id claim for the subsequent LTI message launch
        """
        try:
            assert self._registration.get_iss()
            assert self._registration.get_launch_url()
            assert self.get_lti_message_hint()
            assert user_id
        except AssertionError as err:
            raise exceptions.PreflightRequestValidationException from err

        params = {
            "iss": self._registration.get_iss(),
            "target_link_uri": self._registration.get_launch_url(),
            "login_hint": user_id,
            "lti_message_hint": self.get_lti_message_hint(),
        }
        
        client_id = self._registration.get_client_id()
        if client_id:
            params['client_id'] = client_id
        
        deployment_id = self._registration.get_deployment_id()
        if deployment_id:
            params['lti_deployment_id'] = deployment_id
        
        return f"{self._registration.get_oidc_login_url()}?{urlencode(params)}"

    @abstractmethod
    def get_redirect(self, url):
        raise NotImplementedError

    def initiate_login(self, user_id):
        """
        Initiate OIDC login
        """
        self._registration = self._platform_config.get_registration()
        # prepare preflight url
        preflight_url = self.prepare_preflight_url(user_id)
        
        # redirect to preflight url
        return self.get_redirect(preflight_url)